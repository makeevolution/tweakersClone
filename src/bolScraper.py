'''\nWeb Scraper (scrapes bol.com)
Usage: python bolScraper.py [OPTIONS] [REQUIRED ARGUMENTS]
REQUIRED ARGUMENTS:
 Search term for bol.com (e.g. Bose headphones)
RETURNS:
 A json string with date of scraping and a dict of all closest items to search term and their price 
OPTIONS:
 -h, --help           Print this help page
 -o, --output-file    Output also to a file, only possible to a json extension
EXAMPLE:
 python bolScraper.py -o output.json Sony WF-1000XM4

'''


from customExceptions import *
import re, os

def extract_record(searchTerm,soup,itemPriceLink,storeName):
    
    items = soup.find_all('div',{'class':'product-title--inline'})
    prices = soup.find_all('meta',{'itemprop':'price'})
    links = soup.find_all('a',{'class':'px_list_page_product_click'})
    for item,price,link in zip(items,prices,links):
        fullTitle = item.a.text
        fullPrice = price["content"]
        link = storeName + ".com" + link["href"]
        if re.search(searchTerm, fullTitle, re.IGNORECASE):
            itemPriceLink.append((fullTitle,fullPrice,link))    

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