#!/usr/bin/env python3

import requests
import json
import mysql.connector
import sys
import re
import logging

log_file = '/home/zavadsky/scripts/log_filename.txt'
logging.basicConfig(filename=log_file,level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

conn = mysql.connector.connect(host='localhost', user='aster', passwd='password', db='aster', charset='utf8')
cursor = conn.cursor()

phone = sys.argv[1]
if re.match(r'\d+', phone).group() != phone or len(phone) != 10:
	logging.error('{} is not a phone number'.format(phone))
	print('There is an error, check {}'.format(log_file))
	sys.exit()

def check_base(phone):
	cursor.execute(\
		"SELECT phone, source FROM operators WHERE phone='{}' AND date > DATE_ADD(NOW(),\
		 INTERVAL -30 DAY)".format(phone))
	result = cursor.fetchall()
	if len(result) >= 2:
		logging.info('Number {} is in the base'.format(phone))
		return result
	elif len(result) == 1:
		return result[0][1]
	else:
		return None

def ask_megafon(phone):
	response = requests.get('http://www.megafon.ru/api/mfn/info?msisdn=7{}'.format(phone),\
							proxies=dict(http='socks5://127.0.0.1:3128'))
	result = json.loads(response.text)
	if result.get('error') != None:
		logging.error('Megafon sent error: {}'.format(result.get('error')))
		return None
	if type(result.get('operator')) != str\
			or type(result.get('operator_id')) != int\
			or type(result.get('region')) != str\
			or type(result.get('region_id')) != int:
		logging.error('Output is not complete: {}'.format(result))
		return None
	result['source'] = 'megafon'
	return result

def ask_htmlweb(phone):
	response = requests.get('http://htmlweb.ru/sendsms/api.php?mnp=7{}&json'.format(phone),\
							proxies=dict(http='socks5://127.0.0.1:3128'))
	result = json.loads(response.text)
	if result.get('error') != None:
		logging.error('Htmlweb sent error: {}'.format(result.get('error')))
		return None
	res = {'source': 'htmlweb', 'operator_id': result.get('oper').get('mnc'),\
			'region_id': result.get('region').get('autocod'),\
			'region': result.get('region').get('name'), 'operator': result.get('oper').get('name')}
	if type(res.get('operator')) != str\
			or type(res.get('operator_id')) != int\
			or type(res.get('region')) != str\
			or type(res.get('region_id')) != int:
		logging.error('Output is not complete: {}'.format(res))
		return None
	return res

def renew_base(phone, data):
	cursor.execute("REPLACE INTO operators (phone, operator, operator_id, region, region_id, source)\
					VALUES ('{}', '{}', {}, '{}', {}, '{}')".format(\
						phone, data['operator'], data['operator_id'],\
						data['region'], data['region_id'], data['source']))
	conn.commit()
	logging.info('Number {} updated successfully: {}'.format(phone, data))

data = None
check = check_base(phone)

if check == 'megafon':
	data = ask_htmlweb(phone)
elif check == 'htmlweb':
	data = ask_megafon(phone)
if data != None:
	renew_base(phone, data)
	sys.exit()

if check == None:
	data = ask_megafon(phone)
	if data != None: renew_base(phone, data)
	data = ask_htmlweb(phone)
	if data != None: renew_base(phone, data)
if source == 'megafon': data = ask_megafon(phone)
elif source == 'htmlweb': data = ask_htmlweb(phone)

sys.exit()