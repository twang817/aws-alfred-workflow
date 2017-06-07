import json

import mock
import pytest

from aws_alfred_workflow.cli import base
from aws_alfred_workflow.version import __version__


def test_cli_main():
    '''
    tests the main entry point function in cli/__init__.py

    ensures:
    - the main cli click group is called
    - the workflow is created
    '''
    from aws_alfred_workflow.cli import main
    import workflow
    with mock.patch('aws_alfred_workflow.cli.base.cli') as m:
        main()
        assert m.called
        assert isinstance(m.call_args[1]['obj']['wf'], workflow.Workflow3)


def test_no_args(runner):
    '''
    a test that covers the case where the main cli is called without any
    arguments.

    the current behavior is to display the help page and exit without error (a
    zero return code).
    '''
    with runner(base.cli, exit_code=0) as result:
        pass


def test_set_profile_no_profile(runner):
    '''
    tests that the set-profile subcommand when called without an argument
    displays an error and exits with a non-zero return code.
    '''
    with runner(base.cli, ['set-profile'], 2) as result:
        assert 'Missing argument "profile"' in result.output


def test_set_profile(runner, wf):
    '''
    tests that the set-profile subcommand properly sets the profile within the
    workflow settings dictionary.

    note, no validation is performed to ensure the profile exists.
    '''
    with runner(base.cli, ['set-profile', 'foo']) as result:
        assert wf.settings['profile'] == 'foo'


def test_clear_cache(runner, wf):
    '''
    tests that the clear-cache subcommand properly calls the workflow method to
    clear the cache.

    note, that coverage currently misses the filter that avoids clearing .pid
    files.
    '''
    with mock.patch.object(wf, 'clear_cache') as m:
        with runner(base.cli, ['clear-cache']) as result:
            assert m.call_count == 1


def test_open_help(runner, wf):
    '''
    tests that the open-help subcommand properly calls a subprocess that contains
    the url contained within the workflow configuration.
    '''
    with mock.patch('subprocess.Popen') as m:
        with runner(base.cli, ['open-help']) as result:
            assert m.called
            assert wf.help_url in m.call_args[0][0]


def test_check_update(runner, wf):
    '''
    tests that the check-update subcommand properly calls the check_update
    workflow method.
    '''
    with mock.patch.object(wf, 'check_update') as m:
        with runner(base.cli, ['check-update']) as result:
            assert m.called


def test_update_workflow(runner, wf):
    '''
    tests that the start-update subcommand properly calls the start_update
    workflow method.
    '''
    with mock.patch.object(wf, 'start_update', return_value=True) as m:
        with runner(base.cli, ['update-workflow']) as result:
            assert m.called


def test_update_workflow_no_update(runner, wf):
    '''
    tests that the start-update subcommand properly calls the start_update
    workflow method.

    note, this test primarily improves coverage by mocking the start_update
    workflow command to returrn false.
    '''
    with mock.patch.object(wf, 'start_update', return_value=False) as m:
        with runner(base.cli, ['update-workflow']) as result:
            assert m.called


def test_sf_group_no_args(runner):
    '''
    tests that the script-filter subcommand errors when called without any
    arguments.

    note that this is impossible, since the workflow will always call the
    script-filter subcommand with at least an empty string.
    '''
    with runner(base.cli, ['script-filter'], 2) as result:
        pass


def test_sf_group_empty_args(runner):
    '''
    tests that the script-filter subcommand, when called with an empty string,
    calls the default command.
    '''
    from aws_alfred_workflow.utils import default_command
    o = mock.MagicMock()
    default_command(o)
    with runner(base.cli, ['script-filter', '']) as result:
        assert o.call_count == 1


def test_sf_group_no_match(runner):
    '''
    tests that the script-filter subcommand, when called with something that
    does not match one of the registered subcomands, invokes the default
    command.
    '''
    from aws_alfred_workflow.utils import default_command
    o = mock.MagicMock()
    default_command(o)
    with runner(base.cli, ['script-filter', 'blah']) as result:
        assert o.call_count == 1


def test_wf_complete(runner):
    '''
    tests that the script-filter subcommand, when called with the workflow
    group subcommand, generates 5 completions (for the 5 subcommands).
    '''
    with runner(base.cli, ['script-filter', '>']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 5
        assert set(item['title'] for item in items) == set('profile clear-cache help check-update version'.split())
        for item in items:
            assert item.pop('arg')
            assert item.pop('title')
            assert item.pop('subtitle')
            assert item.pop('autocomplete')
            assert item.pop('valid')
            assert not item


def test_wf_profile_complete(runner):
    '''
    tests that the script-filter command, when called with a prefix of p for the
    workflow subcommands, returns an autocomplete for the profile command.
    '''
    with runner(base.cli, ['script-filter', '>p']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('arg') == 'profile'
        assert items[0].pop('title') == 'profile'
        assert items[0].pop('subtitle') == 'set the active profile'
        assert items[0].pop('autocomplete') == '>profile'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_profile(runner):
    '''
    tests that the script-filter command, when called with the profile subcommand,
    generates a list of profiles found in the .aws/config
    '''
    profiles = 'foo bar'.split()
    parser = mock.MagicMock()
    parser.sections.return_value = profiles
    with mock.patch('six.moves.configparser.ConfigParser', return_value=parser) as m:
        with runner(base.cli, ['script-filter', '>profile']) as result:
            items = json.loads(result.output)['items']
            assert len(items) == 2
            for i, profile in enumerate(profiles):
                assert json.loads(items[i]['arg']) == {
                    'alfredworkflow': {
                        'arg': 'set-profile %s' % profile,
                        'variables': {
                            'action': 'run-script,post-notification',
                            'notification_text': 'Selected profile: %s' % profile,
                        }
                    }
                }
                assert items[i]['title'] == profile
                assert not items[i]['subtitle']
                assert items[i]['autocomplete'] == '>profile ' + profile
                assert items[i]['valid']


def test_wf_profile_filter(runner):
    '''
    tests that the script-filter command, when called with the profile
    subcommand, with a partial name of a profile, generates a list matching
    profiles.
    '''
    profiles = 'foo bar'.split()
    parser = mock.MagicMock()
    parser.sections.return_value = profiles
    with mock.patch('six.moves.configparser.ConfigParser', return_value=parser) as m:
        with runner(base.cli, ['script-filter', '>profile f']) as result:
            items = json.loads(result.output)['items']
            print items
            assert len(items) == 1
            assert json.loads(items[0].pop('arg')) == {
                'alfredworkflow': {
                    'arg': 'set-profile foo',
                    'variables': {
                        'action': 'run-script,post-notification',
                        'notification_text': 'Selected profile: foo',
                    }
                }
            }
            assert items[0].pop('title') == 'foo'
            assert not items[0].pop('subtitle')
            assert items[0].pop('autocomplete') == '>profile foo' 
            assert items[0].pop('valid')
            assert not items[0]


def test_wf_clear_cache_complete(runner):
    '''
    tests that the script-filter command, when called with a prefix of cl for the
    workflow subcommands, returns an autocomplete for the clear-cache command.
    '''
    with runner(base.cli, ['script-filter', '>cl']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('arg') == 'clear-cache'
        assert items[0].pop('title') == 'clear-cache'
        assert items[0].pop('subtitle') == 'clears cache'
        assert items[0].pop('autocomplete') == '>clear-cache'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_clear_cache(runner):
    '''
    tests that the script-filter command, when called with the clear-cache subcommand,
    generates an arg that triggers a run-script of the clear-cache command.
    '''
    with runner(base.cli, ['script-filter', '>clear-cache']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert json.loads(items[0].pop('arg')) == {
            'alfredworkflow': {
                'arg': 'clear-cache',
                'variables': {
                    'action': 'run-script,post-notification',
                    'notification_text': 'cache cleared',
                }
            }
        }
        assert items[0].pop('title') == 'clear-cache'
        assert items[0].pop('subtitle') == 'clears cache'
        assert items[0].pop('autocomplete') == '>clear-cache'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_help_complete(runner):
    '''
    tests that the script-filter command, when called with a prefix of h for the
    workflow subcommands, returns an autocomplete for the help command.
    '''
    with runner(base.cli, ['script-filter', '>h']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('arg') == 'help'
        assert items[0].pop('title') == 'help'
        assert items[0].pop('subtitle') == 'opens help in browser'
        assert items[0].pop('autocomplete') == '>help'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_help(runner):
    '''
    tests that the script-filter command, when called with the help subcommand,
    generates an arg that triggers a run-script of the open-help command.
    '''
    with runner(base.cli, ['script-filter', '>help']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert json.loads(items[0].pop('arg')) == {
            'alfredworkflow': {
                'arg': 'open-help',
                'variables': {
                    'action': 'run-script',
                }
            }
        }
        assert items[0].pop('title') == 'help'
        assert items[0].pop('subtitle') == 'opens help in browser'
        assert items[0].pop('autocomplete') == '>help'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_check_update_complete(runner):
    '''
    tests that the script-filter command, when called with a prefix of ch for the
    workflow subcommands, returns an autocomplete for the check-update command.
    '''
    with runner(base.cli, ['script-filter', '>ch']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('arg') == 'check-update'
        assert items[0].pop('title') == 'check-update'
        assert items[0].pop('subtitle') == 'checks for updates'
        assert items[0].pop('autocomplete') == '>check-update'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_check_update(runner):
    '''
    tests that the script-filter command, when called with the check-update subcommand,
    generates an arg that triggers a run-script of the check-update command.
    '''
    with runner(base.cli, ['script-filter', '>check-update']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert json.loads(items[0].pop('arg')) == {
            'alfredworkflow': {
                'arg': 'check-update',
                'variables': {
                    'action': 'run-script',
                }
            }
        }
        assert items[0].pop('title') == 'check-update'
        assert items[0].pop('subtitle') == 'checks for updates'
        assert items[0].pop('autocomplete') == '>check-update'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_version_complete(runner):
    '''
    tests that the script-filter command, when called with a prefix of v for the
    workflow subcommands, returns an autocomplete for the version command.
    '''
    with runner(base.cli, ['script-filter', '>v']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('arg') == 'version'
        assert items[0].pop('title') == 'version'
        assert items[0].pop('subtitle').startswith('v')
        assert items[0].pop('autocomplete') == '>version'
        assert items[0].pop('valid')
        assert not items[0]


def test_wf_version(runner):
    '''
    tests that the script-filter command, when called with the version subcommand,
    generates a invalid completion item that displays the version number
    '''
    with runner(base.cli, ['script-filter', '>version']) as result:
        items = json.loads(result.output)['items']
        print items
        assert len(items) == 1
        assert items[0].pop('title') == 'version'
        assert items[0].pop('subtitle') == __version__
        assert items[0].pop('autocomplete') == '>version'
        assert not items[0].pop('valid')
        assert not items[0]
