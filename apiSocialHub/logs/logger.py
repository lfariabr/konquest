import os
import logging


def configure_logger(logger_name, log_file, log_level=logging.INFO):
    """
    Configure and return a logger.
    :param logger_name: Name of the logger
    :param log_file: File path for the log file
    :param log_level: Logging level
    :return: Configured logger
    """
    # Ensuring 'logs' directory exists
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Logger config
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Avoiding duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    return logger

# Defining root directory/log files
root_directory = os.path.dirname(os.path.abspath(__file__))
root_directory = os.path.dirname(root_directory)

# Configuring loggers
send_file_message_log_path = os.path.join(root_directory, 'logs', 'send_file_message.log')
send_text_message_log_path = os.path.join(root_directory, 'logs', 'send_text_message.log')

send_file_logger = configure_logger('send_file_message', send_file_message_log_path)
send_text_logger = configure_logger('send_text_message', send_text_message_log_path)