import time

import responses

@responses.activate
def test_httpprobe_no_errors(httpprobe, blog_url, interval):
    """Should run indefinitely when no errors occur"""
    SLEEP_TIME = 2.0
    responses.get(blog_url)
    httpprobe.start()
    time.sleep(SLEEP_TIME)
    # Ensure probe was performed the expected number of times:
    assert responses.assert_call_count(blog_url, SLEEP_TIME / interval) is True
    # Ensure all status codes were 200:
    assert [call.response.status_code for call in responses.calls] == [200] * int(SLEEP_TIME / interval)
    assert httpprobe.healthy is True


@responses.activate
def test_httpprobe_retries(httpprobe, blog_url, retry_count):
    """Should only probe the HTTP endpoint a maximum of `retry_count` times"""
    responses.add(responses.Response(method='GET', url=blog_url))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    responses.add(responses.Response(method='GET', url=blog_url, status=500))
    httpprobe.start()
    httpprobe.join()
    assert responses.assert_call_count(blog_url, 1 + retry_count) is True
    assert httpprobe.healthy is False

