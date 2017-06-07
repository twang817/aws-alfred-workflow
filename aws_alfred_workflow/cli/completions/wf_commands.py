import logging
import os

import click

from ..base import (
    pass_complete,
    pass_wf,
    wf_commands,
)
from ...utils import (
    set_version,
)
from ...version import __version__


log = logging.getLogger()


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
@click.argument('query', required=False)
@pass_wf
@pass_complete
def clear_cache(query, wf, complete):
    '''clears cache'''
    item = wf.add_item(
        title='clear-cache',
        subtitle='clears cache',
        valid=True,
        arg='clear-cache',
        autocomplete=complete)
    item.setvar('action', 'run-script,post-notification')
    item.setvar('notification_text', 'cache cleared')
    wf.send_feedback()


@wf_commands.command('help')
@click.argument('query', required=False)
@pass_wf
@pass_complete
def open_help(query, wf, complete):
    '''opens help in browser'''
    item = wf.add_item(
        title='help',
        subtitle='opens help in browser',
        valid=True,
        arg='open-help',
        autocomplete=complete)
    item.setvar('action', 'run-script')
    wf.send_feedback()


@wf_commands.command('check-update')
@click.argument('query', required=False)
@pass_wf
@pass_complete
def check_update(query, wf, complete):
    '''checks for updates'''
    item = wf.add_item(
        title='check-update',
        subtitle='checks for updates',
        valid=True,
        arg='check-update',
        autocomplete=complete)
    item.setvar('action', 'run-script')
    wf.send_feedback()


@wf_commands.command('version')
@click.argument('query', required=False)
@pass_wf
@pass_complete
@set_version
def get_version(query, wf, complete):
    '''%s'''
    item = wf.add_item(
        title='version',
        subtitle=__version__,
        valid=False,
        autocomplete=complete)
    wf.send_feedback()
