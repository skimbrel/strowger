import re
from mock import Mock, patch
from nose.tools import assert_equal
from nose.tools import assert_is_instance
from unittest import TestCase

from flask import request
from twilio import twiml

from strowger import switch

TEST_TWILIO_REQUEST_DATA = {
    'From': '+14155551234',
    'To': '+14158675309',
    'NumMedia': '0',
    'MessageSid': 'MM{}'.format('a' * 34),
    'AccountSid': 'AC{}'.format('a' * 34),
}


class SwitchTestCase(TestCase):
    def setUp(self):
        self.flask_patcher = patch('strowger.switch.Flask')
        self.m_flask = self.flask_patcher.start()
        self.map_patcher = patch('strowger.switch.Map')
        self.m_map_class = self.map_patcher.start()

    def tearDown(self):
        self.map_patcher.stop()
        self.flask_patcher.stop()

    def test_init(self):
        m_flask_app = Mock()
        self.m_flask.return_value = m_flask_app

        m_map = Mock()
        self.m_map_class.return_value = m_map

        s = switch.Switch(__name__)

        assert_equal(s.app, m_flask_app)
        m_flask_app.route.assert_called_with('/', methods=['GET', 'POST'])
        assert_equal(s.mapping, m_map)

        m_handler = Mock()
        s = switch.Switch(__name__, default_handler=m_handler)

        self.m_map_class.assert_called_with(default_handler=m_handler)


class SwitchWithFlaskAppTestCase(TestCase):
    def setUp(self):
        self.s = switch.Switch(__name__)
        self.s.app.testing = True
        self.app = self.s.app.test_client()

    def test_basic_handler(self):
        @self.s.connect('foobar')
        def _verify_handler(request, response):
            assert_equal(request.from_number, '+14155551234')
            assert_equal(request.to_number, '+14158675309')
            assert_equal(request.message_body, 'foobarbaz')
            assert_equal(request.media_count, 0)
            assert_is_instance(response, twiml.Response)
            response.message(msg='quux')
            return response


        request_data = TEST_TWILIO_REQUEST_DATA.copy()
        request_data['Body'] = 'foobarbaz'
        response = self.app.post('/', data=request_data)

        assert_equal(response.status_code, 200)

        twiml_response = twiml.Response()
        twiml_response.message(msg='quux')

        assert_equal(response.get_data(), unicode(twiml_response))

    def test_match_with_groups(self):
        @self.s.connect('(?P<first>\w+) (?P<second>\w+)')
        def _verify_handler(request, response, first, second):
            assert_equal(first, 'foo')
            assert_equal(second, 'bar')
            assert_equal(request.message_body, 'foo bar')
            return response

        request_data = TEST_TWILIO_REQUEST_DATA.copy()
        request_data['Body'] = 'foo bar'
        response = self.app.post('/', data=request_data)

        assert_equal(response.status_code, 200)

        twiml_response = twiml.Response()
        assert_equal(response.get_data(), unicode(twiml_response))

    def test_twilio_message_request(self):
        request_data = TEST_TWILIO_REQUEST_DATA.copy()
        request_data.update(
            Body='foo bar',
            NumMedia=2,
            MediaContentType0='image/jpeg',
            MediaUrl0='http://example.com/image0',
            MediaContentType1='image/png',
            MediaUrl1='http://example.com/image1',
            FromCity='San Francisco',
            FromState='CA',
        )

        with self.s.app.test_request_context('/', query_string=request_data):
            twilio_request = switch.TwilioMessageRequest(request)

            assert_equal(twilio_request.message_body, 'foo bar')
            assert_equal(twilio_request.from_number, '+14155551234')
            assert_equal(twilio_request.to_number, '+14158675309')
            assert_equal(twilio_request.message_sid, 'MM{}'.format('a' * 34))
            assert_equal(twilio_request.account_sid, 'AC{}'.format('a' * 34))
            assert_equal(twilio_request.media_count, 2)
            media_items = twilio_request.media_items
            assert_equal(
                media_items[0],
                switch.MediaItem('image/jpeg', 'http://example.com/image0'),
            )
            assert_equal(
                media_items[1],
                switch.MediaItem('image/png', 'http://example.com/image1'),
            )
            assert_equal(twilio_request.flask_request, request)
            assert_equal(twilio_request.raw_values, request.values)
