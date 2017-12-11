import logging

import boto3
import botocore
import concurrent.futures


log = logging.getLogger()


def get_ec2_instances():
    client = boto3.client('ec2')
    next_token = {}
    instances = []
    while True:
        log.debug('calling describe_instances')
        response = client.describe_instances(MaxResults=1000, Filters=[{
            'Name': 'instance-state-name',
            'Values': ['running'],
            }], **next_token)
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


def get_s3_buckets():
    client = boto3.client('s3')
    buckets = []
    log.debug('calling list_buckets')
    response = client.list_buckets()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(client.get_bucket_tagging, Bucket=bucket['Name']): bucket for bucket in response['Buckets']}
        for future in concurrent.futures.as_completed(futures):
            bucket = futures[future]
            bucket['facets'] = {}
            try:
                tags = future.result()
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    continue
                log.error(e)
            else:
                bucket['TagSet'] = tags.get('TagSet', [])
                for tag in bucket['TagSet']:
                    bucket['facets'][tag['Key'].lower()] = tag['Value']
            finally:
                buckets.append(bucket)
    return buckets


def get_rds_instances():
    client = boto3.client('rds')
    dbs = []
    log.debug('calling describe-db-clusters')
    response = client.describe_db_clusters()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(client.list_tags_for_resource, ResourceName=db['DBClusterArn']): db for db in response['DBClusters']}
        for future in concurrent.futures.as_completed(futures):
            db = futures[future]
            db['type'] = 'cluster'
            db['facets'] = {}
            db['facets']['name'] = db['Endpoint']
            try:
                tags = future.result()
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    continue
                log.error(e)
            else:
                db['TagList'] = tags.get('TagList', [])
                for tag in db['TagList']:
                    db['facets'][tag['Key'].lower()] = tag['Value']
            finally:
                dbs.append(db)

    response = client.describe_db_instances()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(client.list_tags_for_resource, ResourceName=db['DBInstanceArn']): db for db in response['DBInstances'] if 'DBClusterIdentifier' not in db}
        for future in concurrent.futures.as_completed(futures):
            db = futures[future]
            db['type'] = 'instance'
            db['facets'] = {}
            db['facets']['name'] = db['Endpoint']['Address']
            try:
                tags = future.result()
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    continue
                log.error(e)
            else:
                db['TagList'] = tags.get('TagList', [])
                for tag in db['TagList']:
                    db['facets'][tag['Key'].lower()] = tag['Value']
            finally:
                dbs.append(db)
    return dbs


def get_cfn_stacks():
    client = boto3.client('cloudformation')
    next_token = {}
    items = []
    while True:
        log.debug('calling describe_stacks')
        response = client.describe_stacks(**next_token)
        for item in response['Stacks']:
            item['facets'] = {}
            item['facets']['name'] = item['StackName']
            if 'Tags' in item:
                for tag in item['Tags']:
                    item['Tag:%s' % tag['Key']] = tag['Value']
                    item['facets'][tag['Key'].lower()] = tag['Value']
            items.append(item)
        if 'NextToken' in response:
            next_token['NextToken'] = response['NextToken']
        else:
            break
    return items


def get_sqs_queues():
    client = boto3.client('sqs')
    queues = []
    response = client.list_queues()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(client.get_queue_attributes, QueueUrl=queue_url, AttributeNames=['All']): queue_url for queue_url in response['QueueUrls']}
        for future in concurrent.futures.as_completed(futures):
            queue_url = futures[future]
            queue = {
                'QueueUrl': queue_url,
            }
            try:
                attributes = future.result()
            except botocore.exceptions.ClientError as e:
                log.error(e)
            else:
                for key, attribute in list(attributes['Attributes'].items()):
                    queue[key] = attribute
                queue['QueueName'] = queue['QueueArn'].split(':')[-1]
            finally:
                queues.append(queue)
    return queues


def get_redshift_clusters():
    client = boto3.client('redshift')
    next_token = {}
    items = []
    while True:
        log.debug('calling describe_clusters')
        response = client.describe_clusters(**next_token)
        for item in response['Clusters']:
            item['facets'] = {}
            item['facets']['name'] = item['DBName']
            if 'Tags' in item:
                for tag in item['Tags']:
                    item['Tag:%s' % tag['Key']] = tag['Value']
                    item['facets'][tag['Key'].lower()] = tag['Value']
            items.append(item)
        if 'Marker' in response:
            next_token['NextToken'] = response['Marker']
        else:
            break
    return items


def get_lambda_functions():
    client = boto3.client('lambda')
    next_token = {}
    items = []
    while True:
        log.debug('calling list_functions')
        response = client.list_functions(**next_token)
        for item in response['Functions']:
            item['facets'] = {}
            item['facets']['name'] = item['FunctionName']
            items.append(item)
        if 'NextMarker' in response:
            next_token['NextToken'] = response['NextMarker']
        else:
            break
    return items


def get_beanstalk_environments():
    client = boto3.client('elasticbeanstalk')
    items = []
    log.debug('calling describe_environments')
    response = client.describe_environments()
    for item in response['Environments']:
        item['facets'] = {}
        item['facets']['name'] = item['EnvironmentName']
        items.append(item)
    return items


def get_cloudwatch_log_groups():
    client = boto3.client('logs')
    next_token = {}
    items = []
    while True:
        log.debug('calling cloudwatch_streams')
        response = client.describe_log_groups(**next_token)
        for item in response['logGroups']:
            item['facets'] = {}
            item['facets']['name'] = item['logGroupName']
            items.append(item)
        if 'nextToken' in response:
            next_token['nextToken'] = response['nextToken']
        else:
            break
    return items
