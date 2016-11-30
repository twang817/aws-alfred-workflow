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
                for tag in tags.get('TagSet', []):
                    bucket['facets'][tag['Key'].lower()] = tag['Value']
            finally:
                buckets.append(bucket)
    return buckets

