#!/usr/bin/env python3
import logging
import time
import threading
import sys

import docker

from probes import HTTPProbe

DEFAULT_START_PERIOD = 1
DEFAULT_INTERVAL = 3
DEFAULT_RETRIES = 2
DEFAULT_TIMEOUT = 1


def scan_containers():
    client = docker.from_env()
    retval = {}
    for container in client.containers.list():
        if container.labels.get('cpr.enabled') == 'true':
            retval[container.name] = {
                'url': container.labels['cpr.url'],
                'start_period': container.labels.get('cpr.start_period', DEFAULT_START_PERIOD),
                'interval': container.labels.get('cpr.interval', DEFAULT_INTERVAL),
                'retries': container.labels.get('cpr.retries', DEFAULT_RETRIES),
                'timeout': container.labels.get('cpr.timeout', DEFAULT_TIMEOUT),
                'event': threading.Event()
            }
    return retval


def main():
    threads = []
    for container_name, config in scan_containers().items():
        threads.append(HTTPProbe(name=container_name, **config))
    if not threads:
        logging.error("No cpr-enabled containers found! Exiting...")
        sys.exit(-1)
    for thread in threads:
        thread.start()
    while True:
        for thread in threads:
            if not thread.healthy:
                logging.info(f'{thread} is unhealthy!')
            time.sleep(0.5)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(console_handler)
    main()