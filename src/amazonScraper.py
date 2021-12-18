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

import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webScraperCommon import webScraperCommonRawSQLAlchemy, helperFunctions
import os
def extract_record(searchTerm,soup,itemPriceDict,itemPriceLink,storeName):
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
                    itemPriceDict.update(dict([(fullTitle,fullPrice.getText())]))
            except BaseException:
                continue


def main():
    functions = helperFunctions()
    itemPriceDict = dict()
    itemPriceLink = []
    print(__file__)
    storeName = re.search(r"\w+(?=Scraper.py)",__file__).group(0)
    pwd = os.path.dirname(__file__).replace(os.sep, '/')

    outputFile, searchTerm = functions.process_inputs()
    searchTerm = searchTerm.upper()
    print(searchTerm)
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=pwd + r"/geckodriver.exe",options=firefox_options)

    for page in range(1,2):
        driver.get(functions.get_url(page, searchTerm, storeName))
        soup = BeautifulSoup(driver.page_source)
        extract_record(searchTerm,soup,itemPriceDict,itemPriceLink,storeName)

    OnServer = False
    #result = functions.to_json(outputFile, itemPriceDict)
    if not OnServer:
        tunnel = functions.tunnelToDatabaseServer()
        sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@127.0.0.1:{}/aldosebastian$dateItemPrice'.format(tunnel.local_bind_port)
    else:
        sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@aldosebastian.mysql.pythonanywhere-services.com/aldosebastian$dateItemPrice'
    dbFunctions = webScraperCommonRawSQLAlchemy(sqlalchemy_database_uri)
    result = dbFunctions.write_to_db(storeName,searchTerm,itemPriceDict,itemPriceLink)
    driver.close()


if __name__=="__main__":
    main()