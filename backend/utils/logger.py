import logging
import os

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/astra.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


class AstraLogger:

    @staticmethod
    def info(message):
        logging.info(message)

    @staticmethod
    def error(message):
        logging.error(message)

    @staticmethod
    def warning(message):
        logging.warning(message)