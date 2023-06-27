import threading
import unittest.mock as mock

from probes import HTTPProbe

import docker
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


@pytest.fixture
def mocked_docker():
    with mock.patch.object(docker, 'from_env', return_value=mock.MagicMock):
        yield

@pytest.fixture(scope='function')
def httpprobe(blog_url, retry_count, timeout, interval):
    probe = HTTPProbe(blog_url, start_period=0, interval=interval, retries=retry_count, timeout=timeout)
    yield probe
    probe.unhealthy.set()