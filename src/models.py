from sqlalchemy import inspect, create_engine, Column, String, Integer, exc
from sqlalchemy.ext.declarative import declarative_base

Store = type("Store",(declarative_base(),),{
        "__tablename__": " Store",
        "__table_args__": {'extend_existing': True},
        "id" : Column(Integer, primary_key=True),
        "searchTerm": Column(String(255), unique=False),
        "date" : Column(String(255), unique=False),
        "item" : Column(String(255), unique=False),
        "price" :  Column(String(255), unique=False),
        "link" : Column(String(255), unique = False)
    })