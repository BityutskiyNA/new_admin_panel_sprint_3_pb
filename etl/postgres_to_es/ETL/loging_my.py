import logging

logger_one = logging.getLogger('main')
file_handler_one = logging.FileHandler("app.log")
file_handler_one.setLevel(logging.INFO)
logger_one.addHandler(file_handler_one)
logger_one.debug(True)
