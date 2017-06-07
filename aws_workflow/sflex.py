import ply.lex as lex
import ply.yacc as yacc

states = (
    ('dquoted', 'exclusive'),
    ('squoted', 'exclusive'),
)
tokens = 'STRING'.split()
literals = ['"', "'", '>', '+', '@']

def t_empty_quotes(t):
    r"''|\"\""
    t.type = 'STRING'
    t.value = ''
    return t

def t_single_quote(t):
    r"'"
    t.lexer.push_state('squoted')

t_squoted_STRING = r"(?:.(?!(?<![\\])'))+."

def t_squoted_end(t):
    r"'"
    t.lexer.pop_state()

def t_double_quote(t):
    r'"'
    t.lexer.push_state('dquoted')

t_dquoted_STRING = r'(?:.(?!(?<![\\])"))+.'

def t_dquoted_end(t):
    r'"'
    t.lexer.pop_state()

def t_STRING(t):
    r"[a-zA-Z0-9_-]+"
    return t

t_ignore = ' \t'
t_squoted_ignore = ''
t_dquoted_ignore = ''

def t_ANY_error(t):
    t.lexer.skip(1)

lexer = lex.lex()
