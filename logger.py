import logging
import sys

logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def prepare_handler(fhandler):
    formatter = logging.Formatter(logging_format)
    fhandler.setFormatter(formatter)
    return fhandler


def prepare_logger():
    logger = logging.getLogger()
    del logger.handlers[:]
    logger.addHandler(prepare_handler(logging.StreamHandler(sys.stderr)))
    logger.setLevel(logging.INFO)
