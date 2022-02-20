'''\nWeb Scraper (scrapes coolblue.com)
Usage: python coolblueScraper.py [OPTIONS] [REQUIRED ARGUMENTS]
REQUIRED ARGUMENTS:
 Search term for coolblue.com (e.g. Bose headphones)
RETURNS:
 A json string with date of scraping and a dict of all closest items to search term and their price 
OPTIONS:
 -h, --help           Print this help page
 -o, --output-file    Output also to a file, only possible to a json extension
EXAMPLE:
 python coolblueScraper.py -o output.json Sony WF-1000XM4

'''

from customExceptions import *
import re, os

def extract_record(searchTerm,soup,itemPriceLink,storeName):
    divItemPrice = soup.find_all('div',['product-card__details'])

    for div in divItemPrice:
        try:
            fullTitle = [child.get("title") for child in div.findChildren("a") if child.has_attr("title")][0]
            fullPrice = [child.text for child in div.findChildren("strong") \
                        if child.get("class",default = ["False"])[0] == "sales-price__current"][0]
            link = [storeName + ".nl" +child.get("href") 
                    for child in div.findChildren("a") 
                    if child.has_attr("href")][0]
            if re.search(searchTerm, fullTitle, re.IGNORECASE):
                itemPriceLink.append((fullTitle,fullPrice,link))
        except Exception:
            raise("Exception in extract_record function; website may have changed their structure :(")

def main():
    from webScraperCommon import Scrape, SSHTunnelOperations, interrogateStoreRaw
    from inputProcessor import getSearchTermFromInput
    import importlib

    try:
        storeName = re.search(r"\w+(?=Scraper.py)",__file__).group(0)
    except AttributeError:
        raise InvalidFilenameException
    searchTerm = getSearchTermFromInput()
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

    storeModule = importlib.import_module(storeName+"Scraper", package="")
    extractor_function = storeModule.extract_record

    print(f"Scraping {searchTerm} for store {storeName}")
    scrapeFunction = Scrape(storeName,searchTerm,extractor_function)
    scrapingResult = scrapeFunction.scrapeStore()
    print(f"Writing data of item {searchTerm} to {storeName}")
    dbFunctions.write_to_db(storeName,searchTerm,scrapingResult)
    print(f"Done writing")

    dbFunctions.close_db_session()
    sshFunctions.close_tunnel()
    
if __name__=="__main__":
    main()