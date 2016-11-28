import datetime
import logging
import re


log = logging.getLogger('workflow')

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
