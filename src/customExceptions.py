# Custom exceptions class for webscraper
# Usage example:

import platform, traceback
from scraperLoggers import scraperLogger

class InvalidFilenameException(Exception):
    def __init__(self, msg='Invalid filename supplied, has to be in format: storenameScraper.py', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        scraperLogger(level='ERROR',msg=msg)

class DriverException(Exception):
    def __init__(self, msg='geckodriver failed to run after multiple attempts', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        scraperLogger(level='ERROR',msg=f'Max attempts to turn on geckodriver reached, traceback: \n' + msg)

class DBException(Exception):
    pass

class UnsupportedOSException(Exception):
    def __init__(self, msg=f'Operating System {platform.system()} not supported, exiting...', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        scraperLogger(level='ERROR',msg=msg)

class StoreNotSupportedException(Exception):
    def __init__(self, msg=f'Online store not scrapable yet :(', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        scraperLogger(level='ERROR',msg=msg)

class ErrorDuringScrapingException(Exception):
    def __init__(self,msg=f'', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        scraperLogger(level='ERROR', msg = 'Some error happened during scraping: ' + msg)

class EmptyResultException(Exception):
    def __init__(self,storeName='', msg=f'Scraping result is empty, please check manually if the item desired exists in store ', **kwargs):
        super().__init__(msg + storeName, **kwargs)
        scraperLogger(level='ERROR',msg=msg)

class TunnelingTimeoutException(Exception):
    def __init__(self, msg=f'Timeout in tunneling, traceback:', **kwargs):
        super().__init__(msg, **kwargs)
        scraperLogger(level='ERROR',msg=f'Max attempts to tunnel reached, traceback: \n' + msg)

class UnavailableCredentialsException(Exception):
    def __init__(self, msg=f'', **kwargs):
        super().__init__(msg, **kwargs)
        scraperLogger(level='ERROR',msg=f'Credentials of database not available, traceback: \n' + msg)

class NoStoreFileException(Exception):
    def __init__(self, msg=f'', **kwargs):
        super().__init__(msg, **kwargs)
        scraperLogger(level='ERROR',msg=f'No store file (i.e. storenameScraper.py) available! \
                        Please check if you have at least one')
