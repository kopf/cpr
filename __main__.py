#!/usr/bin/env python3
import logging
import time

from probes import HTTPProbe


def main():
    t1 = HTTPProbe('http://blog', start_period=0, interval=1, retries=2, timeout=1)
    t2 = HTTPProbe('http://shop', start_period=1, interval=1, retries=2, timeout=1)
    t1.start()
    t2.start()
    while True:
        for thread in [t1, t2]:
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