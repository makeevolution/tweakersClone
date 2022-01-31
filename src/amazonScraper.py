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

from webScraperCommon import Scrape, DBOperationsRaw
from inputProcessor import getSearchTermFromInput
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
                    fullPrice = [*filter(lambda x: (x.get("class",default = ["False"])[0] == 'a-price-whole'), searchResultSpans)][0]
                    itemPriceLink.append((fullTitle,fullPrice,link))
            except BaseException:
                continue

def main():
    try:
        storeName = re.search(r"\w+(?=Scraper.py)",__file__).group(0)
    except AttributeError:
        raise InvalidFilenameException
    searchTerm = getSearchTermFromInput()
    
    print(f"Scraping {storeName} for {searchTerm}")
    
    try:
        username = os.environ["tweakersCloneUsername"]
        password = os.environ["tweakersClonePassword"]
    except KeyError as e:
        raise UnavailableCredentialsException(msg = traceback.format_exc())

    scrapeFunction = Scrape(storeName,searchTerm,extract_record)
    scrapingResult = scrapeFunction.scrapeStore()
    try:
        assert scrapingResult != []
    except AssertionError:
        raise EmptyResultException(storeName)
    DBfunction = DBOperationsRaw(username,password,dialect="mysql",schema="dateItemPrice")
    DBfunction.write_to_db(storeName,searchTerm,scrapingResult)

if __name__=="__main__":
    main()