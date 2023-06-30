import logging
import threading
import sched
import os

import docker
import requests

CPR_VERSION = os.getenv('CPR_VERSION')


class ProbingThread(threading.Thread):
    def __init__(self, start_period, interval, retries, timeout, **kwargs):
        super(ProbingThread, self).__init__(**kwargs)
        self.start_period = start_period
        self.scheduler = sched.scheduler()
        self.interval = interval
        self.retries = retries
        self.timeout = timeout
        self.results = []
        self.unhealthy = threading.Event()
        self.restarting = False
        self.scheduler.enter(self.start_period, 1, self.trigger)

    def run(self):
        self.scheduler.run()

    def probe(self, *args, **kwargs):
        raise NotImplementedError()

    def restart_container(self):
        self.restarting = True
        client = docker.from_env()
        logging.warning(f'Restarting {self.name}')
        client.containers.get(self.name).restart()
        self.restarting = False
        self.unhealthy.clear()
        self.scheduler.enter(self.start_period, 1, self.trigger)

    def trigger(self):
        if self.unhealthy.is_set():
            if not self.restarting:
                self.restart_container()
            return
        next_scheduled_probe = self.scheduler.enter(self.interval, 1, self.trigger)
        result = self.probe()
        self.results.append(result)
        self.results = self.results[-self.retries:]
        if len(self.results) == self.retries and all(not i for i in self.results):
            self.scheduler.cancel(next_scheduled_probe)
            self.unhealthy.set()
            self.restart_container()
        else:
            self.unhealthy.clear()


class HTTPProbe(ProbingThread):
    def __init__(self, url, *args, user_headers=None, **kwargs):
        super(HTTPProbe, self).__init__(*args, **kwargs)
        self.url = url
        self.headers = {
            'User-Agent': f'cpr/{CPR_VERSION}'
        }
        if user_headers is not None:
            self.headers.update(user_headers)

    def probe(self):
        try:
            requests.get(
                self.url, timeout=self.timeout, headers=self.headers, allow_redirects=False
            ).raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f'Probed {self.url} - Failure: {e}')
            return False
        logging.debug(f'Probed {self.url} with headers {self.headers} - Success.')
        return True
