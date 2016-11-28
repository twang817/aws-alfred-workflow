import logging
import json

from six.moves.urllib.parse import urlencode

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

from .aws import get_ec2_instances
from .aws import get_s3_buckets
from .utils import json_serializer
from .utils import filter_facets


log = logging.getLogger('workflow')


def find_ec2(wf, profile, region_name, terms, facets, quicklook_baseurl):
    instances = wf.cached_data('%s-ec2' % profile, get_ec2_instances, max_age=600)

    if len(terms) == 1 and terms[0].startswith('i-'):
        instances = wf.filter(terms[0], instances, key=lambda i: unicode(i['InstanceId']), match_on=MATCH_STARTSWITH)
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
            icon='icons/ec2.eps',
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
    buckets = wf.cached_data('%s-s3' % profile, get_s3_buckets, max_age=600)

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
            icon='icons/s3_bucket.eps',
            type='default',
        )
