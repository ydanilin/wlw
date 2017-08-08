# -*- coding: utf-8 -*-
import sqlite3


class DBMS:
    def __init__(self, dbName):
        # Database connection
        self.conn = sqlite3.connect(dbName)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cur = self.conn.cursor()
        self.cur.row_factory = sqlite3.Row
        self.dumpCount = 0  # commit counter
        self.threshold = 50  # threshold when to commit
        self.sqlGetCategory = """SELECT * FROM job_state
                                 WHERE name_in_url = ?"""
        self.sqlAddCategory = """INSERT INTO job_state (name_in_url,
                                                        caption,
                                                        scraped,
                                                        total,
                                                        page_seen)
                                        VALUES (:n,
                                                :c,
                                                :s,
                                                :t,
                                                :p)"""
        self.sqlGetPageSeen = """SELECT page_seen FROM job_state
                                 WHERE name_in_url = ?"""

    def getCategory(self, nameInUrl):
        output = self.cur.execute(self.sqlGetCategory, (nameInUrl,)).fetchone()
        return output

    def addCategory(self, nameInUrl, category, total):
        datta = dict(n=nameInUrl, c=category, s=0, t=total, p='')
        self.conn.execute(self.sqlAddCategory, datta)
        self.conn.commit()

    def getPageSeen(self, nameInUrl):
        output = []
        stri = self.cur.execute(self.sqlGetPageSeen, (nameInUrl,)
                                ).fetchone()['page_seen']
        if stri:
            output = list(map(lambda x: int(x), stri.split(',')))
        return output
