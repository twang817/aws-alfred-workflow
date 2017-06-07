import logging

import click

from .base import (
    ensure_default_command,
    cli,
    pass_wf,
    sf_commands,
)
from .. import aws
from ..utils import (
    autocomplete_group,
)


log = logging.getLogger()


@cli.command('script-filter')
@click.argument('query')
@pass_wf
@ensure_default_command
def script_filter(query, wf, default_command):
    from ..lexers.scriptfilter import lexer
    ctx = click.get_current_context()
    lexer.input(query)
    cmd = sf_commands
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


@cli.command('open-help')
@pass_wf
def do_open_help(wf):
    wf.open_help()


@cli.command('check-update')
@pass_wf
def check_update(wf):
    wf.check_update(force=True)


@cli.command('update-workflow')
@pass_wf
def update_workflow(wf):
    if wf.start_update():
        log.info('updating alfred')
    else:
        log.info('no update found')


@cli.command('background')
@click.option('--data_name', envvar='WF_CACHE_DATA_NAME')
@click.argument('command')
@pass_wf
def background(command, data_name, wf):
    data = getattr(aws, command)()
    wf.cache_data(data_name, data)
