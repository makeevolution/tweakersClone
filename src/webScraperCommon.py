'''\n
Class with common functions for web scraper
'''

import getopt, sys, time, json, traceback
from logging import exception
from bs4 import BeautifulSoup
from selenium import webdriver,common
from selenium.webdriver.firefox.options import Options
from sqlalchemy import inspect, create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
import sshtunnel
from flask import request, Flask
import pandas as pd
import re, os
from abc import ABC, abstractmethod
import platform

from urllib3 import Timeout
from customExceptions import *
from interruptingcow import timeout
import subprocess

day = str(time.localtime().tm_mday)
month =  str(time.localtime().tm_mon)
year = str(time.localtime().tm_year)
hour = str(time.localtime().tm_hour) if len(str(time.localtime().tm_hour)) >= 2 else "0" + str(time.localtime().tm_hour)
minute = str(time.localtime().tm_min) if len(str(time.localtime().tm_min)) >= 2 else "0" + str(time.localtime().tm_min)
TIMEOUT = 8
MAXATTEMPT = 3

class SSHTunnelOperations:
    def __init__(self,username,password,dialect,schema):
        self.username = username
        self.password = password
        self.dialect = dialect
        self.schema = schema

    def getURI(self):
        # if not self.OnServer:
        print(f"Obtaining URI to be able to write and read from database...")
        sqlalchemy_database_uri = f'{self.dialect}://{self.username}:{self.password}@127.0.0.1:\
                                    {self._tunnelToDatabaseServer().local_bind_port}/{self.username}${self.schema}'
        # else:
        #     print("We are on the database server, reading directly")
        #     sqlalchemy_database_uri = f'{self.dialect}://{self.username}:{self.password}@{self.username}.{self.dialect}.pythonanywhere-services.com\
        #                                 /{self.username}${self.schema}'
        return sqlalchemy_database_uri

    def _tunnelToDatabaseServer(self):
        tunnel = sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username=self.username,
            ssh_password=self.password,
            local_bind_address=("127.0.0.1",),
            remote_bind_address=('aldosebastian.mysql.pythonanywhere-services.com', 3306)
        )
        # Start SSH tunneling
        print("Connecting to ssh.pythonanywhere.com database using SSH tunneling")
        print("Starting tunnel...")
        for i in range(MAXATTEMPT):
            try:
                with timeout(TIMEOUT,exception=RuntimeError):
                    #time.sleep(14)
                    tunnel.start()
                    print("Tunnel started")
                break
            except AttributeError:
                # timeout module doesn't work since here we're on Windows
                print("no re-attempts if this attempt fails...")
                tunnel.start()
                break
            except (RuntimeError, 
                    sshtunnel.BaseSSHTunnelForwarderError,
                    sshtunnel.HandlerSSHTunnelForwarderError):
                scraperLogger(level = "ERROR", msg = f"SSH tunneling attempt {i} FAILED \n" \
                                                     + traceback.format_exc())
                exceptionMsg = traceback.format_exc()
            if i == MAXATTEMPT:
                raise TunnelingTimeoutException(msg = exceptionMsg)
        return tunnel

class DBoperations(ABC):
    @abstractmethod
    def read_from_db(self,store):
        pass
    @abstractmethod
    def write_to_db(self,store,searchterm,itemPriceLink):
        pass

class DBOperationsFlask(DBoperations):
    def __init__(self,db):
        # SSH to pythonanywhere to get access to database
        self.db = db
            
    def read_from_db(self,store):
        store = "".join(store)
        print("reading data from " + store + "...")
        # Create class of each db dynamically
        self.db.metadata.clear()
        storeTableAsObject=table_struct_to_object(store,self.Base)
        
        # More on sqlalchemy query API here: https://docs.sqlalchemy.org/en/13/orm/query.html
        session=self.db.session()
        sqlQuery = session.query(eval(storeTableAsObject)).statement
        sessionEngine = eval(storeTableAsObject).query.session.bind
        data = pd.read_sql(sqlQuery, sessionEngine)
        print("reading complete!")
        return data

    def write_to_db():
        # Don't forget to make this otherwise we break Interface Segregation principle
        pass

class interrogateStoreFlask(DBOperationsFlask):
    def available_online_stores(self):
        availableStores = inspect(self.db.engine).get_table_names()
        return availableStores
    
class DBOperationsRaw(DBoperations):
    def __init__(self,username,password,dialect,schema):
        self.sqlalchemy_database_uri = SSHTunnelOperations(username,password,dialect,schema).getURI()
        self.Base = declarative_base()
        self.engine = create_engine(self.sqlalchemy_database_uri)
        self.Base.metadata.create_all(self.engine)
        Session = scoped_session(sessionmaker(self.engine))
        self.session = Session()
    
    def read_from_db():
        # Don't forget to make this otherwise we break Interface Segregation principle
        pass

    def write_to_db(self,store,searchterm,itemPriceLink):
        dateScraped = day + "/" + month + "/" + year + " " + hour + ":" + minute
        
        storeTableAsObject=table_struct_to_object(store,self.Base)
        
        for itemScraped, priceScraped, itemLink in itemPriceLink:
            current = eval(storeTableAsObject)(date=dateScraped,searchTerm=searchterm,
                                     item=itemScraped,price=priceScraped,link=itemLink)
            self.session.add(current)
        try:
            print("write successful")
            self.session.commit()
        except Exception:
            print("write failed")
            self.session.rollback()
        finally:
            self.session.close()
    
class interrogateStoreRaw(DBOperationsRaw):
    def available_online_stores(self):
        # use the Session() object in __init__ to check what
        # stores are available in the schema

        # Use this to check if the store requested exists in the db
        pass
    def searched_items_in_store(self,storeName):
        storeTableAsObject=table_struct_to_object(storeName,self.Base)
        searchTerms = self.session.query(storeTableAsObject.searchTerm).distinct()
        searchTerms = list([*searchTerms][0])
        # Remove empty search terms
        searchTerms = [*filter(None,searchTerms)]
        # Return only unique search terms
        searchTerms = set([term.lower() for term in searchTerms])
        return searchTerms
def table_struct_to_object(store,declarative_base):
    # Use locals since database variable is local for write_to_db only
    locals()[store] = type(store,(declarative_base,),{
        "__tablename__": store,
        "id" : Column(Integer, primary_key=True),
        "searchTerm": Column(String(255), unique=False),
        "date" : Column(String(100), unique=False),
        "item" : Column(String(255), unique=False),
        "price" :  Column(String(100), unique=False),
        "link" : Column(String(255), unique = False)
    })
    return locals()[store]

class Scrape():
    def __init__(self,storeName,searchTerm,extract_record):
        self.extract_record = extract_record
        self.storeName = storeName
        self.searchTerm = searchTerm

        self.OnServer = True if "OnServer" in os.environ else False
        self.geckodriverExe = r"/geckodriver" if platform.system() == 'Linux' else r"/geckodriver.exe"
        self.itemPriceLink = []

        try:
            getattr(sys.modules[__name__], self.storeName + "URL")
        except AttributeError:
            raise StoreNotSupportedException

        self.pwd = os.path.dirname(__file__).replace(os.sep, '/')

        self.searchTerm = self.searchTerm.upper()

        self.firefox_options = Options()
        #self.firefox_options.add_argument("--headless")

        for attempt in range(MAXATTEMPT):
            try:
                with timeout(TIMEOUT,exception=RuntimeError):
                    scraperLogger(msg = f"Attempt {attempt + 1} of activating geckodriver")
                    self.driver = webdriver.Firefox(executable_path=self.pwd + self.geckodriverExe, options=self.firefox_options)
                    scraperLogger(msg = "geckodriver successfully activated")
                    break
            except AttributeError:
                # timeout module doesn't work since here we're on Windows
                scraperLogger(msg = f"Attempt {attempt + 1} of activating geckodriver")
                print("no re-attempts if this attempt fails...")
                self.driver = webdriver.Firefox(executable_path=self.pwd + self.geckodriverExe, options=self.firefox_options)
                scraperLogger(msg = "geckodriver successfully activated")
                break
            except (common.exceptions.WebDriverException, RuntimeError):
                subprocess.run(['pkill', '-f', 'firefox'])
                scraperLogger(level = "ERROR", msg = f"Geckodriver activation attempt {attempt + 1} FAILED \n" \
                                                     + traceback.format_exc())
                exceptionMsg = traceback.format_exc()
            if attempt == MAXATTEMPT - 1:
                raise DriverException(msg = exceptionMsg)
     
    # Scrapes store and updates self.itemPriceLink
    def scrapeStore(self):
        try:
            print("Scraping...")
            for page in range(1,2):
                self.driver.get(self._get_url(page))
                self.soup = BeautifulSoup(self.driver.page_source)
                self.extract_record(self.searchTerm,self.soup,self.itemPriceLink,self.storeName)
            return self.itemPriceLink
        except Exception:
            raise ErrorDuringScrapingException(msg = traceback.format_exc())
        finally:
            self.driver.close()
            subprocess.run(['pkill', '-f', 'firefox']) if platform.system() == "Linux" else None

    def _get_url(self, page):
        searchTermForURL=self.searchTerm.replace(" ","+")
        url = getattr(sys.modules[__name__], self.storeName + "URL")().URL_by_page_and_item(searchTermForURL,page)
        return url
        
class storeURL(ABC):
    @abstractmethod
    def URL_by_page_and_item(self,searchTerm,page):
        pass
class bolURL(storeURL):
    def URL_by_page_and_item(self,searchTerm,page):
        return "https://www.bol.com/nl/nl/s/?page={}&searchtext={}&view=list".format(page,searchTerm)
class coolblueURL(storeURL):
    def URL_by_page_and_item(self,searchTerm,page):
        return "https://www.coolblue.nl/zoeken?query={}&page={}".format(searchTerm,page)
class amazonURL(storeURL):
    def URL_by_page_and_item(self,searchTerm,page):
        return "https://www.amazon.nl/s?k={}&page={}".format(searchTerm,page)

if __name__=="__main__":
    def fake():
        pass
    test = Scrape("coolblueScraper.py",fake)
