import json
import logging
import os

from six.moves.urllib.parse import urlencode

import workflow
from workflow.background import run_in_background, is_running

from .utils import json_serializer
from .utils import filter_facets


log = logging.getLogger()


def get_cached_data(wf, profile, region, name, cmdline=None, max_age=60):
    data_name = '%s-%s-%s' % (profile, region, name)
    data = wf.cached_data(data_name, max_age=0)

    # if the cache was out of date (or missing as cached_data_fresh returns 0 if
    # not found)
    if not wf.cached_data_fresh(data_name, max_age=max_age):
        wf.rerun = 1
        if not is_running(data_name):
            if cmdline is None:
                raise Exception('could not generate cached data in background.  missing cmdline argument')
            env = os.environ.copy()
            env['AWS_PROFILE'] = profile
            env['AWS_DEFAULT_REGION'] = region
            env['WF_CACHE_DATA_NAME'] = data_name
            run_in_background(data_name, cmdline, env=env)

    return data


def find_ec2(wf, profile, region_name, terms, facets, quicklook_baseurl):
    instances = get_cached_data(
        wf, profile, region_name, 'ec2',
        max_age=600,
        cmdline=[
            '/usr/bin/env',
            'python',
            wf.workflowfile('aws.py'),
            'background',
            'get_ec2_instances',
        ])

    if not instances:
        return

    if len(terms) == 1 and terms[0].startswith('i-'):
        instances = wf.filter(terms[0], instances, key=lambda i: unicode(i['InstanceId']), match_on=workflow.MATCH_STARTSWITH)
    elif len(terms) > 0:
        instances = wf.filter(' '.join(terms), instances, key=lambda i: i['facets'].get('name', u''))
    instances = filter_facets(wf, instances, facets)

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
            icon='icons/ec2_instance.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'copytoclipboard,postnotification')
        item.setvar('notification_text', 'Copied private IP (%s) of %s.' % (instance.get('PrivateIpAddress', 'N/A'), title))
        altmod = item.add_modifier(
            "alt",
            subtitle='public ip',
            arg=instance.get('PublicIpAddress', 'N/A'),
            valid=valid and 'PublicIpAddress' in instance,
        )
        altmod.setvar('action', 'copytoclipboard,postnotification')
        altmod.setvar('notification_text', 'Copied public IP (%s) of %s.' % (instance.get('PublicIpAddress', 'N/A'), title))
        cmdmod = item.add_modifier(
            "cmd",
            subtitle='open in console',
            arg='https://us-west-2.console.aws.amazon.com/ec2/v2/home?region=%s#Instances:search=%s;sort=instanceState' % (region_name, instance['InstanceId']),
            valid=True,
        )
        cmdmod.setvar('action', 'openurl')


def find_s3_bucket(wf, profile, region_name, terms, facets, quicklook_baseurl):
    buckets = get_cached_data(
        wf, profile, region_name, 's3',
        max_age=3600,
        cmdline=[
            '/usr/bin/env',
            'python',
            wf.workflowfile('aws.py'),
            'background',
            'get_s3_buckets',
        ])

    if not buckets:
        return

    if terms:
        buckets = wf.filter(' '.join(terms), buckets, key=lambda b: unicode(b['Name']))
    buckets = filter_facets(wf, buckets, facets)

    for bucket in buckets:
        title = bucket['Name']
        uid = '%s-bucket-%s' % (profile, title)
        if quicklook_baseurl is not None:
            quicklookurl = '%s/s3?%s' % (quicklook_baseurl, urlencode({
                'template': 's3',
                'context': json.dumps({
                    'title': title,
                    'uid': uid,
                    'bucket': bucket,
                }, default=json_serializer)
            }))
        else:
            quicklookurl = None

        item = wf.add_item(
            title,
            subtitle='open in AWS console',
            arg='https://console.aws.amazon.com/s3/home?region=%s&bucket=%s&prefix=' % (region_name, bucket['Name']),
            valid=True,
            uid=uid,
            icon='icons/s3_bucket.png',
            type='default',
        )
