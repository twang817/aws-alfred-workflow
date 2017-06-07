import datetime
import logging
import os

import boto3
import click
import workflow

from .version import __version__


log = logging.getLogger()


def setup_logger(wf):
    fmt = logging.Formatter('%(asctime)s %(filename)s:%(lineno)s %(levelname)-8s %(message)s', datefmt='%H:%M:%S')
    logfile = logging.handlers.RotatingFileHandler(
        wf.cachefile('%s.log' % wf.bundleid),
        maxBytes=1024 * 1024,
        backupCount=1)
    logfile.setFormatter(fmt)
    log.addHandler(logfile)
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    log.addHandler(console)
    if wf.debugging:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)


def json_serializer(obj):
    if isinstance(obj, datetime.datetime):
        s = obj.isoformat()
        return s
    raise TypeError('Type not serializable')


def filter_facets(wf, matches, facets):
    for k, v in facets.items():
        if v:
            matches = wf.filter(v, matches, key=lambda i: i['facets'].get(k.lower(), u''))
    return matches


def parse_query(query):
    terms, facets = [], {}
    log.debug('parsing query %s' % query)
    if query:
        from lexers.query import parser
        terms, facets = parser.parse(query)
    log.debug('terms: %s', terms)
    log.debug('facets: %s', facets)
    return terms, facets


def find_context(ctx, key):
    while ctx is not None:
        if isinstance(ctx.obj, dict) and key in ctx.obj:
            return ctx
        ctx = ctx.parent
    return None


def make_pass_decorator(key, ensure=False, factory=lambda: None):
    from functools import update_wrapper
    def decorator(f):
        def new_func(*args, **kwargs):
            ctx = click.get_current_context()
            found = find_context(ctx, key)
            if found is None:
                if not ensure:
                    raise RuntimeError('key %r not found in contexts' % key)
                else:
                    if ctx.obj is None:
                        ctx.obj = {}
                    if isinstance(ctx.obj, dict):
                        ctx.obj[key] = factory()
                    else:
                        raise RuntimeError('A non-dict context was found')
            kw = {
                key: ctx.obj[key]
            }
            kw.update(kwargs)
            return ctx.invoke(f, *args[1:], **kw)
        return update_wrapper(new_func, f)
    return decorator


_default_command = None


def default_command(cmd):
    global _default_command
    _default_command = cmd
    return cmd


def get_default_command():
    if _default_command is None:
        raise Exception('Misconfigured, no default command')
    return _default_command


def get_profile():
    ctx = click.get_current_context()
    ctx = find_context(ctx, 'wf')
    if ctx is None:
        raise RuntimeError('Could not find workflow to extract profile')
    wf = ctx.obj['wf']
    profile = wf.settings['profile']
    os.environ['AWS_PROFILE'] = profile
    return profile


def get_region():
    if 'AWS_PROFILE' not in os.environ:
        get_profile()
    region = boto3.Session().region_name
    os.environ['AWS_DEFAULT_REGION'] = region
    return region


def autocomplete_group(wf, query, group, complete, match=None):
    items = group.commands.keys()
    if query:
        items = wf.filter(query, items, match_on=match or workflow.MATCH_STARTSWITH)
    for item in items:
        wf.add_item(title=item,
                    subtitle=group.commands[item].__doc__ or '',
                    arg=item,
                    valid=True,
                    autocomplete=complete + item)
    wf.send_feedback()


def set_version(f):
    f.__doc__ = f.__doc__ % __version__
    return f
