import pytest, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(os.path.join(ROOT, 'src'))
from webScraperCommon import SSHTunnelOperations, DBOperationsRaw, table_struct_to_object
from customExceptions import *

def test_add_new_table(db_session):
    # make a new table in form of object
    test_table = table_struct_to_object("test2",db_session.Base)
    test_table.create(db_session.engine)
    # make an instance of the test table object
    test_table_instance = test_table(date="test",searchTerm="test",item="test",price="test",link="test")
    # write the test table to db
    db_session.session.add(test_table_instance)
    db_session.session.commit()
    # check if test table is there in database
    try:
        db_session.session.query(test_table)
    except Exception:
        pytest.fail("test2 table is not in the database!")
    test_table.drop(db_session.engine)
    # Test if you can add a new table, and delete that table after
    # Check that all columns have a value
    
    # Test if you can add a new row to existing table

    