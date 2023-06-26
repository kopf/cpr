import threading

from probes import HTTPProbe

import pytest


@pytest.fixture
def blog_url():
    return 'http://blog'

@pytest.fixture
def retry_count():
    return 2

@pytest.fixture
def timeout():
    return 1

@pytest.fixture
def interval():
    return 0.1

@pytest.fixture(scope='function')
def httpprobe(blog_url, retry_count, timeout, interval):
    probe = HTTPProbe(blog_url, start_period=0, interval=interval, retries=retry_count, timeout=timeout, event=threading.Event())
    yield probe
    probe.event = False