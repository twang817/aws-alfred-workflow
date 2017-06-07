from contextlib import contextmanager
import logging
import os
import tempfile

from click.testing import CliRunner
import pytest
import workflow

from aws_alfred_workflow.server import make_app


@pytest.fixture()
def root_dir():
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture()
def app(root_dir):
    return make_app(root_dir)


@pytest.fixture()
def runner(wf):
    runner = CliRunner()
    def _runner(cmd, args=None, exit_code=0, extra=None):
        result = runner.invoke(cmd, args, obj={'wf': wf}, **(extra or {}))
        if result.exception:
            if not isinstance(result.exception, SystemExit):
                import traceback
                traceback.print_exception(*result.exc_info)
        assert result.exit_code == exit_code
        yield result
    return contextmanager(_runner)


@pytest.fixture()
def wf():
    logger = logging.getLogger()
    wf = workflow.Workflow3(
        help_url='http://google.com',
    )
    wf.logger = logger
    yield wf
