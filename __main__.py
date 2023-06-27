#!/usr/bin/env python3
import logging
import time
import threading
import os
import sys

import docker

from probes import HTTPProbe

DEFAULT_START_PERIOD = int(os.getenv('CPR_DEFAULT_START_PERIOD', 1))
DEFAULT_INTERVAL = int(os.getenv('CPR_DEFAULT_INTERVAL', 3))
DEFAULT_RETRIES = int(os.getenv('CPR_DEFAULT_RETRIES', 2))
DEFAULT_TIMEOUT = int(os.getenv('CPR_DEFAULT_TIMEOUT', 1))
TICK_TIME = float(os.getenv('CPR_TICK_TIME', 0.5))
LOGLEVEL = getattr(logging, os.getenv('CPR_LOGLEVEL', 'DEBUG'))


def scan_containers():
    client = docker.from_env()
    retval = {}
    for container in client.containers.list():
        if container.labels.get('cpr.enabled') == 'true':
            event = threading.Event()
            event.set()
            retval[container.name] = {
                'url': container.labels['cpr.url'],
                'start_period': container.labels.get('cpr.start_period', DEFAULT_START_PERIOD),
                'interval': container.labels.get('cpr.interval', DEFAULT_INTERVAL),
                'retries': container.labels.get('cpr.retries', DEFAULT_RETRIES),
                'timeout': container.labels.get('cpr.timeout', DEFAULT_TIMEOUT),
                'event': event
            }
    return retval


def restart_container(container_name):
    client = docker.from_env()
    logging.info(f'Restarting {container_name}')
    return client.containers.get(container_name).restart()


def main():
    threads = []
    containers = scan_containers()
    for container_name, config in containers.items():
        threads.append(HTTPProbe(name=container_name, **config))
    if not threads:
        logging.error("No cpr-enabled containers found! Exiting...")
        sys.exit(-1)
    logging.info(f'Detected following cpr-enabled containers: {containers}')
    logging.info('Starting probe threads...')
    for thread in threads:
        thread.start()
    while True:
        for thread in threads:
            if not thread.healthy:
                logging.info(f'{thread.name} is unhealthy!')
                restart_container(thread.name)
            time.sleep(TICK_TIME)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(LOGLEVEL)
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(console_handler)
    if not os.path.exists('/var/run/docker.sock'):
        logging.exception("Unable to connect to docker. Have you mounted /var/run/docker.sock in the docker container?")
        sys.exit(-1)
    main()