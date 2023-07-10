#!/usr/bin/env python3
import json
import logging
import time
import os
import sys

import docker

from probes import HTTPProbe
import settings


def scan_containers():
    client = docker.from_env()
    retval = {}
    for container in client.containers.list():
        if container.labels.get('cpr.enabled') == 'true':
            retval[container.name] = {
                'url': container.labels['cpr.url'],
                'start_period': float(container.labels.get('cpr.start_period', settings.DEFAULT_START_PERIOD)),
                'interval': float(container.labels.get('cpr.interval', settings.DEFAULT_INTERVAL)),
                'retries': int(container.labels.get('cpr.retries', settings.DEFAULT_RETRIES)),
                'timeout': float(container.labels.get('cpr.timeout', settings.DEFAULT_TIMEOUT))
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
        time.sleep(settings.REFRESH_TIME)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(settings.LOGLEVEL)
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logging.getLogger().addHandler(console_handler)
    logging.info(f'cpr {settings.CPR_VERSION} starting...')
    if not os.path.exists('/var/run/docker.sock'):
        logging.exception("Unable to connect to docker. Have you mounted /var/run/docker.sock in the docker container?")
        sys.exit(-1)
    main()