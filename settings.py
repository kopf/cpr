import logging
import os


CPR_VERSION = os.getenv('CPR_VERSION')

DEFAULT_START_PERIOD = int(os.getenv('CPR_DEFAULT_START_PERIOD', 8))
DEFAULT_INTERVAL = int(os.getenv('CPR_DEFAULT_INTERVAL', 3))
DEFAULT_RETRIES = int(os.getenv('CPR_DEFAULT_RETRIES', 2))
DEFAULT_TIMEOUT = int(os.getenv('CPR_DEFAULT_TIMEOUT', 1))
REFRESH_TIME = int(os.getenv('CPR_REFRESH_TIME', 60))
LOGLEVEL = getattr(logging, os.getenv('CPR_LOGLEVEL', 'INFO'))