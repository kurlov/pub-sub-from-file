import asyncio

import pytest

from pub.publisher import Publisher


def test_parse_line_valid():
    result = Publisher.parse_line("John Smith, some@email.int")
    assert len(result) == 2
    is_valid, data = result
    assert is_valid is True
    assert data['name'] == "John Smith"
    assert data['email'] == "some@email.int"


def test_parse_line_wrong():
    result = Publisher.parse_line("John Smith, not_email")
    assert len(result) == 2
    is_valid, data = result
    assert is_valid is False
    assert data == {}


def test_parse_line_empty_name():
    result = Publisher.parse_line(", not_email")
    assert len(result) == 2
    is_valid, data = result
    assert is_valid is False
    assert data == {}

