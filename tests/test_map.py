import re
from mock import Mock
from nose.tools import assert_equal
from unittest import TestCase

from strowger import Map
from strowger import Rule


class MapTestCase(TestCase):
    def setUp(self):
        self.map = Map()
        self.m_handler = Mock()

    def test_init(self):
        assert_equal(self.map.rules, [])
        assert_equal(self.map.default_handler, None)

    def test_add_rule(self):
        self.map.add_rule('foobar', self.m_handler)

        assert_equal(len(self.map.rules), 1)
        rule = self.map.rules[0]
        assert_equal(rule.pattern, re.compile('foobar'))
        assert_equal(rule.handler, self.m_handler)

        m_handler_2 = Mock()
        self.map.add_rule('Quux', m_handler_2, re.IGNORECASE)

        assert_equal(len(self.map.rules), 2)
        rule = self.map.rules[1]
        assert_equal(rule.pattern, re.compile('Quux', re.IGNORECASE))
        assert_equal(rule.handler, m_handler_2)

    def test_match(self):
        self.map.add_rule('foobar', self.m_handler)

        match, handler = self.map.match('foobar')
        assert_equal(match.start(), 0)
        assert_equal(handler, self.m_handler)

    def test_no_match(self):
        self.map.add_rule('quux', self.m_handler)

        match, handler = self.map.match('xyzzy plugh')
        assert_equal(match, None)
        assert_equal(handler, None)

    def test_default_handler(self):
        self.map = Map(default_handler=self.m_handler)
        m_handler_2 = Mock()

        self.map.add_rule('foobar', m_handler_2)

        match, handler = self.map.match('garply')
        assert_equal(match, None)
        assert_equal(handler, self.m_handler)

    def test_match_multiple_rules(self):
        self.map.add_rule('foobar', self.m_handler)
        m_handler_2 = Mock()

        self.map.add_rule('quux', m_handler_2)

        match, handler = self.map.match('foobarbaz')
        assert_equal(match.span(), (0, 6))
        assert_equal(handler, self.m_handler)

        match, handler = self.map.match('quux quuux')
        assert_equal(match.span(), (0, 4))
        assert_equal(handler, m_handler_2)
