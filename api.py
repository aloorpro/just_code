from flask import Flask, request
from time import time
from hashlib import md5
from base64 import b64encode
from json import dumps
import re
from  ConfigParser import ConfigParser

def get_config(cfg): #making dict with values from cfg
    config = ConfigParser()
    config.read(cfg)
    data = {}
    for section in config.sections():
        data[section] = {}
        for option in config.options(section):
            data[section][option] = config.get(section, option)
    return data


def check(data):     #checking input values
    data['errors'] = {}
    for param in data['parameters']:
        #check if parameter exists
        if data['parameters'].get(param) == None:
            if data['default'].get(param) == None:
                data['errors'][param] = 'Fatal error. Param is not defined'
                break
            else:
                data['errors'][param] = 'Param is not defined. Using default'
                data['parameters'][param] = data['default'][param]
        #check time
        elif param == 't':
            if type(data['parameters'][param]) is not int:
                data['errors']['t'] = 'time is not a number, using default'
                data['parameters']['t'] = data['default']['t']
            elif data['parameters'][param] < int(time()):
                data['errors']['t'] = 'input time is gone, using default'
                data['parameters']['t'] = data['default']['t']
        #check ip
        elif param == 'ip':
            try:
                octets = data['parameters'][param].split('.')
                is_ip = all([len(octets) == 4, 0 < int(octets[0]) < 224] + 
                            [0 <= int(octet) < 256 for octet in octets[1:]])
            except ValueError: is_ip = False
            if is_ip == False: 
                data['errors']['ip'] = 'IP address if wrong, using default'
                data['parameters']['ip'] = data['default']['ip']
        #check uri
        elif param == 'u':
            uri = data['parameters'][param]
            data['parameters']['u'] = uri = \
                                    data['parameters']['u'].replace('//','/')
            if re.search(r'[^\w/\-_,\.]', uri) != None:
                data['errors']['u'] = 'URI is wrong, using default'
                data['parameters']['u'] = data['default']['u']
            elif re.match(r'[/]?s/.*', uri) == None:
                data['errors']['u'] = 'location is not /s/, URI changed'
                if uri[0] == '/': data['parameters']['u'] = '/s'+ uri
                else: data['parameters']['u'] = '/s/' + uri
            if uri[0] != '/':
                data['parameters']['u'] = '/'+ data['parameters']['u']
            if uri[-1] == '/':
                data['parameters']['u'] = data['parameters']['u'][:-1]
        #check password
        elif param == 'p':
            if data['parameters'][param] != data['default']['p']:
                data['errors']['p'] = 'Your password if wrong, using default'
                data['parameters']['p'] = data['default']['p']
    if data['errors'] == {}: data.pop('errors')
    data.pop('default')
    return data


def link(data):
    md5Obj = md5()
    md5Obj.update(str(data['parameters']['t']) + 
                    data['parameters']['u'] + 
                    data['parameters']['ip'] + '=' + 
                    data['parameters']['p'])
    nginxMD5 = b64encode(md5Obj.digest())
    nginxMD5 = nginxMD5.replace('/','_')
    nginxMD5 = nginxMD5.replace('+','-')
    nginxMD5 = nginxMD5.replace('=','')
    data['result']['md5'] = nginxMD5
    data['result']['link'] = '{}?md5={}&expires={}'.format( \
                                            data['parameters']['u'],
                                            data['result']['md5'],
                                            str(data['parameters']['t']))
    return data


app = Flask(__name__)

@app.route('/securelink')
def securelink():
    cfg = './api.cfg'
    answer = get_config(cfg)
    answer['parameters'] = {}
    answer['result'] = {}

    answer['default']['t'] = int(time()) + 3600
    answer['default']['ip'] = request.environ['REMOTE_ADDR']

    answer['parameters']['t'] = request.args.get(
                                't', answer['default'].get('t'), int)
    answer['parameters']['ip'] = request.args.get(
                                'ip', answer['default'].get('ip'), str)
    answer['parameters']['u'] = request.args.get(
                                'u', answer['default'].get('u'), str)
    answer['parameters']['p'] = request.args.get(
                                'p', answer['default'].get('p'), str)

    answer = check(answer)
    if 'Fatal error. Param is not defined' in answer['errors'].values():
        return dumps(answer, sort_keys=True, indent=4)
    answer = link(answer)
    answer['parameters'].pop('p')
    return dumps(answer, sort_keys=True, indent=4)

@app.errorhandler(404)
def not_found(error):
    response = {'error': 'Page_not_found', 'availiable_link': 
             '/securelink?p=[password]&t=[time]&u=[uri]&ip=[A.B.C.D]'}
    return dumps(response, sort_keys=True, indent=4)

if __name__ == '__main__':
    app.run()