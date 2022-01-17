# Custom exceptions class for webscraper
# Usage example:
# raise InvalidFilenameException -> will raise exception with the default message in msg
# raise InvalidFilenameException("test") -> will raise exception with message "test"
import platform

class InvalidFilenameException(Exception):
    def __init__(self, msg='Invalid filename supplied, has to be in format: storenameScraper.py', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class DriverException(Exception):
    def __init__(self, msg='geckodriver failed to run after multiple attempts of running', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class DBException(Exception):
    pass
class UnsupportedOSException(Exception):
    def __init__(self, msg=f'Operating System {platform.system()} not supported, exiting...', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)