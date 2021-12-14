#pytest -s .\testOne.py
import sys
sys.path.append(".././")

import pytest
import logging
from src.webScraperCommon import webScraperCommon

LOGGER = logging.getLogger(__name__)

itemPriceTest = dict()
fullTitle = ["fakeitem" + str(i) for i in range(0,9)]
fullPrice = [ i for i in range(0,9) ]
itemPriceTest.update(dict([("fakeitem"+str(i),i) for i in range(0,9)]))

def test_write_to_db_pass():
    functions = webScraperCommon()
    webScraperCommon.write_to_db("test", "sony xm", itemPriceTest)

def test_write_to_db_fail():
    #webScraperCommon.write_to_db("test", "sony xm", itemPriceTest)
    with pytest.raises(Exception) as e_info:
        webScraperCommon.write_to_db("test2", "sony xm", itemPriceTest)
    assert e_info.typename == "ProgrammingError"

