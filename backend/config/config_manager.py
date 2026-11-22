from config.settings import *


class ConfigManager:

    @staticmethod
    def app_name():
        return APP_NAME

    @staticmethod
    def version():
        return VERSION

    @staticmethod
    def owner():
        return OWNER_NAME

    @staticmethod
    def debug():
        return DEBUG

    @staticmethod
    def memory_file():
        return MEMORY_FILE

    @staticmethod
    def log_file():
        return LOG_FILE

    @staticmethod
    def max_history():
        return MAX_HISTORY