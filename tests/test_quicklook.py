import json
import os

import mock
import pytest
from six.moves.urllib.parse import urlencode
import tornado.web


@pytest.mark.gen_test
def test_static(http_client, base_url, root_dir):
    response = yield http_client.fetch('%s/static/css/main.css' % base_url)
    with open(os.path.join(root_dir, 'static', 'css', 'main.css'), 'r') as f:
        css = f.read()
    assert response.code == 200
    assert css == response.body


@pytest.mark.gen_test
def test_ec2_instance(http_client, base_url):
    qs = urlencode({
        'context': json.dumps({
            'title': 'title',
            'uid': 'uid',
            'instance': {
                'State': {
                    'Name': 'state name',
                },
                'InstanceType': 'instance type',
                'LaunchTime': 'launch time',
                'VpcId': 'vpc id',
                'SubnetId': 'subnet id',
                'Placement': {
                    'AvailabilityZone': 'availability zone',
                },
                'PrivateIpAddress': 'private ip',
                'PrivateDnsName': 'private dns',
                'PublicIpAddress': 'public ip',
                'PublicDnsName': 'public dns',
                'Tags': [
                    {'Key': 'tag a', 'Value': 'value a'},
                    {'Key': 'tag b', 'Value': 'value b'},
                    {'Key': 'tag c', 'Value': 'value c'},
                ],
            },
        }),
    })
    response = yield http_client.fetch('%s/quicklook/ec2_instance?%s' % (base_url, qs))
    assert response.code == 200


@pytest.mark.gen_test
def test_s3_bucket(http_client, base_url):
    qs = urlencode({
        'context': json.dumps({
            'title': 'title',
            'uid': 'uid',
            'bucket': {
                'CreationDate': 'creation date',
                'TagsSet': [
                    {'Key': 'tag a', 'Value': 'value a'},
                    {'Key': 'tag b', 'Value': 'value b'},
                    {'Key': 'tag c', 'Value': 'value c'},
                ],
            },
        }),
    })
    response = yield http_client.fetch('%s/quicklook/s3_bucket?%s' % (base_url, qs))
    assert response.code == 200


@pytest.mark.gen_test
def test_rds_instance(http_client, base_url):
    qs = urlencode({
        'context': json.dumps({
            'title': 'title',
            'uid': 'uid',
            'db': {
                'Engine': 'engine',
                'EngineVersion': 'engine version',
                'Tags': [
                    {'Key': 'tag a', 'Value': 'value a'},
                    {'Key': 'tag b', 'Value': 'value b'},
                    {'Key': 'tag c', 'Value': 'value c'},
                ],
            },
        }),
    })
    response = yield http_client.fetch('%s/quicklook/rds_instance?%s' % (base_url, qs))
    assert response.code == 200


@pytest.mark.gen_test
def test_rds_cluster(http_client, base_url):
    qs = urlencode({
        'context': json.dumps({
            'title': 'title',
            'uid': 'uid',
            'db': {
                'Engine': 'engine',
                'EngineVersion': 'engine version',
                'Tags': [
                    {'Key': 'tag a', 'Value': 'value a'},
                    {'Key': 'tag b', 'Value': 'value b'},
                    {'Key': 'tag c', 'Value': 'value c'},
                ],
            },
        }),
    })
    response = yield http_client.fetch('%s/quicklook/rds_cluster?%s' % (base_url, qs))
    assert response.code == 200
