import workflow

from . import actions
from . import completions
from . import base
from ..version import __version__
from ..utils import setup_logger


def main():
    wf = workflow.Workflow3(
        update_settings={
            'github_slug': 'twang817/aws-alfred-workflow',
            'version': __version__,
        },
        help_url='https://github.com/twang817/aws-alfred-workflow/blob/master/README.md',
    )
    setup_logger(wf)
    wf.run(lambda wf: base.cli(obj={
        'wf': wf,
    }))
