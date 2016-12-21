from .aws import *
import pprint


def test_get_ec2_instances():
    instances = get_ec2_instances()
    assert instances


def test_get_s3_buckets():
    buckets = get_s3_buckets()
    assert buckets


def test_get_rds_instances():
    instances = get_rds_instances()
    assert instances


def test_get_cfn_stacks():
    stacks = get_cfn_stacks()
    assert stacks


def test_get_sqs_queues():
    queues = get_sqs_queues()

    for queue in queues:
        assert 'QueueName' in queue
        assert 'QueueUrl' in queue

    assert queues
