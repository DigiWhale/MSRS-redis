# Simple example
import time
import redis
import json
import random
from datetime import datetime
from redistimeseries.client import Client
import ast

r = redis.StrictRedis(host='192.168.1.4', port=6379, db=0, password='Redis2019!', charset="utf-8", decode_responses=True)
p = r.pubsub()
p.subscribe('msrs_raspberry')
rts = Client(redis.Redis(host="localhost", port=6543, db=0))
count = 0
try:
    rts.create('heading', labels={'Time':'Series'})
    rts.create('acceleration', labels={'Time':'Series'})
    rts.create('angle', labels={'Time':'Series'})
    rts.create('distance', labels={'Time':'Series'})
    rts.create('speed', labels={'Time':'Series'})
except:
    pass
while True:
    count = random.randint(0,360)
    rts.add('heading', '*', count * .5, duplicate_policy='last')
    rts.add('acceleration', '*', count * .5, duplicate_policy='last')
    rts.add('angle', '*', count * .5, duplicate_policy='last')
    rts.add('distance', '*', count * .5, duplicate_policy='last')
    rts.add('speed', '*', count * .5, duplicate_policy='last')
    # print(rts.get('heading'), rts.get('acceleration'), rts.get('angle'), rts.get('distance'), rts.get('speed'))
    msg = p.get_message()
    if msg:
      res = json.loads(str(msg['data']).replace("'", ""))
      if (type(res) == type(dict())):
        for key, value in res.items():
          print(key, value)
      else:
        print(type(res))
    # try:
    #     rts.add('test', 1, 1.12)
    #     rts.add('test', 2, 1.12)
    # except:
    #     pass
    # print(rts.get('test'))
    # time.sleep(1)
    # rts.incrby('test',1)
    # try:
    #     rts.range('test', 0, -1)
    #     rts.range('test', 0, -1, aggregation_type='avg', bucket_size_msec=10)
    #     rts.range('test', 0, -1, aggregation_type='sum', bucket_size_msec=10)
    # except:
    #     pass
    # rts.info('test').__dict__