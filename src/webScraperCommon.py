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

day = str(time.localtime().tm_mday)
month =  str(time.localtime().tm_mon)
year = str(time.localtime().tm_year)
hour = str(time.localtime().tm_hour) if len(str(time.localtime().tm_hour)) >= 2 else "0" + str(time.localtime().tm_hour)
minute = str(time.localtime().tm_min) if len(str(time.localtime().tm_min)) >= 2 else "0" + str(time.localtime().tm_min)

class webScraperCommonFlaskSQLAlchemy():
    def __init__(self,db):
        # SSH to pythonanywhere to get access to database
        self.db = db
    
    # def write_to_db(self,db,store,searchterm,itemPriceDict):
    #     dateScraped = day + "/" + month + "/" + year + " " + hour + ":" + minute
    #     # Create class of each db dynamically
    #     @classmethod
    #     def overridePrint(self):
    #         return '{} {} {} {} {}'.format(self.id, self.searchTerm, self.date, self.item, self.price)
    #     # Use locals since database variable is local for write_to_db only
    #     locals()[store] = type(store,(db.Model,),{
    #         "id" : db.Column(db.Integer, primary_key=True),
    #         "searchTerm": db.Column(db.String(100), unique=False),
    #         "date" : db.Column(db.String(100), unique=False),
    #         "item" : db.Column(db.String(100), unique=False),
    #         "price" :  db.Column(db.String(100), unique=False),
    #         "__repr__": overridePrint
    #     })
    #     for itemScraped, priceScraped in zip(itemPriceDict.keys(),itemPriceDict.values()):
    #         current = eval(store)(date=dateScraped,searchTerm=searchterm,
    #                                  item=itemScraped,price=priceScraped)
    #         db.session.add(current)
    #     try:
    #         db.session.commit()
    #     except Exception:
    #         db.session.rollback()
            
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
    
    def available_online_stores(self):
        availableStores = inspect(self.db.engine).get_table_names()
        return availableStores
    
class webScraperCommonRawSQLAlchemy():
    def __init__(self,sqlalchemy_database_uri):
        # SSH to pythonanywhere to get access to database
        self.sqlalchemy_database_uri = sqlalchemy_database_uri
        self.Base = declarative_base()
        self.engine = create_engine(self.sqlalchemy_database_uri)
        self.Base.metadata.create_all(self.engine)
        Session = scoped_session(sessionmaker(self.engine))
        self.session = Session()

    def write_to_db(self,store,searchterm,itemPriceDict,itemPriceLink):
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
        # for itemScraped, priceScraped in zip(itemPriceDict.keys(),itemPriceDict.values()):
        #     current = eval(store)(date=dateScraped,searchTerm=searchterm,
        #                              item=itemScraped,price=priceScraped)
        #     self.session.add(current)
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
        print("fail here")
        session=self.db.session()
        sqlQuery = session.query(eval(store)).statement
        print("fail here2")
        sessionEngine = eval(store).query.session.bind
        data = pd.read_sql(sqlQuery, sessionEngine)
        print("reading complete!")
        return data
    
    def available_online_stores(self):
        availableStores = inspect(self.db.engine).get_table_names()
        return availableStores
    
class helperFunctions():
    def __init__(self):
        pass

    def scrapeWebsite(self,filename,extract_record):
        itemPriceDict = dict()
        itemPriceLink = []
        print(__file__)
        storeName = re.search(r"\w+(?=Scraper.py)",filename).group(0)
        pwd = os.path.dirname(__file__).replace(os.sep, '/')

        outputFile, searchTerm = self._process_inputs()
        searchTerm = searchTerm.upper()
        print(searchTerm)
        firefox_options = Options()
        firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path=pwd + r"/geckodriver.exe",options=firefox_options)

        for page in range(1,2):
            driver.get(self._get_url(page, searchTerm, storeName))
            soup = BeautifulSoup(driver.page_source)
            extract_record(searchTerm,soup,itemPriceDict,itemPriceLink,storeName)

        if "onServer" in os.environ:
            OnServer = True
        else:
            OnServer = False

        if not OnServer:
            tunnel = self.tunnelToDatabaseServer()
            sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@127.0.0.1:{}/aldosebastian$dateItemPrice'.format(tunnel.local_bind_port)
        else:
            print("Reading from database directly...")
            sqlalchemy_database_uri = 'mysql://aldosebastian:25803conan@aldosebastian.mysql.pythonanywhere-services.com/aldosebastian$dateItemPrice'
        dbFunctions = webScraperCommonRawSQLAlchemy(sqlalchemy_database_uri)
        result = dbFunctions.write_to_db(storeName,searchTerm,itemPriceDict,itemPriceLink)
        driver.close()
    
    def tunnelToDatabaseServer(self):
        tunnel = sshtunnel.SSHTunnelForwarder(
            ('ssh.pythonanywhere.com'),
            ssh_username='aldosebastian',
            ssh_password='25803conan',
            local_bind_address=("127.0.0.1",1000),
            remote_bind_address=('aldosebastian.mysql.pythonanywhere-services.com', 3306)
        )
        # Start SSH tunneling
        print("Reading from database using SSH tunneling")
        print("Starting tunnel...")
        tunnel.start()
        print("Tunnel started")
        return tunnel

    def _process_inputs(self):
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
            raise Exception("Website not scrapable yet :(")
        return url

    def to_json(self,outputFile,itemPriceDict):
        data = {}
        data['date'] = day + "/" + month + "/" + year + " " + hour + ":" + minute
        data['itemPrice'] = []
        for item, price in itemPriceDict.items():
            data['itemPrice'].append({item:price})
        if outputFile:
            with open(outputFile, "a+", encoding="UTF-8") as f:    
                json.dump(data, f)
                print("Data written to file {}".format(outputFile))
        else:
            for key, value in itemPriceDict.items():
                print(key, value)
        return json.dumps(data)
    

