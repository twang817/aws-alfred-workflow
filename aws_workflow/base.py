# -*- coding: utf-8 -*-
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


def helper(item_identifier, aws_list_function_name):
    def decorator(func):
        def wrapper(wf, profile, region_name, terms, facets, quicklook_baseurl):
            functions = func()

            objects = get_cached_data(
                wf, profile, region_name, item_identifier,
                max_age=3600,
        cmdline=[
            '/usr/bin/env',
            'python',
            wf.workflowfile('aws.py'),
            'background',
                    aws_list_function_name,
        ])

            if not objects:
        return

            if terms:
                objects = functions['filter_items'](wf, objects, terms)
            objects = filter_facets(wf, objects, facets)

            for object in objects:
                title = functions['create_title'](object)
                uid = '%s-%s-%s' % (profile, item_identifier, title)
        if quicklook_baseurl is not None:
                    quicklookurl = '%s/%s?%s' % (quicklook_baseurl, item_identifier, urlencode({
                        'template': item_identifier,
                'context': json.dumps({
                    'title': title,
                    'uid': uid,
                            item_identifier: object,
                }, default=json_serializer)
            }))
        else:
            quicklookurl = None

                functions['populate_menu_item'](wf, object, title, uid, region_name, quicklookurl)
        return wrapper
    return decorator


@helper(item_identifier='ec2', aws_list_function_name='get_ec2_instances')
def find_ec2():
    def create_title(instance):
        if 'Tag:Name' in instance:
            return '%s (%s)' % (instance['Tag:Name'], instance['InstanceId'])
        return instance['InstanceId']

    def filter_items(wf, instances, terms):
        if len(terms) == 1 and terms[0].startswith('i-'):
            return wf.filter(terms[0], instances, key=lambda i: unicode(i['InstanceId']), match_on=workflow.MATCH_STARTSWITH)
        elif len(terms) > 0:
            return wf.filter(' '.join(terms), instances, key=lambda i: i['facets'].get('name', u''))
        return instances

    def populate_menu_item(wf, instance, title, uid, region_name, quicklookurl):
        valid = instance['State']['Name'] == 'running'
        private_ip = instance.get('PrivateIpAddress', 'N/A')
        item = wf.add_item(
            title,
            subtitle='copy private ip - ' + private_ip,
            arg=private_ip,
            valid=valid and 'PrivateIpAddress' in instance,
            uid=uid,
            icon='icons/ec2_instance.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'copy-to-clipboard,post-notification')
        item.setvar('notification_title', 'Copied Private IP of EC2 Instance')
        item.setvar('notification_text', '%s of %s' % (private_ip, title))
        public_ip = instance.get('PublicIpAddress', 'N/A')
        altmod = item.add_modifier(
            "alt",
            subtitle='copy public ip - ' + public_ip,
            arg=public_ip,
            valid=valid and 'PublicIpAddress' in instance,
        )
        altmod.setvar('action', 'copy-to-clipboard,post-notification')
        altmod.setvar('notification_title', 'Copied Public IP of EC2 Instance')
        altmod.setvar('notification_text', '%s of %s' % (public_ip, title))
        cmdmod = item.add_modifier(
            "cmd",
            subtitle='open in console',
            arg='https://%s.console.aws.amazon.com/ec2/v2/home?region=%s#Instances:search=%s;sort=instanceState' % (region_name, region_name, instance['InstanceId']),
            valid=True,
        )
        cmdmod.setvar('action', 'open-url')

    return {
        'create_title': create_title,
        'filter_items': filter_items,
        'populate_menu_item': populate_menu_item
    }


@helper(item_identifier='s3', aws_list_function_name='get_s3_buckets')
def find_s3_bucket():
    def create_title(bucket):
        return bucket['Name']

    def filter_items(wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda b: unicode(b['Name']))

    def populate_menu_item(wf, bucket, title, uid, region_name, quicklookurl):
        item = wf.add_item(
            title,
            subtitle='open in AWS console',
            arg='https://console.aws.amazon.com/s3/home?region=%s&bucket=%s&prefix=' % (region_name, bucket['Name']),
            valid=True,
            uid=uid,
            icon='icons/s3_bucket.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'open-url')

    return {
        'create_title': create_title,
        'filter_items': filter_items,
        'populate_menu_item': populate_menu_item
    }


@helper(item_identifier='rds', aws_list_function_name='get_rds_instances')
def find_database():
    def create_title(db):
        return db['facets']['name']

    def filter_items(wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda b: unicode(b['facets']['name']))

    def populate_menu_item(wf, db, title, uid, region_name, quicklookurl):
        item = wf.add_item(
            title,
            subtitle='copy endpoint url',
            arg=title,
            valid=True,
            uid=uid,
            icon='icons/db_instance.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'copy-to-clipboard,post-notification')
        item.setvar('notification_title', 'Copied database endpoint')
        item.setvar('notification_text', title)

    return {
        'create_title': create_title,
        'filter_items': filter_items,
        'populate_menu_item': populate_menu_item
    }
