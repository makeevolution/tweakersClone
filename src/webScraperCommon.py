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
    def getURI(self):
        if not self.OnServer:
            print("Reading from remote database...")
            sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@127.0.0.1:{}/aldosebastian$dateItemPrice'\
                                        .format(self._tunnelToDatabaseServer().local_bind_port)
        else:
            print("We are on the database server, reading directly")
            sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@aldosebastian.mysql.pythonanywhere-services.com\
                                        /aldosebastian$dateItemPrice'
        return sqlalchemy_database_uri

    def _tunnelToDatabaseServer(self):
        tunnel = sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='aldosebastian',
            ssh_password='25803conan',
            local_bind_address=("127.0.0.1",3306),
            remote_bind_address=('aldosebastian.mysql.pythonanywhere-services.com', 3306)
        )
        # Start SSH tunneling
        print("Connecting to database server using SSH tunneling")
        print("Starting tunnel...")
        tunnel.start()
        print("Tunnel started")
        return tunnel

class DBoperations(ABC):
    @abstractmethod
    def read_from_db(self,store):
        pass
    @abstractmethod
    def write_to_db(self,store,searchterm,itemPriceDict,itemLink):
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
        pass

class interrogateStoreFlask(DBOperationsFlask):
    def available_online_stores(self):
        availableStores = inspect(self.db.engine).get_table_names()
        return availableStores
    
class DBOperationsRaw(DBoperations):
    def __init__(self,sqlalchemy_database_uri):
        self.sqlalchemy_database_uri = SSHTunnelOperations.getURI()
        self.Base = declarative_base()
        self.engine = create_engine(self.sqlalchemy_database_uri)
        self.Base.metadata.create_all(self.engine)
        Session = scoped_session(sessionmaker(self.engine))
        self.session = Session()
    
    def read_from_db():
        pass

    def write_to_db(self,store,searchterm,itemPriceDict,itemLink):
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
        for itemScraped, priceScraped, itemLink in itemLink:
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
    def __init__(self,filename,extract_record):
        if "OnServer" in os.environ:
            self.OnServer = True
            geckodriverExe = r"/geckodriver"
        else:
            self.OnServer = False
            geckodriverExe = r"/geckodriver.exe"
        self.itemPriceDict = dict()
        self.itemLink = []
        try:
            self.storeName = re.search(r"\w+(?=Scraper.py)",filename).group(0)
        except AttributeError:
            raise InvalidFilenameException
        self.pwd = os.path.dirname(__file__).replace(os.sep, '/')

        self.outputFile, self.searchTerm = self._process_args()
        self.searchTerm = self.searchTerm.upper()
        print(f'Scraping {self.storeName} for {self.searchTerm}')

        self.firefox_options = Options()
        self.firefox_options.add_argument("--headless")

        maxDriverActivationAttempts = 5
        timeoutEachAttempt = 10
        for attempt in range(maxDriverActivationAttempts):
            try:
                with timeout(timeoutEachAttempt,exception=RuntimeError):
                    print(f"Attempt {attempt} of activating geckodriver")
                    self.driver = webdriver.Firefox(executable_path=self.pwd + geckodriverExe,options=self.firefox_options)
                    break
            except RuntimeError:
                subprocess.run(['pkill', '-f', 'firefox'])
            if attempt == maxDriverActivationAttempts - 1:
                raise DriverException
        
    # Scrapes and updates self.itemPricedict and self.itemLink

    def scrapeStore(self):
        try:
            getattr(sys.modules[__name__],bol + "URL")
        except AttributeError:
            raise Exception("store not yet supported")
        for page in range(1,2):
            self.driver.get(self._get_url(page, self.searchTerm, self.storeName))
            self.soup = BeautifulSoup(self.driver.page_source)
            self.driver.close()
            extract_record(self.searchTerm,self.soup,self.itemPriceDict,self.itemLink,self.storeName)
        return self.itemPriceDict, self.itemLink

    def _process_args(self):
        try:
            argv = sys.argv[1:]
        except IndexError:
            sys.exit("Use -h for more help")

        try:
            opts, searchTerm = getopt.getopt(argv, "ho:", ["help", "output-file="])
        except getopt.GetoptError as err:
            print(err)
            sys.exit(2)
        
        if not searchTerm:
            if "-h" not in str(opts) or "-help" not in str(opts):
                print("Error: At least one search term must be included!")
                sys.exit(__doc__)

        searchTerm = " ".join(searchTerm)
        outputFile = []
        for opt, arg in opts:
            if opt in ["-h","--help"]:
                sys.exit(__doc__)
            elif opt in ["-o","--output-file"]:
                if ".json" in arg:
                    outputFile = arg.strip()
                else:
                    print("Error: Write to specified file type is not possible!")
                    sys.exit(__doc__)
            else:
                print("Error: option {} not available".format(opt))
                sys.exit(__doc__)

        return outputFile, searchTerm

    def _get_url(self, page, searchTerm, website):
        searchTerm=searchTerm.replace(" ","+")
        if website == "bol":
            url = "https://www.bol.com/nl/nl/s/?page={}&searchtext={}&view=list".format(page,searchTerm)
        elif website == "amazon":
            url = "https://www.amazon.nl/s?k={}&page={}".format(searchTerm,page)
        elif website == "coolblue":
            url = "https://www.coolblue.nl/zoeken?query={}&page={}".format(searchTerm,page)
        else:
            raise Exception("Store not scrapable yet :(")
        return url
        
class storeURL(ABC):
    @abstractmethod
    def URL_by_page_and_item(self,page,searchTerm):
        pass
class bolURL(storeURL):
    def URL_by_page_and_item():
        return "https://www.bol.com/nl/nl/s/?page={}&searchtext={}&view=list".format(page,searchTerm)
class coolblueURL(storeURL):
    def URL_by_page_and_item():
        return "https://www.coolblue.nl/zoeken?query={}&page={}".format(searchTerm,page)
class amazonURL(storeURL):
    def URL_by_page_and_item():
        return "https://www.amazon.nl/s?k={}&page={}".format(searchTerm,page)

if __name__=="__main__":
    def fake():
        pass
    test = Scrape("coolblueScraper.py",fake)