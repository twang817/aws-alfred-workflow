import json
import os
import sys

from jinja2 import Environment, FileSystemLoader
import tornado.autoreload
import tornado.ioloop
import tornado.web


class BaseHandler(tornado.web.RequestHandler):
    def enrich(self, context):
        pass

    def get(self):
        template = templates.get_template(self.template)
        context = json.loads(self.get_argument('context', '{}'))
        self.enrich(context)
        self.write(template.render(**context))


class Ec2QuicklookHandler(BaseHandler):
    template = 'ec2.html.j2'


class S3QuicklookHandler(BaseHandler):
    template = 's3.html.j2'


class RdsQuicklookHandler(BaseHandler):
    template = 'rds.html.j2'


class CfnQuicklookHandler(BaseHandler):
    template = 'cfn.html.j2'


class SqsQuicklookHandler(BaseHandler):
    template = 'sqs.html.j2'


class RedshiftClusterQuicklookHandler(BaseHandler):
    template = 'redshift.html.j2'


def make_app():
    return tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.getcwd(), 'static')}),
        (r'/quicklook/ec2', Ec2QuicklookHandler),
        (r'/quicklook/s3', S3QuicklookHandler),
        (r'/quicklook/rds', RdsQuicklookHandler),
        (r'/quicklook/cfn', CfnQuicklookHandler),
        (r'/quicklook/sqs', SqsQuicklookHandler),
        (r'/quicklook/redshift', RedshiftClusterQuicklookHandler),
    ])


if __name__ == '__main__':
    templates = Environment(loader=FileSystemLoader(os.path.join(os.getcwd(), 'templates')))
    app = make_app()
    app.listen(int(sys.argv[1]))
    tornado.autoreload.start()
    tornado.ioloop.IOLoop.current().start()
