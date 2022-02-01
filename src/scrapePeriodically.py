# to be called by Cron

from webScraperCommon import Scrape, interrogateStoreRaw
from customExceptions import *
import re, os, importlib

def main():
    try:
        all_stores_from_files = [*filter(lambda x:re.search(r"\w+(?=Scraper.py)",x),os.listdir("."))]
        all_stores = [store.replace("Scraper.py", "") for store in all_stores_from_files]
    except AttributeError:
        raise NoStoreFileException
    
    try:
        username = os.environ["tweakersCloneUsername"]
        password = os.environ["tweakersClonePassword"]
    except KeyError as e:
        raise UnavailableCredentialsException(msg = traceback.format_exc())
    
    #make try excepts here too
    for store in all_stores:
        storeModule = importlib.import_module(store+"Scraper", package="")
        extractor_function = storeModule.extract_record

        dbFunctions = interrogateStoreRaw(username,password,dialect="mysql",schema="dateItemPrice")
        searchedItems = dbFunctions.searched_items_in_store(store)
        for searchedItem in searchedItems:
            print(f"Scraping {searchedItem} for store {store}")
            scrapeFunction = Scrape(store,searchedItem,extractor_function)
            scrapingResult = scrapeFunction.scrapeStore()
            print(f"Writing data of item {searchedItem} to {store}")
            dbFunctions.write_to_db(store,searchedItem,scrapingResult)

if __name__=="__main__":
    main()