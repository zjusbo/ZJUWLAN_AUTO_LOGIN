# -*- coding:utf-8 -*-
#
# AUTO_LOGIN_ZJUWLAN and AUTO_START_HOTSPOT
#
#author: Sunny Song, ZJU
#email: sbo@zju.edu.cn

#TODO
#Add encryption algorithm to store username and password at localhost --- DONE
#Fix the bug, which would get random-like MAC address - DONE 
#Modularization.

import sqlite3

class DB:
	def __init__(self, db_name):
		self.conn = sqlite3.connect(db_name)
		self.cu = self.conn.cursor()
	def init(self, sql):
		pass

	@with_connection
	def select(self, sqlstr):
		self.cu.execute(sqlstr, args)
		
	def insert(self, **kw):
		pass
	def update(self, **kw):
		pass
	def delete(self, **kw):
		pass
	def drop(self, **kw):

	def close(self):
		self.conn.close()



def deleteDB(db_name):
	if os.path.isfile(db_name):
		os.remove(db_name)
	else:
		cPrint('[ERROR] DB does not exist.', COLOR.RED)

def connectToDB(db_name):
	conn = sqlite3.connect(db_name)
	cu = conn.cursor()
	sqlScript = '''CREATE TABLE IF NOT EXISTS user
			(
			userID INTEGER PRIMARY KEY AUTOINCREMENT,
			userStudentID BLOB NOT NULL UNIQUE ON CONFLICT IGNORE,
			userPassword BLOB NOT NULL
			);
		'''
	try:
		cu.execute(sqlScript)
		conn.commit()
	except sqlite3.DatabaseError,e:
		#DB is damaged. Delete the file and create it again.
		cPrint("[WARNING] Database is weird. Retrieving...", COLOR.DARKRED)
		cu.close()
		conn.close()
		deleteDB(db_name)
		
		conn = sqlite3.connect(db_name)
		cu=conn.cursor()
		cu.execute(sqlScript)
		conn.commit()
		cPrint("[INFO] Database is retrieved.", COLOR.SILVER)
	return (conn,cu)

def cleanDB(conn,cu):
	query = '''DELETE FROM user'''
	cu.execute(query)
	conn.commit()
