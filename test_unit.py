import time
from unittest import mock

import responses



@responses.activate
def test_httpprobe_no_errors(httpprobe, blog_url, interval, mocked_docker):
    """Should run indefinitely when no errors occur"""
    SLEEP_TIME = 2.0
    responses.get(blog_url)
    httpprobe.start()
    time.sleep(SLEEP_TIME)
    # Ensure probe was performed the expected number of times:
    assert responses.assert_call_count(blog_url, SLEEP_TIME / interval) is True
    # Ensure all status codes were 200:
    assert [call.response.status_code for call in responses.calls] == [200] * int(SLEEP_TIME / interval)
    assert not httpprobe.unhealthy.is_set()


@responses.activate
def test_httpprobe_retries(httpprobe, blog_url, retry_count, mocked_docker):
    """Should only probe the HTTP endpoint a maximum of `retry_count` times"""
    responses.add(responses.Response(method='GET', url=blog_url))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    with mock.patch.object(httpprobe, 'restart_container') as restart_mock:
        httpprobe.start()
        httpprobe.join()
        assert restart_mock.called
        assert responses.assert_call_count(blog_url, 1 + retry_count) is True
        assert httpprobe.unhealthy.is_set()

