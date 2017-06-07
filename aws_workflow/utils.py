# -*- coding: utf-8 -*-
import datetime
import logging
import os

import boto3
import click

from .version import __version__


log = logging.getLogger()

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
        from .qlex import parser
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


def autocomplete_group(wf, query, group, complete):
    items = group.commands.keys()
    if query:
        items = wf.filter(query, items)
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


def create_stack_status_icons():
    """
    Using statuses from
    https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html#d0e12244

    Note that, due to its dynamic nature, this function creates a couple of unused keys in the status icons dict
    """
    status_icons = {}

    verbs = [
        'CREATE',
        'DELETE',
        'REVIEW',
        'UPDATE',
        'ROLLBACK',
        'UPDATE_ROLLBACK',
    ]
    states = {
        'IN_PROGRESS': u'⏲',
        'FAILED': u'❌',
        'COMPLETE': u'✅',
    }

    for verb in verbs:
        for key in states.keys():
            status_icons['%s_%s' % (verb, key)] = states[key]

    # custom statuses
    status_icons['UPDATE_COMPLETE_CLEANUP_IN_PROGRESS'] \
        = status_icons['UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS'] \
        = states['IN_PROGRESS']

    return status_icons
