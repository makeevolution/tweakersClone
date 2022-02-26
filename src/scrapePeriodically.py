# to be called by Cron

from webScraperCommon import Scrape, SSHTunnelOperations, interrogateStoreRaw
from customExceptions import *
import re, os, importlib, sshtunnel

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
    
    sshFunctions = SSHTunnelOperations(username,password,"mysql","dateItemPrice")
    
    sshFunctions.start_tunnel()
    URIForDB = sshFunctions.getURI()
    
    dbFunctions = interrogateStoreRaw(URIForDB)
    dbFunctions.start_db_session()
    #make try excepts here too
    for store in ["coolblue"]:
        storeModule = importlib.import_module(store+"Scraper", package="")
        extractor_function = storeModule.extract_record

        searchedItems = dbFunctions.searched_items_in_store(store)
        if not searchedItems:
            searchedItems = ["Sony WH-1000XM3"]
        for searchedItem in searchedItems:
            scraperLogger(f"Scraping {searchedItem} for store {store}")
            scrapeFunction = Scrape(store,searchedItem,extractor_function)
            scrapingResult = scrapeFunction.scrapeStore()
            scraperLogger(f"Writing data of item {searchedItem} to {store}")
            dbFunctions.write_to_db(store,searchedItem,scrapingResult)
            scraperLogger(f"Done writing")
    
    dbFunctions.close_db_session()
    sshFunctions.close_tunnel()

if __name__=="__main__":
    try:
        main()
    except Exception:
        scraperLogger(traceback.format_exc())
        sys.exit(1)
