import mysql.connector
import re
import pexpect
import string

class nwdb():
	def __init__(self, numm):
		self.db = mysql.connector.connect(host='10.135.132.61', user='dgh', passwd='3xkrivolapp', db='NWLINK', charset='utf8')
		self.cursor = self.db.cursor()
		self.params = ['Number', 'IP', 'Masck', 'Gate', 'Number_net', 'Number_serv', 'switchP', 'PortP', 'vlan', 'dhcp_type', 'Add_IP', 'Vznos']
		self.info = self.getuserinfo(numm) 
#		self.sw = self.explogin(self.base('switchP'))
	

	def getuserinfo(self, numm):  #Коннектимся к базе и получаем список параметров, заданный в переменной params
		self.cursor.execute("SELECT {} FROM users WHERE Number={}".format(', '.join(self.params), numm))
		data = self.cursor.fetchall()
		info = dict(zip(self.params, data[0]))
		return info

	def base(self, column):
		return self.info.get(column)

	def L3(self):
		self.cursor.execute("SELECT IP FROM users WHERE Vznos='59' AND Number_net='{}' AND IP LIKE '10.%.253' AND FIO !='3120-24TC' LIMIT 1".format(self.base('Number_net')))
		res = self.cursor.fetchall()
		if res == []:
			res = self.base('switchP').rpartition('.')[0] + '.253'
			return res
		return res[0][0]


	def getGateExtIP(self):  #Для внешников функция: получает адрес настоящего шлюза из базы в зависимости от номера влана
		if self.base('vlan') == '404':
			return self.L3()
		elif self.base('vlan') == (0 or None):
			return None
		else:
			self.cursor.execute("SELECT Gate FROM users WHERE Number_net='{}' AND vlan='{}' AND Gate LIKE '10%' LIMIT 1".format(self.base('Number_net'),self.base('vlan')))
			gate = self.cursor.fetchall()
			return gate[0][0]

	def realgate(self):  #Выясняем, првнеш это или нет. Если 
		inf = self.base('Gate') 
		if inf == ('' or None):
			return None
		elif inf[1] == '0':
			return self.base('Gate')
		else:
			return self.getGateExtIP()


class nwtel():
	
	def __init__(self, ip):
		self.conn = self.explogin(ip)

	def explogin(self, ip):	        #логинется на наш свич по адресу и создает объект для манипуляций
		if ip == None or ip == '': return 0
		cn = pexpect.spawn ('telnet {}'.format(ip))
		index = cn.expect([':', pexpect.TIMEOUT], timeout=5)
		if index == 1: return 1
		cn.sendline('angel'); cn.expect(':'); cn.sendline('842huevgalz'); cn.expect('#')
		return cn

	def expint(self):               #запускаем интерактив по имеющемуся соединению
		self.conn.sendline('')
		self.conn.interact()
		pass

	def telovertel(self, ip):
		self.conn.sendline('telnet {}'.format(ip))
		index = self.conn.expect(['UserName:', pexpect.TIMEOUT], timeout=5)
		if index == 1: return 1
		self.conn.sendline('angel'); self.conn.expect('PassWord:'); self.conn.sendline('842huevgalz'); self.conn.expect('#')

	def rescomm(self, command):     #спрашиваем команду и получаем вывод без дисконнекта
		self.conn.sendline(command)
		k = self.conn.expect(['#', pexpect.TIMEOUT], timeout=1)
		if k == 1:
			self.conn.sendline('a')
			self.conn.expect('#')
		data = self.conn.before.decode('utf8')
		return data.split('\n\r')

	def parsetable(self, command, pattern):
		data = self.rescomm(command)
		pattern = re.compile(pattern)
		result = []
		for line in data:
			res = pattern.search(line)
			if res != None: 
				result.append(res.groups())
		return result

	def arpbyip(self, ip):
		return self.parsetable('show arpentry ipaddress {}'.format(ip), '(\d{1,3}\\.\d{1,3}\\.\d{1,3}\\.\d{1,3}).*(\w\w-\w\w\-\w\w-\w\w\-\w\w-\w\w)')
	def fdbbyport(self, port):
		return self.parsetable('show fdb port {}'.format(port), '(\d{1,4}).*(\w\w-\w\w\-\w\w-\w\w\-\w\w-\w\w)')
	def dgate(self): 
		return self.parsetable('show iproute 0.0.0.0/0', '(\d{1,3}\\.\d{1,3}\\.\d{1,3}\\.\d{1,3})\s+(\S*)')
	def allstrt(self):
		return self.parsetable('show iproute static', '(\d{1,3}\\.\d{1,3}\\.\d{1,3}\\.\d{1,3})\\/32\s*(\S+)')