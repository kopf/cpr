import logging
import threading
import sched

import docker
import requests


class ProbingThread(threading.Thread):
    def __init__(self, start_period, interval, retries, timeout, event, **kwargs):
        super(ProbingThread, self).__init__(**kwargs)
        self.start_period = start_period
        self.scheduler = sched.scheduler()
        self.interval = interval
        self.retries = retries
        self.timeout = timeout
        self.results = []
        self.healthy = True
        self.event = event
        self.restarting = False
        self.scheduler.enter(self.start_period, 1, self.trigger)

    def run(self):
        self.scheduler.run()

    def probe(self, *args, **kwargs):
        raise NotImplementedError()

    def restart_container(self):
        self.restarting = True
        client = docker.from_env()
        logging.info(f'Restarting {self.name}')
        client.containers.get(self.name).restart()
        self.restarting = False
        self.healthy = True
        self.event.set()
        self.scheduler.enter(self.start_period, 1, self.trigger)

    def trigger(self):
        if not self.healthy or not self.event.is_set():
            if not self.restarting:
                self.restart_container()
                return
        self.scheduler.enter(self.interval, 1, self.trigger)
        result = self.probe()
        self.results.append(result)
        self.results = self.results[-self.retries:]
        if len(self.results) == self.retries and all(not i for i in self.results):
            self.healthy = False
        else:
            self.healthy = True


class HTTPProbe(ProbingThread):
    def __init__(self, url, *args, **kwargs):
        super(HTTPProbe, self).__init__(*args, **kwargs)
        self.url = url

    def probe(self):
        try:
            requests.get(self.url, timeout=self.timeout).raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.warning(f'Probed {self.url} - Failure: {e}')
            return False
        logging.debug(f'Probed {self.url} - Success.')
        return True
