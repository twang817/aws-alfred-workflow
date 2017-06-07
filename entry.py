import os
import sys

root = os.path.abspath(os.path.dirname(__file__))
vendor = os.path.join(root, 'vendor')
sys.path.append(vendor)

from aws_alfred_workflow.cli import main


if __name__ == '__main__':
    main()
