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

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webScraperCommon import webScraperCommonRawSQLAlchemy, helperFunctions
import re
import os

def extract_record(searchTerm,soup,itemPriceDict,itemPriceLink,storeName):
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
                itemPriceDict.update(dict([(fullTitle,fullPrice)]))
                itemPriceLink.append((fullTitle,fullPrice,link))
        except BaseException:
            raise("Exception in extract_record function; website may have changed their structure :(")
    
    # items = soup.find_all(lambda x:(x.name=='a') & (x.has_attr("title")))
    # items = [i['title'] for i in items if searchTerm in i['title']]
    # prices = soup.find_all('strong',{'class':'sales-price__current'})
    
    # for item,price in zip(items,prices):
    #     fullTitle = item
    #     fullPrice = price.text
    #     if searchTerm in fullTitle:
    #         itemPriceDict.update(dict([(fullTitle,fullPrice)]))


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
    # import sys, os
    # print(sys.argv[0])
    # print(__file__)
    # print(re.search(r"(?<=\\)\w+(?=Scraper\.py)",__file__).group(0))
    # print(os.path.dirname(__file__).replace(os.sep, '/'))
    main()