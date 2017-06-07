import click

from ..utils import (
    get_default_command,
    get_profile,
    get_region,
    make_pass_decorator,
)


pass_wf = make_pass_decorator('wf')
pass_complete = make_pass_decorator('complete')
ensure_default_command = make_pass_decorator('default_command', ensure=True, factory=get_default_command)
ensure_profile = make_pass_decorator('profile', ensure=True, factory=get_profile)
ensure_region = make_pass_decorator('region', ensure=True, factory=get_region)


@click.group()
def cli():
    '''the main cli command'''


@click.group(invoke_without_command=True)
@click.argument('query', required=False)
@click.pass_context
def sf_commands(ctx, query):
    '''the root script-fliter command'''
    if ctx.invoked_subcommand is None:
        return ctx.obj['default_command'](args=(query,), parent=ctx)


@sf_commands.group('>')
def wf_commands():
    '''run a workflow command'''
