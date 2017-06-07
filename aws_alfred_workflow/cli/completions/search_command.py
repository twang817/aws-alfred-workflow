import logging
import os

import click

from ..base import (
    ensure_profile,
    ensure_region,
    pass_wf,
)
from ... import aws
from ...utils import default_command


log = logging.getLogger()


@default_command
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
                                            wf.workflowfile('quicklook/server.py'),
                                            quicklook_port])
        else:
            log.info('quicklook server should be on port %s' % quicklook_port)
        quicklook_baseurl = 'http://localhost:%s/quicklook' % quicklook_port

    terms, facets = parse_query(query)
    #aws.find_ec2(wf, profile, region, terms, facets, quicklook_baseurl)
    #aws.find_s3_bucket(wf, profile, region, terms, facets, quicklook_baseurl)
    #aws.find_database(wf, profile, region, terms, facets, quicklook_baseurl)

    wf.send_feedback()
