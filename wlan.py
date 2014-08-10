# -*- coding:utf-8 -*-
#author: Sunny Song, ZJU
#email: sbo@zju.edu.cn

#TODO
#Add encryption algorithm to store username and password at localhost DONE
#Test program

#Import exit to exit program when necessary
import sys

#Import os module to do some IO work
import os

#Import universally unique indentifiers to generate encryption key
import uuid

#Import urlencode() in this package to encode post data
import urllib

#Import http relevant functions 
from urllib2 import Request, urlopen, URLError, HTTPError

#Import sleep() to control pace of the program
from time import sleep

#Import Popen() to make cmd command available in this program
import subprocess

#Import encryption functions, it is used to encrypt private data 
import pyDes

#Import database related functions
import sqlite3

#Import getpass word input method. (password will not be shown)
from getpass import getpass
#Replace yourusername and yourpassword with your username and password

#Configuration area
author_email = 'sbo@zju.edu.cn'

db_name = 'pywin27.dll'

testWebsite = 'http://www.baidu.com'
wlanName = 'ZJUWLAN'
maxRetryTimesForPassword = 3
maxRetryTimesForServer = 3
#Configuration area end.

#Global status area
exit = False
debug = False
refreshNetwork = False
passwordIncorrectTimes = 0
serverFailureTimes = 0
isConnected = False
#Global status area end.

class COLOR:
	BLACK = 0
	BLUE = 1
	DARKGREEN = 2
	DARKCYAN = 3
	DARKRED = 4
	DARKPINK = 5
	BROWN = 6
	SILVER = 7
	GRAY = 8
	BLUE = 9
	GREEN = 10
	CYAN = 11
	RED = 12
	PINK = 13
	YELLOW = 14
	WHITE = 15

class KeyExpireError(Exception):
	def __init__(self):
		Exception.__init__(self)


def cPrint(msg, color = COLOR.SILVER):
	'''Print coloforul message in console.
	msg -- message you want to print
	color -- color you want to use. There are 16 colors available by default. More details are available in class COLOR.
	'''
	import ctypes
	ctypes.windll.Kernel32.GetStdHandle.restype = ctypes.c_ulong
	h = ctypes.windll.Kernel32.GetStdHandle(ctypes.c_ulong(0xfffffff5))
	if isinstance(color, int) == False or color < 0 or color > 15:
		color = COLOR.SILVER #
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, color)
	print msg
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, COLOR.SILVER)

def isConnectedToInternet(url):
	'''Check if the host is already connected to the Internet.
	Parameter:
		url -- URL of test website
	Return value:
		True -- the host can connect to the test URL.
		False -- the host can not connect to the test URL.
			In this scenario, error message shall be printed on the console. 
	'''
	req = Request(url)
	try:
		response = urlopen(req, timeout = 10)
		code = response.getcode()
		content = response.read()
	except URLError, e:
		if hasattr(e, 'reason'):
			info = '[ERROR] Failed to reach the server.\nReason: ' + str(e.reason)

		elif hasattr(e, 'code'):
			info = '[ERROR] The server couldn\'t fullfill the request.\nError code: ' +str(e.code)
		else:

			info = '[ERROR] Unknown URLError'
		if debug == True:
			cPrint(info, COLOR.RED)
		return False
	except Exception:
		import traceback
		if debug == True:
			print "Generic exception: " + traceback.format_exc()
		return False
	else:
		if code == 200 and 'net.zju.edu.cn/srun_port1.php' not in content:
			return True
		else:
			return False

def isSpecifiedWlanAvailable(name):
	'''Check if specified wlan is available to the host.
	Parameter:
		name -- wlan name
	Return value:
		True -- Specified wlan is available.
		False -- Specified wlan is not available
	'''
	p = subprocess.Popen(
		'netsh wlan show networks',
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()
	if name in stdout:
		return True
	else:
		return False

def isConnectedToSpecifiedWlan(name):
	'''return true if host is connected to specified wlan , otherwise return false. '''
	p = subprocess.Popen(
		'netsh wlan show interfaces' ,
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()
	if name in stdout:
		return True
	else:
		return False

def connectTo(name):
	'''connect to specified wlan. '''
	p = subprocess.Popen(
		'netsh wlan connect {0}' .format(name),
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()
	#Since encoding rule varies in different areas. Length of msg is used to check whether the connection is successful or not.
	if len(stdout) == 22 or 'Connection request was completed successfully' in stdout:
		return True
	else:
		return False 

def login(username, password):
	'''login wlan using given username and password. '''
	global passwordIncorrectTimes
	global isConnected
	global exit
	data = {'action':'login','username':username,'password':password,'ac_id':'3','type':'1','wbaredirect':'http://net.zju.edu.cn',
	'mac':'undefined','user_ip':'','is_ldap':'1','local_auth':'1'}
	data = urllib.urlencode(data)
	try:
		req = Request("https://net.zju.edu.cn/cgi-bin/srun_portal")
		response = urlopen(req,data, timeout = 10)	
		content = response.read()
		if 'help.html' in content:
			passwordIncorrectTimes = 0
			isConnected = True
			return True
		else:
			if len(content) == 27:#wrong password
				if passwordIncorrectTimes == 3:
					exit = True
				else:
					cPrint("[WARNING] Username or password is incorrect. Please check them again.",CLOLR.DARKRED)
					cPrint("[INFO] Retry for {0} more times." .format(maxRetryTimesForPassword - passwordIncorrectTimes))
					passwordIncorrectTimes += 1	
			else:
				cPrint("[UNKNOWN ERROR] " + content,COLOR.RED)
			return False

	except URLError, e:
		if hasattr(e, 'reason'):
			info = '[ERROR] Failed to reach the server.\nReason: ' + str(e.reason)
		elif hasattr(e, 'code'):
			info = '[ERROR] The server couldn\'t fullfill the request.\nError code: ' +str(e.code)
		else:
			info = '[ERROR] Unknown URLError'
		cPrint(info, COLOR.RED)
		return False

	except Exception:
		import traceback
		print "Generic exception: " + traceback.format_exc()
		return False

def logout(username, password):
	'''logout using given username and password.
	since in ZJU, one account only supports one host online concurrently, so previous hosts should be kicked off before a new host logs in.  
	'''
	global exit
	global passwordIncorrectTimes, serverFailureTimes
	global refreshNetwork
	data = {'action':'auto_dm','username':username,'password':password}
	data = urllib.urlencode(data)
	try:
		req = Request("https://net.zju.edu.cn/rad_online.php")

		response = urlopen(req, data, timeout = 10)
		content = response.read()
		if content == 'ok':
			serverFailureTimes = 0
			passwordIncorrectTimes = 0
			return True
		else:
			if len(content) == 8:#Wrong password
				if passwordIncorrectTimes == maxRetryTimesForPassword:
					exit = True
				else:
					cPrint("[WARNING] Username or password is incorrect. Please check them again.", COLOR.DARKRED)
					cPrint("[INFO] Retry for {0} more times." .format(maxRetryTimesForPassword - passwordIncorrectTimes))
					passwordIncorrectTimes += 1
			else:
				cPrint('[UNKNOWN ERROR]' + content,COLOR.RED) #another unknown error reason
			return False 

	except URLError, e:
		if hasattr(e, 'reason'):
			# '[Error] Failed to reach the server.\nReason: ' + str(e.reason)
			info = '[WARNING] Failed to reach the server. Retry for {0} more times.' .format(maxRetryTimesForServer - serverFailureTimes)
			serverFailureTimes += 1
			if serverFailureTimes == maxRetryTimesForServer:
				refreshNetwork = True
			cPrint(info,COLOR.DARKRED)
		elif hasattr(e, 'code'):
			info = '[ERROR] The server couldn\'t fullfill the request.\nError code: ' +str(e.code)
			cPrint(info, COLOR.RED)
		else:
			info = '[ERROR] Unknown URLError'
			cPrint(info, COLOR.RED)
		return False

	except Exception:
		import traceback
		print "Generic exception: " + traceback.format_exc()
		print info
		return False

def cleanLog():
	global refreshNetwork, passwordIncorrectTimes, serverFailureTimes, isConnected
	refreshNetwork = False
	passwordIncorrectTimes = 0
	serverFailureTimes = 0
	isConnected = False	

def refreshNetworkFunc():
	p = subprocess.Popen(
		'netsh wlan disconnect',
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()

def generateKey():
	import uuid
	from binascii import unhexlify as unhex
	ud = uuid.uuid1()
	ud = ud.hex
	mac = ud[-12:]
	hi_time = ud[12:16]
	key = hi_time + mac
	return unhex(key)

def encrypt(text):
	key = generateKey()
	des = pyDes.des(key, padmode = pyDes.PAD_PKCS5)
	return des.encrypt(text)
def decrypt(cipher):
	key = generateKey()
	des = pyDes.des(key)
	return des.decrypt(cipher, padmode = pyDes.PAD_PKCS5)
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

def fetchUserData(conn, cu):
	cu.execute('''SELECT * FROM user''')
	res = cu.fetchone()
	if res == None:
		return (None,None)
	else:#res[0] = id, res[1] = studentID, res[2] = password
		try:
			username = decrypt(res[1])
			password = decrypt(res[2])
			if len(username) == 0 or len(password) == 0:
				raise KeyExpireError
		except ValueError, e:
			cPrint("[WARNING] Database is damaged. Retrieving...", COLOR.DARKRED)
			cleanDB(conn, cu)
			username = password = None
		except KeyExpireError, e:
			cPrint("[WARNING] Session expires. Please enter username and password again.", COLOR.DARKRED)
			cleanDB(conn, cu)
			username = password = None
		except Exception, e:
			import traceback
			print "Generic exception: " + traceback.format_exc()
		finally:
			return (username, password)

def inputUsernameAndPassword():
	'''get username and password from console
		Return value:
			(isRememberPassword, username, password) 
	'''
	username = raw_input("Please enter your username:")
	password = getpass('Please enter your password(not be shown): ')
	state = raw_input("Remember this password?(y/n)")
	if state == 'Y' or state == 'y':
		isRememberPassword = True
	else:
		isRememberPassword = False
	return (isRememberPassword, username, password)

def isUseThisUsername(username):
	'''Ask user whether use the showed userneame to login.
	Parameter:
		username:
	Return value:
		True -- use this username
		False -- do not use this username
	'''
	state = raw_input("Do you want to use account {0} to login?(y/n)" .format(username))
	if state == 'Y' or state == 'y':
		return True
	else:
		return False
def insertUsernameAndPasswordToDB(conn, cu, username, password):
	username = encrypt(username)
	password = encrypt(password)
	cu.execute("INSERT INTO user(userStudentID, userPassword) VALUES (?,?)", (buffer(username), buffer(password)) )
	conn.commit()

def cleanDB(conn,cu):
	query = '''DELETE FROM user'''
	cu.execute(query)
	conn.commit()

def main():
	cPrint("Welcome to use ZJUWLAN auto login program.", COLOR.DARKGREEN)
	cPrint("Find bugs? Report it to %s :)\n" % author_email, COLOR.SILVER)
	(conn,cu) = connectToDB(db_name)
	(username,password) = fetchUserData(conn, cu)
	if username != None: #DB is not empty
		if isUseThisUsername(username) == False:
			#Clean DB and input new username and password
			cleanDB(conn,cu)
			username = password = None

	if username == None:#DB is empty or user doesn't use the current username
		(isRememberPassword, username, password) = inputUsernameAndPassword()
		if isRememberPassword == True:
			insertUsernameAndPasswordToDB(conn, cu, username, password)
		else:
			cleanDB(conn,cu)
	cu.close()
	conn.close()
	#Listen to the network status
	while exit == False:
		cPrint('[INFO] Checking network status...')
		if isConnectedToInternet(testWebsite):
			cPrint("[SUCCESS] Connected to the Internet.", COLOR.DARKGREEN)
			cleanLog()
			sleep(20)
			continue
		if isSpecifiedWlanAvailable(wlanName) == False:
			cPrint("[WARNING] "+ wlanName + " is not in range", COLOR.DARKRED)
			cleanLog()
			sleep(10)
			continue
		#wlan is available but host can not connect to the internet
		if isConnectedToSpecifiedWlan(wlanName) == False:
			cPrint('[INFO] Connecting to ' + wlanName + '...')
			cleanLog()
			status = connectTo(wlanName)
			if status != True:
				cPrint("[WARNING] Can not connect to {0}. Retry later." .format(wlanName), COLOR.DARKRED)
				sleep(5)
				continue
			else:
				sleep(5) #wait 5s 
		else:
			cPrint('[SUCCESS] Connected to ' + wlanName + '.', COLOR.DARKGREEN)
		#if login success but can still not connect to the internet.
		if refreshNetwork == True or isConnected == True: 
			cleanLog()
			cPrint("[INFO] Refreshing network connection....")
			refreshNetworkFunc()
			continue
		cPrint("[INFO] Username: " + username)
		cPrint("[INFO] Login...")
		status = logout(username, password)
		if status == False:
			sleep(5)
			continue
		status = login(username, password)
		if status == False:
			sleep(5)
			continue
		else:
			cPrint("[SUCCESS] Login Success.",COLOR.DARKGREEN)
	else:
		cPrint("\n[INFO] PROGRAM EXIT.",COLOR.SILVER)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt,e:
		cPrint("\n[INFO] PROGRAM EXIT.",COLOR.SILVER)
