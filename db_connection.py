import sqlite3
from sqlite3 import Error


class db_connect(object):

    def __init__(self, db_file):
        self._db_connection = sqlite3.connect(db_file)
        self._db_cur = self._db_connection.cursor()

    def connection(self):
        return self._db_connection

    def query(self, query, params):
        return self._db_cur.execute(query, params)

    def __del__(self):
        self._db_connection.close()
