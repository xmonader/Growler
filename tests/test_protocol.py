#
# tests/test_protocol.py
#

import growler
from growler.aio import GrowlerProtocol

import pytest
import asyncio
from unittest import mock

from mocks import *


@pytest.fixture
def mock_handler():
    handler = mock.Mock()
    return handler


@pytest.fixture
def mock_responder():
    mock_handler = mock.Mock()
    responder = growler.http.responder.GrowlerHTTPResponder(mock_handler)
    return mock.Mock(wraps=responder)


@pytest.fixture
def m_make_responder(mock_responder):
    mock_factory = mock.Mock(return_value=mock_responder)
    return mock_factory


@pytest.fixture
def proto(mock_event_loop, m_make_responder):
    return GrowlerProtocol(mock_event_loop, m_make_responder)


@pytest.fixture
def listening_proto(proto, mock_transport):
    proto.connection_made(mock_transport)
    return proto


@pytest.fixture
def mock_protocol(mock_event_loop, m_make_responder):
    # return MockGrowlerProtocol()(mock_event_loop, m_make_responder)
    return GrowlerProtocol(mock_event_loop, m_make_responder)


def test_mock_protocol(mock_protocol, mock_event_loop, mock_responder):
    from growler.aio import GrowlerProtocol
    assert isinstance(mock_protocol, GrowlerProtocol)


def test_constructor(mock_event_loop):
    proto = GrowlerProtocol(mock_event_loop, mock_responder)

    assert isinstance(proto, asyncio.Protocol)
    assert proto.make_responder is mock_responder


def test_connection_made(proto, mock_transport, mock_responder, m_make_responder):
    host_info = ('mock.host', 2112)
    mock_transport.get_extra_info.return_value = host_info
    proto.connection_made(mock_transport)
    assert proto.transport is mock_transport
    assert proto.responders[0] is mock_responder
    assert proto.remote_port is host_info[-1]
    mock_transport.get_extra_info.assert_called_with('peername')
    m_make_responder.assert_called_with(proto)


def test_on_data(listening_proto, mock_responder):
    data = b'data'
    listening_proto.data_received(data)
    mock_responder.on_data.assert_called_with(data)


@pytest.mark.parametrize('mock_responder', [
    None,
    mock.Mock(spec=int)
])
def test_missing_responder(proto, mock_transport):
    with pytest.raises(TypeError):
        proto.connection_made(mock_transport)


def test_eof_received(proto):
    proto.eof_received()
    assert proto.is_done_transmitting


def test_connection_lost_no_exception(proto):
    proto.connection_lost(None)


def test_connection_lost_with_exception(proto):
    ex = Exception()
    proto.connection_lost(ex)


def test_on_data_error(listening_proto, mock_responder):
    data = b'data'
    ex = Exception()
    mock_responder.on_data.side_effect = ex
    with pytest.raises(NotImplementedError):
        listening_proto.data_received(data)


def test_factory():
    proto = GrowlerProtocol.factory(None, None)
    assert isinstance(proto, GrowlerProtocol)


def test_get_factory():
    factory = GrowlerProtocol.get_factory(None, None)
    assert callable(factory)
    proto = factory()
    assert isinstance(proto, GrowlerProtocol)
