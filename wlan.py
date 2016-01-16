# -*- coding:utf-8 -*-
#
# AUTO_LOGIN_ZJUWLAN and AUTO_START_HOTSPOT
#
#author: Bo Song, ZJU
#email: bo.song@yale.edu
#website: www.bo-song.com

#TODO
#Add encryption algorithm to store username and password at localhost --- DONE
#Fix the bug, which would get random-like MAC address - DONE 
#Modularization. 

#Import exit to exit program when necessary
import sys

#Import os module to do some IO work
import os

#Import universally unique identifiers to generate encryption key
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

#Configuration area
isSongBo = False
myWifiName = 'WLAN_sbo'
myWifiPassword = '12356789'

author_email = 'sbo@zju.edu.cn'
author_name = 'Song Bo'
date = '2014.8.22'
version = 'V0.3.3'
db_name = 'pywin27.dll'
log_name ='log' 
testWebsite1 = 'http://www.baidu.com'
testWebsite2 = 'http://www.google.com' #Add this test website to support proxy check. 
wlanName = 'ZJUWLAN'
maxRetryTimesForPassword = 3
maxRetryTimesForServer = 3
startWebsite = 'http://www.baidu.com'


DecryptionIdentifier = "sbo@zju.edu.cn"
wifiNamePrefix = 'WLAN_'
#Configuration area end.

#Global status area
isAskedTurnOnWifi = False
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

class DecryptionError(Exception):
	def __init__(self):
		Exception.__init__(self)

def cPrint(msg, color = COLOR.SILVER, mode = 0):
	'''Print coloforul message in console.
	msg -- message you want to print
	color -- color you want to use. There are 16 colors available by default. More details are available in class COLOR.
	mode -- 0: newline at the end
		 1: no newline at the end 
	'''
	import ctypes
	ctypes.windll.Kernel32.GetStdHandle.restype = ctypes.c_ulong
	h = ctypes.windll.Kernel32.GetStdHandle(ctypes.c_ulong(0xfffffff5))
	if isinstance(color, int) == False or color < 0 or color > 15:
		color = COLOR.SILVER #
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, color)
	if mode == 0:
		print msg
	elif mode == 1:
		import sys
		sys.stdout.write(msg)
		sys.stdout.flush()
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, COLOR.SILVER)

def pwd_input(msg = ''):
	import msvcrt, sys

	if msg != '':
		sys.stdout.write(msg)
	chars = []
	while True:
		newChar = msvcrt.getch()
		if newChar in '\3\r\n': # 如果是换行，Ctrl+C，则输入结束
			print ''
			if newChar in '\3': # 如果是Ctrl+C，则将输入清空，返回空字符串
				chars = []
			break
		elif newChar == '\b': # 如果是退格，则删除末尾一位
			if chars:
				del chars[-1]
				sys.stdout.write('\b \b') # 左移一位，用空格抹掉星号，再退格
		else:
			chars.append(newChar)
			sys.stdout.write('*') # 显示为星号
	return ''.join(chars)

def welcomeMsg():
	lineLength = 45
	line1 = 'Welcome to use ZJUWLAN_AUTO_LOGIN %s' %(version)
	line2 = 'Find bugs or have advices?'
	line3 = ' Report it to %s :)' % (author_email)
	cPrint("|----%s----|" %line1.center(lineLength), COLOR.DARKGREEN)
	cPrint("|----%s----|" %line2.center(lineLength), COLOR.DARKGREEN)
	cPrint("|----%s----|\n" %line3.center(lineLength), COLOR.DARKGREEN)
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
		response.close()
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

def turnOnWifi(ssid, password):
	if len(password) < 8:
		cPrint("[WARNING] Password shall contains at least 8 characters", COLOR.DARDRED)
		return False
	p = subprocess.Popen(
		'netsh wlan stop hostednetwork',
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()

	p = subprocess.Popen(
		'netsh wlan set hostednetwork mode=allow ssid=%s key=%s' %(ssid, password),
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()

	p = subprocess.Popen(
		'netsh wlan start hostednetwork',
		shell = True,
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE)
	stdout, stderr = p.communicate()
	return True

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
		response.close()
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
				cPrint("[UNKNOWN ERROR] " + content.decode('utf-8'),COLOR.RED)
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
		response.close()
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
				cPrint('[UNKNOWN ERROR]' + content.decode('utf-8'),COLOR.RED) #another unknown error reason
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

def _ipconfig_getnode():
	"""Get the hardware address on Windows by running ipconfig.exe."""

	def _random_getnode():
		"""Get a random node ID, with eighth bit set as suggested by RFC 4122."""
		import random
		return random.randrange(0, 1<<48L) | 0x010000000000L

	import os, re
	dirs = ['', r'c:\windows\system32', r'c:\winnt\system32']
	try:
		import ctypes
		buffer = ctypes.create_string_buffer(300)
		ctypes.windll.kernel32.GetSystemDirectoryA(buffer, 300)
		dirs.insert(0, buffer.value.decode('mbcs'))
	except:
		pass
	for dir in dirs:
		try:
			pipe = os.popen(os.path.join(dir, 'ipconfig') + ' /all')
		except IOError:
			continue
		bestMacAddress = '000000000000'
		for line in pipe:
			value = line.split(':')[-1].strip().lower()
			if re.match('([0-9a-f][0-9a-f]-){5}[0-9a-f][0-9a-f]', value):
				value = value.replace('-', '')
				if value.count('0') < bestMacAddress.count('0'):
					bestMacAddress = value
		if bestMacAddress != '000000000000':
			return bestMacAddress
		else:
			return None

#To be debuged. It is not tested cause there is not an OS/linux platform handy.
def _ifconfig_getnode():
	"""Get the hardware address on Unix by running ifconfig."""
	# This works on Linux ('' or '-a'), Tru64 ('-av'), but not all Unixes.
	for args in ('', '-a', '-av'):
		mac = _find_mac('ifconfig', args, ['hwaddr', 'ether'], lambda i: i+1)
	if mac:
		return str(mac)

	import socket
	ip_addr = socket.gethostbyname(socket.gethostname())
	# Try getting the MAC addr from arp based on our IP address (Solaris).
	mac = _find_mac('arp', '-an', [ip_addr], lambda i: -1)
	if mac:
		return str(mac)

	# This might work on HP-UX.
	mac = _find_mac('lanscan', '-ai', ['lan0'], lambda i: 0)
	if mac:
		return str(mac)
	return None

def generateKey():
	import uuid
	import sys
	from binascii import unhexlify as unhex
	if sys.platform == 'win32':
		mac = _ipconfig_getnode()
	else:
		mac = _ifconfig_getnode()
	if mac == None:
		mac = hex(_random_getnode())[2:-1]
	ud = uuid.uuid1()
	ud = ud.hex
	hi_time = ud[12:16]
	key = hi_time + mac
	return unhex(key)

def encrypt(text):
	if isinstance(text, str) == False:
		raise TypeError
	key = generateKey()
	text = DecryptionIdentifier + text
	des = pyDes.des(key, padmode = pyDes.PAD_PKCS5)
	return des.encrypt(text)

def decrypt(cipher):
	key = generateKey()
	des = pyDes.des(key)
	dcyIDLen = len(DecryptionIdentifier)
	text = des.decrypt(cipher, padmode = pyDes.PAD_PKCS5)
	if len(text) < dcyIDLen or text[0:dcyIDLen] != DecryptionIdentifier:
		raise DecryptionError
	else:
		text = text[dcyIDLen:]
		return text
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
		except ValueError, e:
			cPrint("[WARNING] Database is damaged. Retrieving...", COLOR.DARKRED)
			cleanDB(conn, cu)
			username = password = None
		except DecryptionError, e:
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

	usernameLength = 0
	while usernameLength == 0:
		username = raw_input("Please enter your ZJUWLAN username:")
		usernameLength = len(username)
	passwordLength = 0
	while passwordLength == 0:
		password = pwd_input('Please enter your password: ')
		passwordLength = len(password)
	state = raw_input("Remember this password on this laptop?(y/n)")
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
	cPrint("Dear", color = COLOR.SILVER, mode = 1)
	cPrint(" %s " %username, color = COLOR.BROWN, mode = 1)
	cPrint(", is it you?(y/n)", color = COLOR.SILVER, mode = 1)
	state = raw_input()
	if state == 'Y' or state == 'y' or state == '':
		return True
	else:
		return False
def insertUsernameAndPasswordToDB(conn, cu, username, password):
	username = encrypt(username)
	password = encrypt(password)
	#test
	# from binascii import hexlify
	# writeLog(hexlify(generateKey()), 'w')

	cu.execute("INSERT INTO user(userStudentID, userPassword) VALUES (?,?)", (buffer(username), buffer(password)) )
	conn.commit()

def cleanDB(conn,cu):
	query = '''DELETE FROM user'''
	cu.execute(query)
	conn.commit()
def isAskedTurnOnWifiFunc():
	return isAskedTurnOnWifi
def isTurnOnWifi():
	global isAskedTurnOnWifi
	isAskedTurnOnWifi = True
	state = raw_input("Do you want to turn on your laptop hotspot?(y/n)")
	if state == 'Y' or state == 'y':
		return True
	else:
		return False
def inputWifiNameAndPassword():
	global wifiNamePrefix
	nameLength = 0
	while nameLength == 0:
		wifiName = raw_input("Please set your wifi name(SSID):")
		nameLength = len(wifiName)
	wifiName = wifiNamePrefix + wifiName
	passwordLength = 0
	while passwordLength < 8:
		wifiPassword = raw_input("Please set your wifi password(at least 8 digits): ")
		passwordLength = len(wifiPassword)
	return (wifiName, wifiPassword)

def generatePassword(length, mode = None):
	import random
	if isinstance(length, int) == False:
		raise TypeError
	if length < 1:
		return None
	seed = uuid.uuid4().int
	password = ""
	for x in xrange(0,length):
		#[a-zA-Z0-9] 62 characters in total
		c = random.randint(0,61)
		if c < 10:
			password += chr(c+ord('0'))
		elif c < 36:
			password += chr(c+ord('A') - 10)
		else:
			password += chr(c+ord('a') - 36)
	return password

def writeLog(msg, mode = 'a'):
	fp = open(log_name, mode)
	fp.write(msg)
	fp.write('\n')
	fp.close()
def readLog():
	if os.path.isfile(log_name) == True:
		fp = open(log_name,'r')
		msg = fp.read()
		fp.close()
		return msg
	else:
		return ""
def main():
	global exit
	welcomeMsg()
	(conn,cu) = connectToDB(db_name)
	(username,password) = fetchUserData(conn, cu)
	if username != None: #DB is not empty
		if isSongBo == True:
			pass
		else:
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
		if isConnectedToInternet(testWebsite1) or isConnectedToInternet(testWebsite2):
			cPrint("[SUCCESS] Connected to the Internet.", COLOR.DARKGREEN)
			cleanLog()

			if isSongBo == True:
				if isAskedTurnOnWifiFunc() == False:
					global isAskedTurnOnWifi
					isAskedTurnOnWifi = True
					wifiName = myWifiName
					wifiPassword = myWifiPassword
					if turnOnWifi(wifiName, wifiPassword) == True:
						cPrint("[SUCCESS] Wifi %s is on work." % wifiName, COLOR.DARKGREEN)
						cPrint("[INFO] Wifi Password:", COLOR.SILVER, mode = 1)
						cPrint(" %s " % wifiPassword, COLOR.BROWN, mode = 0)	
				sleep(1)
				exit = True
				continue
			else:
				if isAskedTurnOnWifiFunc() == False:
					#following code runs only once. 
					if isTurnOnWifi() == True:
						(wifiName, wifiPassword) = inputWifiNameAndPassword()
						if turnOnWifi(wifiName, wifiPassword) == True:
							cPrint("[SUCCESS] Wifi %s is on work." % wifiName, COLOR.DARKGREEN)
							cPrint("[INFO] Wifi Password:", COLOR.SILVER, mode = 1)
							cPrint(" %s " % wifiPassword, COLOR.BROWN, mode = 0)	
					# os.system("start %s" %startWebsite)
				sleep(1)
				exit = True
				continue
				# else:
				#	sleep(20)
				#	continue
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
