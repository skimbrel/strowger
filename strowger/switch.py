import re
from collections import namedtuple
from functools import wraps

from flask import Flask
from flask import abort
from flask import request
from twilio import twiml


Rule = namedtuple('Rule', 'pattern handler')
MediaItem = namedtuple('MediaItem', 'content_type url')

RESPONSE_HEADERS = {'Content-Type': 'application/xml'}


class Map(object):

    def __init__(self, default_handler=None):
        self.rules = []
        self.default_handler = default_handler

    def add_rule(self, pattern, handler, flags=0):
        compiled = re.compile(pattern, flags=flags)
        self.rules.append(Rule(compiled, handler))

    def match(self, body):
        for rule in self.rules:
            m = rule.pattern.match(body)
            if m is not None:
                return m, rule.handler

        return None, self.default_handler


class TwilioMessageRequest(object):

    def __init__(self, flask_request):
        self.from_number = flask_request.values['From']
        self.to_number = flask_request.values['To']
        self.message_body = flask_request.values['Body']
        self.media_count = int(flask_request.values['NumMedia'])
        self.media_items = []
        self.raw_values = flask_request.values
        self.flask_request = flask_request

        if self.media_count > 0:
            media_items = []
            for index in xrange(self.media_count):
                url = flask_request.values['MediaUrl{}'.format(index)]
                ctype = flask_request.values[
                    'MediaContentType{}'.format(index)
                ]
                media_urls.append(MediaItem(ctype, url))

            self.media_items = media_items


class Switch(object):

    def __init__(self, name, request_path='/', methods=None,
                 default_handler=None, **kwargs):
        '''Create a Switch named `name`.

        Additional kwargs are passed to the underlying Flask application.
        '''
        self.app = Flask(name, **kwargs)
        self.mapping = Map(default_handler=default_handler)

        if methods is None:
            methods = ['GET', 'POST']

        @self.app.route(request_path, methods=methods)
        def twilio():
            body = request.values['Body']
            match_obj, handler = self.mapping.match(body)

            if handler is None:
                # XXX Is this the right behavior?
                abort(404)

            # Set up our response and request
            twiml_response = twiml.Response()
            twilio_request = TwilioMessageRequest(request)

            if match_obj is not None:
                kwargs = match_obj.groupdict()
            else:
                kwargs = {}

            try:
                response = handler(twilio_request, twiml_response, **kwargs)
                return unicode(response), 200, RESPONSE_HEADERS
            except:
                abort(500)

    def connect(self, pattern, flags=0):
        def _decorator(f):
            self.mapping.add_rule(pattern, f, flags=flags)
            @wraps(f)
            def wrapped(*args, **kwargs):
                return f(*args, **kwargs)
        return _decorator

    def set_default_handler(self, handler):
        self.mapping.default_handler = handler

    def run(self, debug=False):
        self.app.run(debug=debug)

    def __call__(self, *args, **kwargs):
        return self.app(*args, **kwargs)
