import datetime
import logging
import os
import re

import boto3
import click


log = logging.getLogger()

def json_serializer(obj):
    if isinstance(obj, datetime.datetime):
        s = obj.isoformat()
        return s
    raise TypeError('Type not serializable')


QUOTED_TERMS = re.compile(r'(?:[^\s,"]|"(?:\\.|[^"])*")+')
QUOTED_SPLIT = re.compile(''':(?=(?:[^'"]|'[^']*'|"[^"]*")*$)''')


def filter_facets(wf, matches, facets):
    for k, v in facets.items():
        if v:
            matches = wf.filter(v, matches, key=lambda i: i['facets'].get(k.lower(), u''))
    return matches


def parse_query(query):
    terms, facets = [], {}
    if query:
        atoms = QUOTED_TERMS.findall(query)
        for atom in atoms:
            if ':' in atom:
                k, v = QUOTED_SPLIT.split(atom)
                facets[k] = v.strip("'\"")
            else:
                terms.append(atom)
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


group_map = {}
def get_group_map():
    return group_map


def leader(key, type):
    def decorator(f):
        group = getattr(click, type)()(f)
        group_map[key] = group
        return group
    return decorator
