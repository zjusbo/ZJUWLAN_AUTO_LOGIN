ZJUWLAN_AUTO_LOGIN
==================
This is a Python script that helps you connect to ZJUWLAN automatically.

It implements some basic functions such as wifi scanning, wifi connecting, login, connection lost recovering and error recovering.

Implemented in Python 2.7.6.

Support OS: Windows 7.

##BUGS
- Key expires so quick. It only last about 1 day. Checking it...SOLVED
- Sometimes it refreshes the connection though we are still online, which causes a connection lost.

##TODO 
- Support Ethernet login **via vpn**. 10.5.1.7 or vpn2.zju.edu.cn
- Check the connection states via some more efficient methods. (currently it tries to connect to a testwebsite using HTTP protocol.)


Author: Song Bo, Zhejiang University

Email: sbo at zju dot edu dot cn
