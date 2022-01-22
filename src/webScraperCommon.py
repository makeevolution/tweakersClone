'''\n
Class with common functions for web scraper
'''

import getopt, sys, time, json
from bs4 import BeautifulSoup
from selenium import webdriver
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
import platform, importlib
from customExceptions import *
from interruptingcow import timeout
import subprocess

day = str(time.localtime().tm_mday)
month =  str(time.localtime().tm_mon)
year = str(time.localtime().tm_year)
hour = str(time.localtime().tm_hour) if len(str(time.localtime().tm_hour)) >= 2 else "0" + str(time.localtime().tm_hour)
minute = str(time.localtime().tm_min) if len(str(time.localtime().tm_min)) >= 2 else "0" + str(time.localtime().tm_min)

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
            local_bind_address=("127.0.0.1",3306),
            remote_bind_address=('aldosebastian.mysql.pythonanywhere-services.com', 3306)
        )
        # Start SSH tunneling
        print("Connecting to ssh.pythonanywhere.com database using SSH tunneling")
        print("Starting tunnel...")
        tunnel.start()
        print("Tunnel started")
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
        @classmethod
        def overridePrint(self):
            return '{} {} {} {} {}'.format(self.id, self.searchTerm, self.date, self.item, self.price)
        # Use locals since database variable is local for read_from_db only
        locals()[store] = type(store,(self.db.Model,),{
            "id" : self.db.Column(self.db.Integer, primary_key=True),
            "searchTerm": self.db.Column(self.db.String(100), unique=False),
            "date" : self.db.Column(self.db.String(100), unique=False),
            "item" : self.db.Column(self.db.String(100), unique=False),
            "price" :  self.db.Column(self.db.String(100), unique=False),
            "link" : self.db.Column(self.db.String(255), unique = False),
            "__repr__": overridePrint,
        })
        
        # More on sqlalchemy query API here: https://docs.sqlalchemy.org/en/13/orm/query.html
        session=self.db.session()
        sqlQuery = session.query(eval(store)).statement
        sessionEngine = eval(store).query.session.bind
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
        # Create class of each db dynamically
        @classmethod
        def overridePrint(self):
            return '{} {} {} {} {}'.format(self.id, self.searchTerm, self.date, self.item, self.price)
        # Use locals since database variable is local for write_to_db only
        locals()[store] = type(store,(self.Base,),{
            "__tablename__": store,
            "id" : Column(Integer, primary_key=True),
            "searchTerm": Column(String(255), unique=False),
            "date" : Column(String(100), unique=False),
            "item" : Column(String(255), unique=False),
            "price" :  Column(String(100), unique=False),
            "link" : Column(String(255), unique = False),
            "__repr__": overridePrint
        })
        for itemScraped, priceScraped, itemLink in itemPriceLink:
            current = eval(store)(date=dateScraped,searchTerm=searchterm,
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
        self.firefox_options.add_argument("--headless")

        maxDriverActivationAttempts = 5
        timeoutEachAttempt = 20
        for attempt in range(maxDriverActivationAttempts):
            try:
                print(f"Attempt {attempt + 1} of activating geckodriver")
                self.driver = webdriver.Firefox(executable_path=self.pwd + self.geckodriverExe, options=self.firefox_options)
                print("geckodriver successfully activated")
                break
            except RuntimeError:
                subprocess.run(['pkill', '-f', 'firefox'])
            if attempt == maxDriverActivationAttempts - 1:
                raise DriverException

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
            raise ErrorDuringScrapingException
        finally:
            self.driver.close()
            subprocess.run(['pkill', '-f', 'firefox'])

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