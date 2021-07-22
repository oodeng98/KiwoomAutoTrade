from datetime import datetime
import os
import sqlite3


db = object()
now = datetime.now()

DATABASE_PATH = os.path.join('.', 'data', now.strftime('%Y%m%d.db'))


class Database:
    def __init__(self):
        self.con: sqlite3.Connection = None # type: ignore

        self.get_db_connect()


    def get_db_connect(self):
        if not self.con:
            self.con = sqlite3.connect(DATABASE_PATH)
