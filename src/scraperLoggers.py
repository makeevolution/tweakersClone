import logging

def scraperLogger(level='INFO',msg='No message'):
    filename = __file__.strip(".py") + ".log"

    try:
        loggingLevel = getattr(logging,level)
    except AttributeError:
        level = "INFO"
        loggingLevel = getattr(logging,level)

    logger = logging.getLogger(__name__)
    logger.setLevel(loggingLevel)

    if logger.hasHandlers():
        logger.handlers.clear()

    file_handler = logging.FileHandler(filename)
    file_handler.setLevel(loggingLevel)

    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(file_handler)

    getattr(logger,level.lower())(msg)

if __name__=="__main__":
    scraperLogger()