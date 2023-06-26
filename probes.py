import logging
import random
import threading
import sched


class ProbingThread(threading.Thread):
    def __init__(self, start_period, interval, retries, timeout):
        super(ProbingThread, self).__init__()
        self.scheduler = sched.scheduler()
        self.interval = interval
        self.retries = retries
        self.timeout = timeout
        self.results = []
        self.healthy = True
        self.scheduler.enter(start_period, 1, self.trigger)

    def run(self):
        self.scheduler.run()

    def trigger(self):
        if not self.healthy:
            return
        self.scheduler.enter(self.interval, 1, self.trigger)
        result = self.probe()
        self.results.append(result)
        self.results = self.results[-self.retries:]
        if len(self.results) == self.retries and all(not i for i in self.results):
            self.healthy = False


class HTTPProbe(ProbingThread):
    def __init__(self, url, *args, **kwargs):
        super(HTTPProbe, self).__init__(*args, **kwargs)
        self.url = url

    def probe(self):
        result = random.choice([True, False])

        if result:
            logging.debug(f'{self.url} - Success. {self.results}')
        else:
            logging.debug(f'{self.url} - Failure. {self.results}')
        return result