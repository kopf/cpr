#!/usr/bin/env python3
import json
import logging
import time
import os
import sys

import docker

from probes import HTTPProbe

DEFAULT_START_PERIOD = int(os.getenv('CPR_DEFAULT_START_PERIOD', 8))
DEFAULT_INTERVAL = int(os.getenv('CPR_DEFAULT_INTERVAL', 3))
DEFAULT_RETRIES = int(os.getenv('CPR_DEFAULT_RETRIES', 2))
DEFAULT_TIMEOUT = int(os.getenv('CPR_DEFAULT_TIMEOUT', 1))
REFRESH_TIME = int(os.getenv('CPR_REFRESH_TIME', 60))
LOGLEVEL = getattr(logging, os.getenv('CPR_LOGLEVEL', 'INFO'))


def scan_containers():
    client = docker.from_env()
    retval = {}
    for container in client.containers.list():
        if container.labels.get('cpr.enabled') == 'true':
            retval[container.name] = {
                'url': container.labels['cpr.url'],
                'start_period': int(container.labels.get('cpr.start_period', DEFAULT_START_PERIOD)),
                'interval': int(container.labels.get('cpr.interval', DEFAULT_INTERVAL)),
                'retries': int(container.labels.get('cpr.retries', DEFAULT_RETRIES)),
                'timeout': int(container.labels.get('cpr.timeout', DEFAULT_TIMEOUT))
            }
            user_headers = container.labels.get('cpr.headers', '{}')
            try:
                retval[container.name]['user_headers'] = json.loads(user_headers)
            except json.decoder.JSONDecodeError as e:
                logging.error(f"Could not parse JSON value {user_headers} - {e}")
    return retval


def main():
    threads = []
    seen_containers = set()
    while True:
        containers = scan_containers()
        for container_name, config in containers.items():
            if container_name not in seen_containers:
                seen_containers.add(container_name)
                threads.append(HTTPProbe(name=container_name, **config))
        if not threads:
            logging.critical("No cpr-enabled containers found!")
        else:
            logging.debug(f'Detected following cpr-enabled containers: {containers}')
        new_threads = []
        for thread in threads:
            if not thread.is_alive():
                thread.start()
                new_threads.append(thread.name)
        if new_threads:
            logging.info(f'Started {len(new_threads)} new probe thread{"s" if len(new_threads)>1 else ""}: {new_threads}')
        time.sleep(REFRESH_TIME)


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