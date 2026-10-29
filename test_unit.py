import signal
import time
from unittest import mock

import responses

from probes import TERMINATION_SIGNALS


def test_probe_thread_blocks_termination_signals(httpprobe):
    """Probe threads must block SIGTERM so the kernel delivers it to the main thread"""
    thread_mask = []
    with mock.patch.object(
        httpprobe, 'run', side_effect=lambda: thread_mask.append(signal.pthread_sigmask(signal.SIG_BLOCK, set()))
    ):
        main_mask_before = signal.pthread_sigmask(signal.SIG_BLOCK, set())
        httpprobe.start()
        httpprobe.join()
    assert TERMINATION_SIGNALS <= thread_mask[0]
    assert signal.pthread_sigmask(signal.SIG_BLOCK, set()) == main_mask_before
    assert not TERMINATION_SIGNALS & main_mask_before


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

