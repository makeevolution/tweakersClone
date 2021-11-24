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
from webScraperCommon import webScraperCommon

def extract_record(searchTerm,soup,itemPriceDict):
    divItemPrice = soup.find("ul",{"id":"js_items_content"}).findChildren("div",{"class":"product-item__content"})
    
    items = soup.find_all('div',{'class':'product-title--inline'})
    prices = soup.find_all('meta',{'itemprop':'price'})
    
    for item,price in zip(items,prices):
        fullTitle = item.a.text
        fullPrice = price["content"]
        if searchTerm in fullTitle:
            itemPriceDict.update(dict([(fullTitle,fullPrice)]))
    # items = soup.find_all(lambda x:(x.name=='a') & (x.has_attr("title")))
    # items = [i['title'] for i in items if searchTerm in i['title']]
    # prices = soup.find_all('strong',{'class':'sales-price__current'})
    
    # for item,price in zip(items,prices):
    #     fullTitle = item
    #     fullPrice = price.text
    #     if searchTerm in fullTitle:
    #         itemPriceDict.update(dict([(fullTitle,fullPrice)]))


def main():
    itemPriceDict = dict()
    outputFile, searchTerm = webScraperCommon.process_inputs()
    print(searchTerm)
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    driver = webdriver.Firefox(executable_path=r"geckodriver.exe",options=firefox_options)

    for page in range(1,2):
        driver.get(webScraperCommon.get_url(page, searchTerm))
        soup = BeautifulSoup(driver.page_source)
        extract_record(searchTerm,soup,itemPriceDict)

    #result = webScraperCommon.to_json(outputFile, itemPriceDict)
    result = webScraperCommon.write_to_db("coolblue",searchTerm,itemPriceDict)
    driver.close()

if __name__=="__main__":
    main()