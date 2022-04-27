import pytest
import sshtunnel
import sqlalchemy
import logging
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(os.path.join(ROOT, 'src'))
# from webScraperCommon import SSHTunnelOperations, DBOperationsRaw
# from customExceptions import *
from src.models import Store
# @pytest.fixture(scope="session")
# def tunnel_to_db():
#     try:
#         username = os.environ["tweakersCloneUsername"]
#         password = os.environ["tweakersClonePassword"]
#     except KeyError as e:
#         raise UnavailableCredentialsException(msg = traceback.format_exc())
    
#     sshFunctions = SSHTunnelOperations(username,password,"mysql","dateItemPrice")
#     sshFunctions.start_tunnel()
#     yield sshFunctions
#     sshFunctions.close_tunnel()

# # This fixture ensures there is only one database connection
# @pytest.fixture(scope="session")
# def db_session_factory(tunnel_to_db):
#     URIForDB = tunnel_to_db.getURI()
#     dbFunctionsFactory = DBOperationsRaw(URIForDB)
#     yield dbFunctionsFactory

# # This fixture gives a fresh db session for every test case
# @pytest.fixture(scope="function")
# def db_session(db_session_factory):
#     db_session_factory.start_db_session()
#     yield db_session_factory
#     db_session_factory.rollback_db_session()
#     db_session_factory.close_db_session()


