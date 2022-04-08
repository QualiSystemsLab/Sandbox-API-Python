import logging


DEFAULT_LOGGER_NAME = "Sandbox Rest Logger"
DEFAULT_FORMAT = '%(asctime)s:%(filename)s:%(lineno)d %(message)s'


def set_up_default_logger(logger_name=DEFAULT_LOGGER_NAME,
                          log_level=logging.INFO,
                          log_to_file=False,
                          log_file_path=".",
                          log_format=DEFAULT_FORMAT):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    formatter = logging.Formatter(log_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_to_file:
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
