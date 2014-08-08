# -*- coding:utf-8 -*-
#author: Sunny Song, ZJU
#email: sbo@zju.edu.cn
import hashlib
import urllib
from urllib2 import Request, urlopen, URLError, HTTPError
from time import sleep
import subprocess
import urllib

#Replace yourusername and yourpassword with your username and password
username = 'yourusername' 
password = 'yourpassword'

#Configuration area
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

def cPrint(msg, color = COLOR.SILVER):
	import ctypes
	ctypes.windll.Kernel32.GetStdHandle.restype = ctypes.c_ulong
	h = ctypes.windll.Kernel32.GetStdHandle(ctypes.c_ulong(0xfffffff5))
	if isinstance(color, int) == False or color < 0 or color > 15:
		color = COLOR.SILVER #
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, color)
	print msg
	ctypes.windll.Kernel32.SetConsoleTextAttribute(h, COLOR.SILVER)

def isConnectedToInternet(url):
	'''return true if host is already connected to the internet, otherwise return false.'''
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
			cPrint(info, COLOR.DARKRED)
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

def isSpecifiedWlanAvaliable(name):
	'''return true if specified wlan (name) is currently avaliable, otherwise return false. '''
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
	successMsg = u'已成功完成连接请求。'
	#Since encoding rule ranges in different areas. Length of msg is used to check whether the connection is successful or not.
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
				cPrint("[WARNING] Username or password is incorrect. Please check them again.",CLOLR.RED)
				cPrint("[INFO] Retry for {0} more times." .format(maxRetryTimesForPassword - passwordIncorrectTimes))
				passwordIncorrectTimes += 1
				if passwordIncorrectTimes == 3:
					exit = True
			return False

	except URLError, e:
		if hasattr(e, 'reason'):
			info = '[ERROR] Failed to reach the server.\nReason: ' + str(e.reason)
		elif hasattr(e, 'code'):
			info = '[ERROR] The server couldn\'t fullfill the request.\nError code: ' +str(e.code)
		else:
			info = '[ERROR] Unknown URLError'
		cPrint(info, COLOR.DARKRED)
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
				cPrint("[WARNING] Username or password is incorrect. Please check them again.", COLOR.RED)
				cPrint("[INFO] Retry for {0} more times." .format(maxRetryTimesForPassword - passwordIncorrectTimes))
				passwordIncorrectTimes += 1
				if passwordIncorrectTimes == maxRetryTimesForPassword:
					exit = True
			else:
				print content #another unknown error reason
			return False 

	except URLError, e:
		if hasattr(e, 'reason'):
			# '[Error] Failed to reach the server.\nReason: ' + str(e.reason)
			info = '[WARNING] Failed to reach the server. Retry for {0} more times.' .format(maxRetryTimesForServer - serverFailureTimes)
			serverFailureTimes += 1
			if serverFailureTimes == maxRetryTimesForServer:
				refreshNetwork = True
			cPrint(info,COLOR.RED)
		elif hasattr(e, 'code'):
			info = '[ERROR] The server couldn\'t fullfill the request.\nError code: ' +str(e.code)
			cPrint(info, COLOR.DARKRED)
		else:
			info = '[ERROR] Unknown URLError'
			cPrint(info, COLOR.DARKRED)
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

def main():
	#Listen to the network status

	while exit == False:
		cPrint('[INFO] Checking network status...')
		if isConnectedToInternet(testWebsite):
			cPrint("[SUCCESS] Connected to the Internet.", COLOR.GREEN)
			cleanLog()
			sleep(20)
			continue
		if isSpecifiedWlanAvaliable(wlanName) == False:
			cPrint("[WARNING] "+ wlanName + " is not in range", COLOR.RED)
			cleanLog()
			sleep(10)
			continue
		#wlan is avaliable but host can not connect to the internet
		if isConnectedToSpecifiedWlan(wlanName) == False:
			cPrint('[INFO] Connecting to ' + wlanName + '...')
			cleanLog()
			status = connectTo(wlanName)
			if status != True:
				cPrint("[WARNING] Can not connect to {0}. Retry later." .format(wlanName), COLOR.RED)
				sleep(5)
				continue
			else:
				sleep(5) #wait 5s 
		else:
			cPrint('[SUCCESS] Connected to ' + wlanName + '.', COLOR.GREEN)
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
			cPrint("[SUCCESS] Login Success.",COLOR.GREEN)
if __name__ == '__main__':
	main()
