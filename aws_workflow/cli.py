import logging
import os

import boto3
import click
from six.moves import configparser
from workflow import Workflow3
from workflow.background import run_in_background, is_running

from .base import find_ec2
from .base import find_s3_bucket
from .utils import parse_query


pass_wf = click.make_pass_decorator(Workflow3)
log = logging.getLogger('workflow')


@click.group()
@pass_wf
def cli(wf):
    pass


@cli.command()
@pass_wf
def list_profiles(wf):
    parser = configparser.ConfigParser()
    parser.read(os.path.expanduser('~/.aws/credentials'))
    for profile in parser.sections():
        wf.add_item(
            title=profile,
            valid=True,
            arg=profile,
        )
    wf.send_feedback()


@cli.command()
@click.argument('profile')
@pass_wf
def set_profile(wf, profile):
    wf.settings['profile'] = profile


@cli.command()
@pass_wf
def clear_cache(wf):
    def _filter(n):
        return not n.endswith('.pid')
    wf.clear_cache(_filter)


@cli.command()
@click.option('--quicklook_port', envvar='WF_QUICKLOOK_PORT')
@click.argument('query')
@pass_wf
def search(wf, quicklook_port, query):
    profile = wf.settings['profile']
    if profile is None:
        raise Exception('no profile selected')

    os.environ['AWS_PROFILE'] = profile

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
    region_name = boto3.Session().region_name
    find_ec2(wf, profile, region_name, terms, facets, quicklook_baseurl)
    find_s3_bucket(wf, profile, region_name, terms, facets, quicklook_baseurl)

    wf.send_feedback()


def main():
    wf = Workflow3()
    wf.run(lambda wf: cli(obj=wf))
