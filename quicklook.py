import os
import sys

root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(os.path.join(root_dir, 'vendor'))

from aws_alfred_workflow.server import run


if __name__ == '__main__':
    run(port=int(sys.argv[1]), root_dir=root_dir)
