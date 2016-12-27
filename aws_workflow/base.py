# -*- coding: utf-8 -*-
import json
import logging
import os

from six.moves.urllib.parse import urlencode

import workflow
from workflow.background import run_in_background, is_running

from .utils import json_serializer
from .utils import filter_facets
from .utils import create_stack_status_icons


log = logging.getLogger()


def _get_cached_data(wf, profile, region, name, cmdline=None, max_age=60):
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


class Finder:
    item_identifier = None
    aws_list_function_name = None

    def create_title(self, obj):
        raise NotImplementedError

    def filter_items(self, wf, objects, terms):
        raise NotImplementedError

    def populate_menu_item(self, wf, obj, title, uid, region_name, quicklookurl):
        raise NotImplementedError

    def find(self, wf, profile, region_name, terms, facets, quicklook_baseurl):
        objects = _get_cached_data(
            wf, profile, region_name, self.item_identifier,
            max_age=3600,
            cmdline=[
                '/usr/bin/env',
                'python',
                wf.workflowfile('aws.py'),
                'background',
                self.aws_list_function_name,
            ])

        if not objects:
            return

        if terms:
            objects = self.filter_items(wf, objects, terms)
        objects = filter_facets(wf, objects, facets)

        for obj in objects:
            title = self.create_title(obj)
            uid = '%s-%s-%s' % (profile, self.item_identifier, title)
            if quicklook_baseurl is not None:
                quicklookurl = '%s/%s?%s' % (quicklook_baseurl, self.item_identifier, urlencode({
                    'template': self.item_identifier,
                    'context': json.dumps({
                        'title': title,
                        'uid': uid,
                        self.item_identifier: obj,
                    }, default=json_serializer)
                }))
            else:
                quicklookurl = None

            self.populate_menu_item(wf, obj, title, uid, region_name, quicklookurl)


class Ec2Finder(Finder):
    item_identifier = 'ec2'
    aws_list_function_name = 'get_ec2_instances'

    def create_title(self, instance):
        if 'Tag:Name' in instance:
            return '%s (%s)' % (instance['Tag:Name'], instance['InstanceId'])
        return instance['InstanceId']

    def filter_items(self, wf, instances, terms):
        if len(terms) == 1 and terms[0].startswith('i-'):
            return wf.filter(terms[0], instances, key=lambda i: unicode(i['InstanceId']), match_on=workflow.MATCH_STARTSWITH)
        elif len(terms) > 0:
            return wf.filter(' '.join(terms), instances, key=lambda i: i['facets'].get('name', u''))
        return instances

    state_icons = {
        'pending': '⏲',
        'rebooting': '⏲',
        'running': '🍏',
        'stopping': '💣',
        'stopped': '🔴',
        'terminated': '🔴',
        'shutting-down': '💣',
    }

    def populate_menu_item(self, wf, instance, title, uid, region_name, quicklookurl):
        state = instance['State']['Name']
        valid = state == 'running'
        state_icon = self.state_icons.get(state, '❔')
        private_ip = instance.get('PrivateIpAddress', 'N/A')
        item = wf.add_item(
            title,
            subtitle='copy private ip - %s (status: %s %s)' % (private_ip, state, state_icon),
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


class BucketFinder(Finder):
    item_identifier = 's3'
    aws_list_function_name = 'get_s3_buckets'

    def create_title(self, bucket):
        return bucket['Name']

    def filter_items(self, wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda b: unicode(b['Name']))

    def populate_menu_item(self, wf, bucket, title, uid, region_name, quicklookurl):
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


class DatabaseFinder(Finder):
    item_identifier = 'rds'
    aws_list_function_name = 'get_rds_instances'

    def create_title(self, db):
        return db['facets']['name']

    def filter_items(self, wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda b: unicode(b['facets']['name']))

    def populate_menu_item(self, wf, db, title, uid, region_name, quicklookurl):
        if db['type'] == 'instance':
            db_id = db['DBInstanceIdentifier']
            icon = 'icons/db_instance.png'
            url = 'https://%s.console.aws.amazon.com/rds/home?region=%s#dbinstances:id=%s;sf=all' % (region_name, region_name, db_id)
        else:
            icon = 'icons/db_cluster.png'
            url = 'https://%s.console.aws.amazon.com/rds/home?region=%s#dbclusters:' % (region_name, region_name)

        item = wf.add_item(
            title,
            subtitle='copy endpoint url (%s)' % db['type'],
            arg=title,
            valid=True,
            uid=uid,
            icon=icon,
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'copy-to-clipboard,post-notification')
        item.setvar('notification_title', 'Copied database endpoint')
        item.setvar('notification_text', title)

        cmdmod = item.add_modifier(
            "cmd",
            subtitle='open in AWS console',
            arg=url,
            valid=True,
        )
        cmdmod.setvar('action', 'open-url')


class StackFinder(Finder):
    item_identifier = 'cfn'
    aws_list_function_name = 'get_cfn_stacks'

    stack_status_icons = create_stack_status_icons()

    def create_title(self, stack):
        return stack['StackName']

    def filter_items(self, wf, stacks, terms):
        return wf.filter(' '.join(terms), stacks, key=lambda stack: unicode(stack['StackName']))

    def populate_menu_item(self, wf, stack, title, uid, region_name, quicklookurl):
        url = 'https://%s.console.aws.amazon.com/cloudformation/home?region=%s#/stack/detail?stackId=%s' % (region_name, region_name, stack['StackId'])

        status = stack['StackStatus']
        stack_status_icon = self.stack_status_icons.get(status, '')
        item = wf.add_item(
            title,
            subtitle='open in AWS console (status: %s %s)' % (status, stack_status_icon),
            arg=url,
            valid=True,
            uid=uid,
            icon='icons/cfn_stack.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'open-url')


class QueueFinder(Finder):
    item_identifier = 'sqs'
    aws_list_function_name = 'get_sqs_queues'

    def create_title(self, queue):
        return queue['QueueName']

    def filter_items(self, wf, stacks, terms):
        return wf.filter(' '.join(terms), stacks, key=lambda stack: unicode(stack['QueueUrl']))

    def populate_menu_item(self, wf, queue, title, uid, region_name, quicklookurl):
        queue_url = queue['QueueUrl']
        # aws console doesn't use the actual queue url attribute for its query parameters, so manually construct it
        formatted_queue_url = 'https://sqs.%s.amazonaws.com%s' % (region_name, queue_url.split('amazonaws.com')[-1])
        url = 'https://console.aws.amazon.com/sqs/home?region=%s#queue-browser:selected=%s;prefix=' % (region_name, formatted_queue_url)
        item = wf.add_item(
            title,
            subtitle='open in AWS console (messages available: %s; in-flight: %s)' % (queue['ApproximateNumberOfMessages'], queue['ApproximateNumberOfMessagesNotVisible']),
            arg=url,
            valid=True,
            uid=uid,
            icon='icons/sqs_queue.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'open-url')

        cmdmod = item.add_modifier(
            "cmd",
            subtitle='copy queue url',
            arg=queue_url,
            valid=True,
        )
        cmdmod.setvar('action', 'copy-to-clipboard,post-notification')
        cmdmod.setvar('notification_title', 'Copied queue URL')
        cmdmod.setvar('notification_text', queue_url)


class RedshiftClusterFinder(Finder):
    item_identifier = 'redshift'
    aws_list_function_name = 'get_redshift_clusters'

    def create_title(self, item):
        return item['ClusterIdentifier']

    def filter_items(self, wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda item: unicode(item['ClusterIdentifier']))

    def populate_menu_item(self, wf, cluster, title, uid, region_name, quicklookurl):
        url = 'https://%s.console.aws.amazon.com/redshift/home?region=%s#cluster-details:cluster=%s' % (region_name, region_name, title)
        del cluster['ClusterCreateTime'] # TODO
        item = wf.add_item(
            title,
            subtitle='open in AWS console (status: %s)' % cluster['ClusterStatus'],
            arg=url,
            valid=True,
            uid=uid,
            icon='icons/services/redshift.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'open-url')

        first_node = next(iter(cluster['ClusterNodes']), None)

        private_ip = first_node.get('PrivateIPAddress', 'N/A')
        cmdmod = item.add_modifier(
            'cmd',
            subtitle='copy first node\'s private IP - %s' % private_ip,
            arg=private_ip,
            valid=first_node and 'PrivateIPAddress' in first_node,
        )
        cmdmod.setvar('action', 'copy-to-clipboard,post-notification')
        cmdmod.setvar('notification_title', 'Copied Private IP of Redshift Node')
        cmdmod.setvar('notification_text', '%s of %s' % (private_ip, title))

        public_ip = first_node.get('PublicIPAddress', 'N/A')
        altmod = item.add_modifier(
            'alt',
            subtitle='copy first node\'s public IP - %s' % public_ip,
            arg=public_ip,
            valid=first_node and 'PublicIPAddress' in first_node,
        )
        altmod.setvar('action', 'copy-to-clipboard,post-notification')
        altmod.setvar('notification_title', 'Copied Public IP of Redshift Node')
        altmod.setvar('notification_text', '%s of %s' % (public_ip, title))


class FunctionFinder(Finder):
    item_identifier = 'lambda'
    aws_list_function_name = 'get_lambda_functions'

    def create_title(self, item):
        return item['FunctionName']

    def filter_items(self, wf, items, terms):
        return wf.filter(' '.join(terms), items, key=lambda item: unicode(item['FunctionName']))

    def populate_menu_item(self, wf, function, title, uid, region_name, quicklookurl):
        url = 'https://%s.console.aws.amazon.com/lambda/home?region=%s#/functions/%s?tab=code' % (region_name, region_name, title)
        item = wf.add_item(
            title,
            subtitle='open in AWS console (runtime: %s)' % function.get('Runtime', 'N/A'),
            arg=url,
            valid=True,
            uid=uid,
            icon='icons/services/lambda.png',
            type='default',
            quicklookurl=quicklookurl
        )
        item.setvar('action', 'open-url')
