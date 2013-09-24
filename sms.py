import re
from collections import namedtuple

from flask import Flask
from flask import abort
from flask import request
from twilio import twiml


Map = namedtuple('Map', 'pattern handler')
MediaItem = namedtuple('MediaItem', 'content_type url')

RESPONSE_HEADERS = {'Content-Type': 'application/xml'}


class Router(object):

    def __init__(self, default_handler=None):
        self.routes = []
        self.default_handler = default_handler

    def add_route(self, pattern, handler):
        compiled = re.compile(pattern)
        self.routes.append(Map(compiled, handler))

    def match(self, body):
        for route in self.routes:
            if route.pattern.match(body):
                return route.handler

        return self.default_handler


class TwilioMessageRequest(object):

    def __init__(self, flask_request):
        self.from_number = flask_request.values['From']
        self.to_number = flask_request.values['To']
        self.message_body = flask_request.values['Body']
        self.media_count = int(flask_request.values['NumMedia'])
        self.media_items = []
        self.raw_values = flask_request.values

        if self.media_count > 0:
            media_items = []
            for index in xrange(self.media_count):
                url = flask_request.values['MediaUrl{}'.format(index)]
                ctype = flask_request.values[
                    'MediaContentType{}'.format(index)
                ]
                media_urls.append(MediaItem(ctype, url))

            self.media_items = media_items


class SmsApp(object):

    def __init__(self, name, request_path='/', default_handler=None, **kwargs):
        '''Create an SmsApp named `name`.

        Additional kwargs are passed to the underlying Flask application.
        '''
        self.app = Flask(name, **kwargs)
        self.router = Router(default_handler=default_handler)

        @self.app.route(request_path, methods=['GET', 'POST'])
        def twilio():
            body = request.values['Body']
            handler = self.router.match(body)

            if handler is None:
                # XXX Is this the right behavior?
                abort(404)

            # Set up our response and request
            twiml_response = twiml.Response()
            twilio_request = TwilioMessageRequest(request)

            try:
                handler(twilio_request, twiml_response)
                return unicode(twiml_response), 200, RESPONSE_HEADERS
            except:
                abort(500)

    def run(self, debug=False):
        self.app.run(debug=debug)
