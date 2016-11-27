import datetime
import json
import os
import re
import sys

from six.moves import configparser
from six.moves.urllib.parse import urlencode

import boto3
import click
from workflow import Workflow3
from workflow import (
    MATCH_ALL,
    MATCH_ALLCHARS,
    MATCH_ATOM,
    MATCH_CAPITALS,
    MATCH_INITIALS,
    MATCH_INITIALS_CONTAIN,
    MATCH_INITIALS_STARTSWITH,
    MATCH_STARTSWITH,
    MATCH_SUBSTRING,
)
from workflow.background import run_in_background, is_running

pass_wf = click.make_pass_decorator(Workflow3)
log = None


def json_serializer(obj):
    if isinstance(obj, datetime.datetime):
        s = obj.isoformat()
        return s
    raise TypeError('Type not serializable')


def get_ec2_instances():
    client = boto3.client('ec2')
    next_token = {}
    instances = []
    while True:
        log.debug('calling describe_instances')
        response = client.describe_instances(MaxResults=1000, **next_token)
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance['facets'] = {}
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        instance['Tag:%s' % tag['Key']] = tag['Value']
                        instance['facets'][tag['Key'].lower()] = tag['Value']
                instances.append(instance)
        if 'NextToken' in response:
            next_token['NextToken'] = response['NextToken']
        else:
            break
    return instances


def dedupe(lofd, key):
    seen = set()
    res = []
    for d in lofd:
        if d[key] not in seen:
            seen.add(d[key])
            res.append(d)
    return res


def find_ec2(wf, profile, query, quicklook_baseurl):
    instances = wf.cached_data('%s-ec2' % profile, get_ec2_instances, max_age=600)

    facets = {}
    terms = []
    if query:
        atoms = re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', query)
        for atom in atoms:
            if ':' in atom:
                k, v = re.split(''':(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''', atom)
                facets[k] = v.strip("'\"")
            else:
                terms.append(atom)
    log.debug('terms: %s', terms)
    log.debug('facets: %s', facets)

    if len(terms) == 1:
        term = terms[0]
        if term.startswith('i-'):
            instances = wf.filter(term, instances, key=lambda i: unicode(i['InstanceId']), match_on=MATCH_STARTSWITH)
        else:
            instances = wf.filter(term, instances, key=lambda i: i['facets'].get('name', u''))
    elif len(terms) > 1:
        term = ' '.join(terms)
        instances = wf.filter(term, instances, key=lambda i: i['facets'].get('name', u''))

    for k, v in facets.items():
        if v:
            instances = wf.filter(v, instances, key=lambda i: i['facets'].get(k.lower(), u''))

    for instance in instances:
        if 'Tag:Name' in instance:
            title = '%s (%s)' % (instance['Tag:Name'], instance['InstanceId'])
        else:
            title = instance['InstanceId']
        uid = '%s-ec2-%s' % (profile, instance['InstanceId'])
        valid = instance['State']['Name'] == 'running'
        if quicklook_baseurl is not None:
            quicklookurl = '%s/ec2?%s' % (quicklook_baseurl, urlencode({
                'template': 'ec2',
                'context': json.dumps({
                    'title': title,
                    'uid': uid,
                    'instance': instance,
                }, default=json_serializer)
            }))
        else:
            quicklookurl = None

        item = wf.add_item(
            title,
            subtitle='private ip',
            arg=instance.get('PrivateIpAddress', 'N/A'),
            valid=valid and 'PrivateIpAddress' in instance,
            uid=uid,
            icon='icons/ec2.eps',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('title', title)
        item.add_modifier(
            "alt",
            subtitle='public ip',
            arg=instance.get('PublicIpAddress', 'N/A'),
            valid=valid and 'PublicIpAddress' in instance,
        )
        item.add_modifier(
            "cmd",
            subtitle='open in console',
            arg='https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=us-west-2#Instances:search=%s;sort=instanceState' % instance['InstanceId'],
            valid=True,
        )


@click.group()
@pass_wf
def cli(wf):
    pass

@cli.command()
@pass_wf
def list_profiles(wf):
    parser = configparser.ConfigParser()
    parser.read(os.path.expanduser('~/.aws/credentials'))
    for profile in parser.sections():
        wf.add_item(
            title=profile,
            valid=True,
            arg=profile,
        )
    wf.send_feedback()

@cli.command()
@click.argument('profile')
@pass_wf
def set_profile(wf, profile):
    wf.settings['profile'] = profile

@cli.command()
@pass_wf
def clear_cache(wf):
    def _filter(n):
        return not n.endswith('.pid')
    wf.clear_cache(_filter)

@cli.command()
@click.option('--quicklook_port', envvar='WF_QUICKLOOK_PORT')
@click.argument('query')
@pass_wf
def search(wf, quicklook_port, query):
    profile = wf.settings['profile']
    if profile is None:
        raise Exception('no profile selected')

    os.environ['AWS_PROFILE'] = profile

    quicklook_baseurl = None
    if quicklook_port is not None:
        if not is_running('quicklook'):
            log.info('\n'.join('%s = %s' % (k, v) for k, v in os.environ.items()))
            log.info('launching quicklook server on port %s' % quicklook_port)
            run_in_background('quicklook', ['/usr/bin/env',
                                            'python',
                                            wf.workflowfile('quicklook_server.py'),
                                            quicklook_port])
        else:
            log.info('quicklook server should be on port %s' % quicklook_port)
        quicklook_baseurl = 'http://localhost:%s/quicklook' % quicklook_port

    find_ec2(wf, profile, query, quicklook_baseurl)

    wf.send_feedback()

if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    wf.run(lambda wf: cli(obj=wf))
