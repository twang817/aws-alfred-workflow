import json
import os
import sys

# pylint: disable=locally-disabled,wrong-import-position
from jinja2 import Environment, FileSystemLoader
import tornado.autoreload
import tornado.ioloop
import tornado.web


class QuicklookHandler(tornado.web.RequestHandler):
    # pylint: disable=locally-disabled,abstract-method
    def __init__(self, application, request, **kwargs):
        self.env = kwargs.pop('env')
        super(QuicklookHandler, self).__init__(application, request, **kwargs)

    def enrich(self, context):
        pass


class Ec2InstanceQuicklookHandler(QuicklookHandler):
    # pylint: disable=locally-disabled,abstract-method
    def get(self):
        template = self.env.get_template('ec2_instance.html.j2')
        context = json.loads(self.get_argument('context', '{}'))
        self.enrich(context)
        self.write(template.render(**context))


class S3BucketQuicklookHandler(QuicklookHandler):
    # pylint: disable=locally-disabled,abstract-method
    def get(self):
        template = self.env.get_template('s3_bucket.html.j2')
        context = json.loads(self.get_argument('context', '{}'))
        self.enrich(context)
        self.write(template.render(**context))


class RdsInstanceQuicklookHandler(QuicklookHandler):
    # pylint: disable=locally-disabled,abstract-method
    def get(self):
        template = self.env.get_template('rds_instance.html.j2')
        context = json.loads(self.get_argument('context', '{}'))
        self.enrich(context)
        self.write(template.render(**context))


class RdsClusterQuicklookHandler(QuicklookHandler):
    # pylint: disable=locally-disabled,abstract-method
    def get(self):
        template = self.env.get_template('rds_cluster.html.j2')
        context = json.loads(self.get_argument('context', '{}'))
        self.enrich(context)
        self.write(template.render(**context))


def make_app(root_dir):
    env = Environment(loader=FileSystemLoader(os.path.join(root_dir, 'templates')))
    return tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(root_dir, 'static')}),
        (r'/quicklook/ec2_instance', Ec2InstanceQuicklookHandler, {'env': env}),
        (r'/quicklook/s3_bucket', S3BucketQuicklookHandler, {'env': env}),
        (r'/quicklook/rds_instance', RdsInstanceQuicklookHandler, {'env': env}),
        (r'/quicklook/rds_cluster', RdsClusterQuicklookHandler, {'env': env}),
    ])


def run(port, root_dir):
    app = make_app(root_dir)
    app.listen(port)
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.current().start()
