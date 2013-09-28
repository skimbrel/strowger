import re
from mock import Mock, patch
from nose.tools import assert_equal
from unittest import TestCase

from strowger import switch


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
        assert_equal(s.mapping, m_map)
