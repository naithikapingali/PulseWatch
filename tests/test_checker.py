from unittest.mock import Mock, patch
import pytest
from monitor.checker import validate_url, check_endpoint


def test_valid_url():
    assert validate_url(" https://example.com ") == "https://example.com"


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://example.com", "not-a-url", "https://user:pass@example.com"])
def test_invalid_url(url):
    with pytest.raises(ValueError):
        validate_url(url)


def test_success():
    endpoint={"id":1,"url":"https://example.com","method":"GET","expected_status":200,"contains_text":"hello"}
    response=Mock(status_code=200,text="hello world")
    response.__enter__=Mock(return_value=response)
    response.__exit__=Mock(return_value=False)
    with patch("monitor.checker.requests.request",return_value=response):
        result=check_endpoint(endpoint)
    assert result["healthy"] == 1
    assert result["status_code"] == 200


def test_unexpected_status():
    endpoint={"id":1,"url":"https://example.com","expected_status":200}
    response=Mock(status_code=503)
    response.__enter__=Mock(return_value=response)
    response.__exit__=Mock(return_value=False)
    with patch("monitor.checker.requests.request",return_value=response):
        result=check_endpoint(endpoint)
    assert result["healthy"] == 0
    assert "503" in result["error"]


def test_timeout():
    import requests
    endpoint={"id":1,"url":"https://example.com","expected_status":200}
    with patch("monitor.checker.requests.request",side_effect=requests.Timeout("timed out")):
        result=check_endpoint(endpoint)
    assert result["healthy"] == 0
    assert "Timeout" in result["error"]
