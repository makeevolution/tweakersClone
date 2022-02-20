'''\nWeb Scraper (scrapes amazon.nl)
Usage: python amazonScraper.py [OPTIONS] [REQUIRED ARGUMENTS]
REQUIRED ARGUMENTS:
 Search term for amazon.com (e.g. Bose headphones)
RETURNS:
 A json string with date of scraping and a dict of all closest items to search term and their price 
OPTIONS:
 -h, --help           Print this help page
 -o, --output-file    Output also to a file, only possible to a json extension
EXAMPLE:
 python amazonScraper.py -o output.json Sony WF-1000XM4

'''

from customExceptions import *
import re, os

def extract_record(searchTerm,soup,itemPriceLink,storeName):
    searchResultList = soup.find_all('div',{'data-component-type': 's-search-result'})

    for searchResult in searchResultList:
        searchResultSpans = searchResult.findChildren("span")[1:]
        searchResultSpans = [*filter(lambda x : x.has_attr("class"), searchResultSpans)]
        for data in searchResultSpans:
            try:
                fullTitle = data.getText()
                # For each term in searchTerm, check if it exists in data.getText(). If they do, then we are good
                if len([*filter(lambda x: re.search(x, fullTitle, re.IGNORECASE),searchTerm.split(" "))]) == len(searchTerm.split(" ")):
                    fullPrice = [*filter(lambda x: (x.get("class",default = ["False"])[0] == 'a-price-whole'), searchResultSpans)][0].getText()
                    link = storeName + ".nl" + data.previous_element.attrs["href"]
                    itemPriceLink.append((fullTitle,fullPrice,link))
            except BaseException:
                continue

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