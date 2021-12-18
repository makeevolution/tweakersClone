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
from webScraperCommon import webScraperCommonRawSQLAlchemy, helperFunctions
import re
import os

def extract_record(searchTerm,soup,itemPriceDict,itemPriceLink,storeName):
    divItemPrice = soup.find("ul",{"id":"js_items_content"}).findChildren("div",{"class":"product-item__content"})
    
    items = soup.find_all('div',{'class':'product-title--inline'})
    prices = soup.find_all('meta',{'itemprop':'price'})
    links = soup.find_all('a',{'class':'px_list_page_product_click'})
    for item,price,link in zip(items,prices,links):
        fullTitle = item.a.text
        fullPrice = price["content"]
        link = storeName + ".nl" + link["href"]
        if re.search(searchTerm, fullTitle, re.IGNORECASE):
            itemPriceDict.update(dict([(fullTitle,fullPrice)]))
            itemPriceLink.append((fullTitle,fullPrice,link))
        

def main():
    functions = helperFunctions()
    functions.scrapeWebsite(__file__,extract_record)

if __name__=="__main__":
    main()