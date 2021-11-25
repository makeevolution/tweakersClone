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

import getopt, sys, time, json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webScraperCommon import webScraperCommon
import re

def extract_record(searchTerm,soup,itemPriceDict):
    divItemPrice = soup.find("ul",{"id":"js_items_content"}).findChildren("div",{"class":"product-item__content"})
    
    items = soup.find_all('div',{'class':'product-title--inline'})
    prices = soup.find_all('meta',{'itemprop':'price'})
    
    for item,price in zip(items,prices):
        fullTitle = item.a.text
        fullPrice = price["content"]
        if re.search(searchTerm, fullTitle, re.IGNORECASE):
            itemPriceDict.update(dict([(fullTitle,fullPrice)]))
        

def main():
    itemPriceDict = dict()
    outputFile, searchTerm = webScraperCommon.process_inputs()
    print(searchTerm)
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=r"geckodriver.exe",options=firefox_options)

    for page in range(1,2):
        driver.get(webScraperCommon.get_url(page, searchTerm, "bol"))
        soup = BeautifulSoup(driver.page_source)
        extract_record(searchTerm,soup,itemPriceDict)

    #result = webScraperCommon.to_json(outputFile, itemPriceDict)
    result = webScraperCommon.write_to_db("bol",searchTerm,itemPriceDict)

    driver.close()
    return result

if __name__=="__main__":
    main()