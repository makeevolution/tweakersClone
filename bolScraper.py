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

def extract_record(searchTerm,soup,itemPriceDict):
    divItemPrice = soup.find_all('div',['product-card__details'])
    
    for div in divItemPrice:
        try:
            fullTitle = [child.get("title") for child in div.findChildren("a") if child.has_attr("title")][0]
            fullPrice = [child.text for child in div.findChildren("strong") if child.get("class",default = ["False"])[0] == "sales-price__current"][0]
        except BaseException:
            continue    
        if searchTerm in fullTitle:
            itemPriceDict.update(dict([(fullTitle,fullPrice)]))

def main():
    itemPriceDict = dict()
    outputFile, searchTerm = webScraperCommon.process_inputs()
    print(searchTerm)
    firefox_options = Options()
    #firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=r"geckodriver.exe",options=firefox_options)

    for page in range(1,2):
        driver.get(webScraperCommon.get_url(page, searchTerm))
        soup = BeautifulSoup(driver.page_source)
        extract_record(searchTerm,soup,itemPriceDict)

    #result = webScraperCommon.to_json(outputFile, itemPriceDict)
    result = webScraperCommon.write_to_db("bol",itemPriceDict)

    driver.close()
    return result

if __name__=="__main__":
    main()