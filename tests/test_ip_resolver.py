"""Tests for IP resolver module."""

import requests
import responses
import pytest

from cloudflare_ddns.ip_resolver import get_public_ip, ENDPOINTS


class TestIPv4Resolution:
    """Tests for IPv4 (record type A) resolution."""

    @responses.activate
    def test_successful_ipv4_resolution(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="203.0.113.42\n",
            status=200,
        )
        ip = get_public_ip("A")
        assert ip == "203.0.113.42"

    @responses.activate
    def test_ipv4_whitespace_is_stripped(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="  203.0.113.42  \n",
            status=200,
        )
        ip = get_public_ip("A")
        assert ip == "203.0.113.42"


class TestIPv6Resolution:
    """Tests for IPv6 (record type AAAA) resolution."""

    @responses.activate
    def test_successful_ipv6_resolution(self):
        responses.add(
            responses.GET,
            ENDPOINTS["AAAA"],
            body="2001:db8::1\n",
            status=200,
        )
        ip = get_public_ip("AAAA")
        assert ip == "2001:db8::1"

    @responses.activate
    def test_ipv6_whitespace_is_stripped(self):
        responses.add(
            responses.GET,
            ENDPOINTS["AAAA"],
            body="  2001:db8::1  \n",
            status=200,
        )
        ip = get_public_ip("AAAA")
        assert ip == "2001:db8::1"


class TestInvalidResponses:
    """Tests for invalid IP responses."""

    @responses.activate
    def test_invalid_ipv4_raises_value_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="not-an-ip\n",
            status=200,
        )
        with pytest.raises(ValueError, match="Invalid IP"):
            get_public_ip("A")

    @responses.activate
    def test_invalid_ipv6_raises_value_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["AAAA"],
            body="not-an-ipv6\n",
            status=200,
        )
        with pytest.raises(ValueError, match="Invalid IP"):
            get_public_ip("AAAA")

    @responses.activate
    def test_ipv6_returned_for_ipv4_record_type_raises_value_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="2001:db8::1\n",
            status=200,
        )
        with pytest.raises(ValueError, match="Invalid IP"):
            get_public_ip("A")

    @responses.activate
    def test_ipv4_returned_for_ipv6_record_type_raises_value_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["AAAA"],
            body="203.0.113.42\n",
            status=200,
        )
        with pytest.raises(ValueError, match="Invalid IP"):
            get_public_ip("AAAA")


class TestUnsupportedRecordType:
    """Tests for unsupported record types."""

    def test_unsupported_record_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported record type"):
            get_public_ip("MX")

    def test_empty_record_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported record type"):
            get_public_ip("")


class TestNetworkErrors:
    """Tests for network error handling."""

    @responses.activate
    def test_connection_error_raises_request_exception(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body=requests.ConnectionError("Connection refused"),
        )
        with pytest.raises(requests.ConnectionError):
            get_public_ip("A")

    @responses.activate
    def test_http_500_raises_http_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="Internal Server Error",
            status=500,
        )
        with pytest.raises(requests.HTTPError):
            get_public_ip("A")

    @responses.activate
    def test_http_404_raises_http_error(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body="Not Found",
            status=404,
        )
        with pytest.raises(requests.HTTPError):
            get_public_ip("A")

    @responses.activate
    def test_timeout_raises_request_exception(self):
        responses.add(
            responses.GET,
            ENDPOINTS["A"],
            body=requests.Timeout("Request timed out"),
        )
        with pytest.raises(requests.Timeout):
            get_public_ip("A")
