# Custom exceptions class for webscraper
# Usage example:
# raise InvalidFilenameException -> will raise exception with the default message in msg
# raise InvalidFilenameException("test") -> will raise exception with message "test"
import platform

class InvalidFilenameException(Exception):
    def __init__(self, msg='Invalid filename supplied, has to be in format: storenameScraper.py', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class DriverException(Exception):
    def __init__(self, msg='geckodriver failed to run after multiple attempts', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class DBException(Exception):
    pass
class UnsupportedOSException(Exception):
    def __init__(self, msg=f'Operating System {platform.system()} not supported, exiting...', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class StoreNotSupportedException(Exception):
    def __init__(self, msg=f'Online store not scrapable yet :(', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class ErrorDuringScrapingException(Exception):
    def __init__(self,msg=f'Some error happened during scraping', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
class EmptyResultException(Exception):
    def __init__(self,storeName=" ", msg=f'Scraping result is empty, please check manually if the item desired exists in store ', **kwargs):
        super().__init__(msg + storeName, **kwargs)