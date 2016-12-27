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


def test_get_redshift_clusters():
    clusters = get_redshift_clusters()
    assert clusters


def test_get_lambda_functions():
    items = get_lambda_functions()
    assert items


def test_get_beanstalk_environments():
    items = get_beanstalk_environments()
    printer = pprint.PrettyPrinter()
    printer.pprint(items)
    assert not items
