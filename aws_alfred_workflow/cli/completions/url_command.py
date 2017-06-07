from collections import namedtuple
import logging

import click

from ..base import (
    ensure_region,
    pass_complete,
    pass_wf,
    sf_commands,
)
from ...utils import (
    set_version,
)


log = logging.getLogger()


@sf_commands.command('+')
@click.argument('query', required=False)
@pass_wf
@pass_complete
@ensure_region
def aws_console(query, wf, complete, region):
    '''opens browser to AWS console'''
    ConsoleItem = namedtuple('ConsoleItem', 'key name url icon')
    items = [
        ConsoleItem('ec2', 'Virtual Servers in the Cloud', 'https://{region}.console.aws.amazon.com/ec2/v2/home?region={region}'.format(region=region), 'icons/services/ec2.png'),
        ConsoleItem('ecs', 'Run and Manage Docker Containers', 'https://{region}.console.aws.amazon.com/ecs/home?region={region}'.format(region=region), 'icons/services/ecs.png'),
        ConsoleItem('elasticbeanstalk', 'Run and Manage Web Apps', 'https://{region}.console.aws.amazon.com/elasticbeanstalk/home?region={region}'.format(region=region), 'icons/services/elasticbeanstalk.png'),
        ConsoleItem('lambda', 'Run Code without Thinking about Servers', 'https://{region}.console.aws.amazon.com/lambda/home?region={region}'.format(region=region), 'icons/services/lambda.png'),
        ConsoleItem('servermigration', 'Migrate on-premises servers to AWS', 'https://console.aws.amazon.com/servermigration/home?region={region}'.format(region=region), 'icons/services/servermigration.png'),
        ConsoleItem('s3', 'Scalable Storage in the Cloud', 'https://console.aws.amazon.com/s3/home?region={region}'.format(region=region), 'icons/services/s3.png'),
        ConsoleItem('cloudfront', 'Global Content Delivery Network', 'https://console.aws.amazon.com/cloudfront/home?region={region}'.format(region=region), 'icons/services/cloudfront.png'),
        ConsoleItem('efs', 'Fully Managed File System for EC2', 'https://{region}.console.aws.amazon.com/efs/home?region={region}'.format(region=region), 'icons/services/efs.png'),
        ConsoleItem('glacier', 'Archive Storage in the Cloud', 'https://{region}.console.aws.amazon.com/glacier/home?region={region}'.format(region=region), 'icons/services/glacier.png'),
        ConsoleItem('snowball', 'Large Scale Data Transport', 'https://console.aws.amazon.com/importexport/home?region={region}'.format(region=region), 'icons/services/snowball.png'),
        ConsoleItem('storagegateway', 'Hybrid Storage Integration', 'https://{region}.console.aws.amazon.com/storagegateway/home?region={region}'.format(region=region), 'icons/services/storagegateway.png'),
        ConsoleItem('rds', 'Managed Relational Database Service', 'https://{region}.console.aws.amazon.com/rds/home?region={region}'.format(region=region), 'icons/services/rds.png'),
        ConsoleItem('dynamodb', 'Managed NoSQL Database', 'https://{region}.console.aws.amazon.com/dynamodb/home?region={region}'.format(region=region), 'icons/services/dynamodb.png'),
        ConsoleItem('elasticache', 'In-Memory Cache', 'https://{region}.console.aws.amazon.com/elasticache/home?region={region}'.format(region=region), 'icons/services/elasticache.png'),
        ConsoleItem('redshift', 'Fast, Simple, Cost-Effective Data Warehousing', 'https://{region}.console.aws.amazon.com/redshift/home?region={region}'.format(region=region), 'icons/services/redshift.png'),
        ConsoleItem('dms', 'Managed Database Migration Service', 'https://{region}.console.aws.amazon.com/dms/home?region={region}'.format(region=region), 'icons/services/dms.png'),
        ConsoleItem('vpc', 'Isolated Cloud Resources', 'https://{region}.console.aws.amazon.com/vpc/home?region={region}'.format(region=region), 'icons/services/vpc.png'),
        ConsoleItem('directconnect', 'Dedicated Network Connection to AWS', 'https://{region}.console.aws.amazon.com/directconnect/home?region={region}'.format(region=region), 'icons/services/directconnect.png'),
        ConsoleItem('route53', 'Scalable DNS and Domain Name Registration', 'https://console.aws.amazon.com/route53/home?region={region}'.format(region=region), 'icons/services/route53.png'),
        ConsoleItem('codecommit', 'tore Code in Private Git Repositories', 'https://{region}.console.aws.amazon.com/codecommit/home?region={region}'.format(region=region), 'icons/services/codecommit.png'),
        ConsoleItem('codedeploy', 'Automate Code Deployments', 'https://{region}.console.aws.amazon.com/codedeploy/home?region={region}'.format(region=region), 'icons/services/codedeploy.png'),
        ConsoleItem('codepipeline', 'Release Software using Continuous Delivery', 'https://{region}.console.aws.amazon.com/codepipeline/home?region={region}'.format(region=region), 'icons/services/codepipeline.png'),
        ConsoleItem('cloudwatch', 'Monitor Resources and Applications', 'https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}'.format(region=region), 'icons/services/cloudwatch.png'),
        ConsoleItem('cloudformation', 'Create and Manage Resources with Templates', 'https://{region}.console.aws.amazon.com/cloudformation/home?region={region}'.format(region=region), 'icons/services/cloudformation.png'),
        ConsoleItem('cloudtrail', 'Track User Activity and API Usage', 'https://{region}.console.aws.amazon.com/cloudtrail/home?region={region}'.format(region=region), 'icons/services/cloudtrail.png'),
        ConsoleItem('config', 'Track Resource Inventory and Changes', 'https://{region}.console.aws.amazon.com/config/home?region={region}'.format(region=region), 'icons/services/config.png'),
        ConsoleItem('opsworks', 'Automate Operations with Chef', 'https://console.aws.amazon.com/opsworks/landing/home?region={region}'.format(region=region), 'icons/services/opsworks.png'),
        ConsoleItem('catalog', 'Create and Use Standardized Products', 'https://{region}.console.aws.amazon.com/catalog/home?region={region}'.format(region=region), 'icons/services/catalog.png'),
        ConsoleItem('trustedadvisor', 'Optimize Performance and Security', 'https://console.aws.amazon.com/trustedadvisor/home?region={region}'.format(region=region), 'icons/services/trustedadvisor.png'),
        ConsoleItem('iam', 'Manage User Access and Encryption Keys', 'https://console.aws.amazon.com/iam/home?region={region}'.format(region=region), 'icons/services/iam.png'),
        ConsoleItem('directoryservice', 'Host and Manage Active Directory', 'https://{region}.console.aws.amazon.com/directoryservice/home?region={region}'.format(region=region), 'icons/services/directoryservice.png'),
        ConsoleItem('inspector', 'Analyze Application Security', 'https://{region}.console.aws.amazon.com/inspector/home?region={region}'.format(region=region), 'icons/services/inspector.png'),
        ConsoleItem('waf', 'Filter Malicious Web Traffic', 'https://console.aws.amazon.com/waf/home?region={region}'.format(region=region), 'icons/services/waf.png'),
        ConsoleItem('acm', 'Provision, Manage, and Deploy SSL/TLS Certificates', 'https://{region}.console.aws.amazon.com/acm/home?region={region}'.format(region=region), 'icons/services/acm.png'),
        ConsoleItem('elasticmapreduce', 'Managed Hadoop Framework', 'https://{region}.console.aws.amazon.com/elasticmapreduce/home?region={region}'.format(region=region), 'icons/services/elasticmapreduce.png'),
        ConsoleItem('datapipeline', 'Orchestration for Data-Driven Workflows', 'https://console.aws.amazon.com/datapipeline/home?region={region}'.format(region=region), 'icons/services/datapipeline.png'),
        ConsoleItem('es', 'Run and Scale Elasticsearch Clusters', 'https://{region}.console.aws.amazon.com/es/home?region={region}'.format(region=region), 'icons/services/es.png'),
        ConsoleItem('kinesis', 'Work with Real-Time Streaming Data', 'https://{region}.console.aws.amazon.com/kinesis/home?region={region}'.format(region=region), 'icons/services/kinesis.png'),
        ConsoleItem('machinelearning', 'Build Smart Applications Quickly and Easily', 'https://console.aws.amazon.com/machinelearning/home?region={region}'.format(region=region), 'icons/services/machinelearning.png'),
        ConsoleItem('quicksight', 'Fast, easy to use business analytics', 'https://quicksight.aws.amazon.com'.format(region=region), 'icons/services/quicksight.png'),
        ConsoleItem('iot', 'Connect Devices to the Cloud', 'https://{region}.console.aws.amazon.com/iot/home?region={region}'.format(region=region), 'icons/services/iot.png'),
        ConsoleItem('gamelift', 'Deploy and Scale Session-based Multiplayer Games', 'https://{region}.console.aws.amazon.com/gamelift/home?region={region}'.format(region=region), 'icons/services/gamelift.png'),
        ConsoleItem('mobilehub', 'Build, Test, and Monitor Mobile Apps', 'https://console.aws.amazon.com/mobilehub/home?region={region}'.format(region=region), 'icons/services/mobilehub.png'),
        ConsoleItem('cognito', 'User Identity and App Data Synchronization', 'https://{region}.console.aws.amazon.com/cognito/home?region={region}'.format(region=region), 'icons/services/cognito.png'),
        ConsoleItem('devicefarm', 'Test Android, iOS, and Web Apps on Real Devices in the Cloud', 'https://console.aws.amazon.com/devicefarm/home?region={region}'.format(region=region), 'icons/services/devicefarm.png'),
        ConsoleItem('mobileanalytics', 'Collect, View and Export App Analytics', 'https://console.aws.amazon.com/mobileanalytics/home?region={region}'.format(region=region), 'icons/services/mobileanalytics.png'),
        ConsoleItem('sns', 'Push Notification Service', 'https://{region}.console.aws.amazon.com/sns/home?region={region}'.format(region=region), 'icons/services/sns.png'),
        ConsoleItem('apigateway', 'Build, Deploy and Manage APIs', 'https://{region}.console.aws.amazon.com/apigateway/home?region={region}'.format(region=region), 'icons/services/apigateway.png'),
        ConsoleItem('appstream', 'Low Latency Application Streaming', 'https://console.aws.amazon.com/appstream/home?region={region}'.format(region=region), 'icons/services/appstream.png'),
        ConsoleItem('cloudsearch', 'Managed Search Service', 'https://{region}.console.aws.amazon.com/cloudsearch/home?region={region}'.format(region=region), 'icons/services/cloudsearch.png'),
        ConsoleItem('elastictranscoder', 'Easy-to-Use Scalable Media Transcoding', 'https://{region}.console.aws.amazon.com/elastictranscoder/home?region={region}'.format(region=region), 'icons/services/elastictranscoder.png'),
        ConsoleItem('ses', 'Email Sending and Receiving Service', 'https://{region}.console.aws.amazon.com/ses/home?region={region}'.format(region=region), 'icons/services/ses.png'),
        ConsoleItem('sqs', 'Message Queue Service', 'https://console.aws.amazon.com/sqs/home?region={region}'.format(region=region), 'icons/services/sqs.png'),
        ConsoleItem('swf', 'Workflow Service for Coordinating Application Components', 'https://{region}.console.aws.amazon.com/swf/home?region={region}'.format(region=region), 'icons/services/swf.png'),
        ConsoleItem('workspaces', 'Desktops in the Cloud', 'https://{region}.console.aws.amazon.com/workspaces/home?region={region}'.format(region=region), 'icons/services/workspaces.png'),
        ConsoleItem('workdocs', 'Secure Enterprise Storage and Sharing Service', 'https://console.aws.amazon.com/zocalo/home?region={region}'.format(region=region), 'icons/services/workdocs.png'),
        ConsoleItem('workmail', 'Secure Email and Calendaring Service', 'https://{region}.console.aws.amazon.com/workmail/home?region={region}'.format(region=region), 'icons/services/workmail.png'),
    ]
    if query:
        items = wf.filter(query, items, key=lambda i: i.key)
    for item in items:
        item = wf.add_item(
            title=item.key,
            subtitle=item.name,
            valid=True,
            autocomplete=complete + item.key,
            arg=item.url,
            icon=item.icon,
        )
        item.setvar('action', 'open-url')
    wf.send_feedback()
