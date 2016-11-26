import os
import sys

from six.moves import configparser

import boto3
import click
from jinja2 import Environment, FileSystemLoader
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

pass_wf = click.make_pass_decorator(Workflow3)
log = None


def get_ec2_instances():
    client = boto3.client('ec2')
    next_token = {}
    instances = []
    while True:
        log.debug('calling describe_instances')
        response = client.describe_instances(MaxResults=1000, **next_token)
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                if 'Tags' in instance:
                    for tag in instance['Tags']:
                        instance['Tag:%s' % tag['Key']] = tag['Value']
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


def find_ec2(wf, profile, quicklook, query):
    instances = wf.cached_data('%s-ec2' % profile, get_ec2_instances, max_age=600)

    if query:
        matched = wf.filter(query, instances, key=lambda i: unicode(i['InstanceId']), match_on=MATCH_STARTSWITH)
        matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Name', u''))
        # TODO: parse query for facet:query to perform faceted search
        # matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Application', u''))
        # matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Role', u''))
        # matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Vertical', u''))
        # matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Vpc', u''))
        # matched += wf.filter(query, instances, key=lambda i: i.get('Tag:Environment', u''))
    else:
        matched = instances

    matched = dedupe(matched, 'InstanceId')

    for instance in matched:
        if 'Tag:Name' in instance:
            title = '%s (%s)' % (instance['Tag:Name'], instance['InstanceId'])
        else:
            title = instance['InstanceId']
        uid = '%s-ec2-%s' % (profile, instance['InstanceId'])
        valid = instance['State']['Name'] == 'running'
        quicklookurl = None
        # quicklookurl = quicklook(uid, 'ec2', {
        #     'title': title,
        #     'uid': uid,
        #     'instance': instance,
        # })

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
            "shift",
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
@click.argument('query')
@pass_wf
def search(wf, query):
    profile = wf.settings['profile']
    if profile is None:
        raise Exception('no profile selected')

    os.environ['AWS_PROFILE'] = profile

    def _quicklook_closure():
        env = Environment(loader=FileSystemLoader(os.path.join(wf.workflowdir, 'quicklook')))
        def build_quicklook(uid, template, context):
            filename = wf.cachefile('%s.html' % uid)
            template = env.get_template('%s.html.j2' % template)
            with open(filename, 'w') as f:
                f.write(template.render(**context))
            return filename
        return build_quicklook
    quicklook = _quicklook_closure()

    find_ec2(wf, profile, quicklook, query)

    wf.send_feedback()

if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    wf.run(lambda wf: cli(obj=wf, auto_envvar_prefix='WF'))
