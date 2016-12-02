from collections import namedtuple
import logging
import os
import sys

import boto3
import click
from workflow import (
    Workflow3,
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
from workflow.background import run_in_background, is_running

from .base import find_ec2
from .base import find_s3_bucket
from .utils import (
    autocomplete_group,
    get_profile,
    get_region,
    make_pass_decorator,
    parse_query,
)


log = logging.getLogger()


def setup_logger(wf):
    logger = logging.getLogger()
    fmt = logging.Formatter('%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    logfile = logging.handlers.RotatingFileHandler(
        wf.cachefile('%s.log' % wf.bundleid),
        maxBytes=1024 * 1024,
        backupCount=1)
    logfile.setFormatter(fmt)
    logger.addHandler(logfile)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    if wf.debugging:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    return logger


pass_wf = make_pass_decorator('wf')
pass_complete = make_pass_decorator('complete')
ensure_default_command = make_pass_decorator('default_command', ensure=True, factory=lambda: search)
ensure_profile = make_pass_decorator('profile', ensure=True, factory=get_profile)
ensure_region = make_pass_decorator('region', ensure=True, factory=get_region)


@click.group()
def cli():
    '''the main cli command'''


@cli.command('script-filter')
@click.argument('query')
@pass_wf
@ensure_default_command
def script_filter(query, wf, default_command):
    from .sflex import lexer
    ctx = click.get_current_context()
    lexer.input(query)
    cmd = root
    trimpos = 0
    complete, args = '', (query,)
    while True:
        # if cmd is a Command, run it
        if not hasattr(cmd, 'commands'):
            ctx.obj['complete'] = complete
            return cmd(args=args, parent=ctx)

        # otherwise, grab another token from the stream
        token = lexer.token()
        if not token:
            # if there are no more tokens in the stream, but we have not made it
            # to a command yet, then we need to check if the group wants to be
            # invoked even without a command.  note, this delegates the
            # responsibility of generating the autocompletion for the group to
            # the group callback
            if cmd.invoke_without_command:
                ctx.obj['complete'] = complete
                return cmd(args=args, parent=ctx)
            # if it does not, break here to perform autocompletion on the group's
            # subcommands
            break

        # search for the token in subcommands
        if token.value not in cmd.commands:
            # if not found, we need to check if the group wants to be invoked
            # without a command.  note, this delegates the responsibility of
            # generating the autocompletion for the group to the group callback
            if cmd.invoke_without_command:
                ctx.obj['complete'] = complete
                return cmd(args=args, parent=ctx)
            break

        # if were able to grab another token, update trimpos
        trimpos = token.lexpos + len(token.value)
        complete = query[:trimpos]
        args = (query[trimpos:].strip(),)

        cmd = cmd.commands[token.value]
    autocomplete_group(wf, getattr(token, 'value', None), cmd, complete)


@cli.command('set-profile')
@click.argument('profile')
@pass_wf
def set_profile(profile, wf):
    log.info('setting profile to %s' % profile)
    wf.settings['profile'] = profile


@cli.command('clear-cache')
@pass_wf
def clear_cache(wf):
    log.info('cache cleared')
    def _filter(n):
        return not n.endswith('.pid')
    wf.clear_cache(_filter)


@click.group(invoke_without_command=True)
@click.argument('query', required=False)
@click.pass_context
def root(ctx, query):
    '''the root cli command'''
    if ctx.invoked_subcommand is None:
        return ctx.obj['default_command'](args=(query,), parent=ctx)


@root.group('>')
def wf_commands():
    '''run a workflow command'''


@wf_commands.command('profile')
@click.argument('query', required=False)
@pass_wf
@pass_complete
def list_profiles(query, wf, complete):
    '''set the active profile'''
    from six.moves import configparser
    parser = configparser.ConfigParser()
    parser.read(os.path.expanduser('~/.aws/credentials'))
    profiles = parser.sections()
    if query:
        profiles = wf.filter(query, profiles)
    for profile in profiles:
        item = wf.add_item(
            title=profile,
            valid=True,
            arg='set-profile %s' % profile,
            autocomplete=' '.join([complete, profile]),
        )
        item.setvar('action', 'run-script,post-notification')
        item.setvar('notification_text', 'Selected profile: %s' % profile)
    wf.send_feedback()


@wf_commands.command('clear-cache')
@pass_wf
def clear_cache(wf):
    '''clears cache'''
    item = wf.add_item(
        title='clear cache',
        subtitle='clears cache',
        valid=True,
        arg='clear-cache',
        autocomplete='clear-cache')
    item.setvar('action', 'run-script,post-notification')
    item.setvar('notification_text', 'cache cleared')
    wf.send_feedback()


@wf_commands.command('help')
def help():
    '''opens help in browser'''
    raise NotImplementedError('Not Implemented')


@root.command('+')
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



@click.command()
@click.option('--quicklook_port', envvar='WF_QUICKLOOK_PORT')
@click.argument('query')
@pass_wf
@ensure_profile
@ensure_region
def search(quicklook_port, query, wf, profile, region):
    quicklook_baseurl = None
    if quicklook_port is not None:
        if not is_running('quicklook'):
            log.info('\n'.join('%s = %s' % (k, v) for k, v in os.environ.items()))
            log.info('launching quicklook server on port %s' % quicklook_port)
            run_in_background('quicklook', ['/usr/bin/env',
                                            'python',
                                            wf.workflowfile('quicklook_server.py'),
                                            quicklook_port])
        else:
            log.info('quicklook server should be on port %s' % quicklook_port)
        quicklook_baseurl = 'http://localhost:%s/quicklook' % quicklook_port

    terms, facets = parse_query(query)
    find_ec2(wf, profile, region, terms, facets, quicklook_baseurl)
    find_s3_bucket(wf, profile, region, terms, facets, quicklook_baseurl)

    wf.send_feedback()


def main():
    wf = Workflow3()
    setup_logger(wf)
    wf.run(lambda wf: cli(obj={
        'wf': wf,
    }))
