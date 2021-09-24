import redis
from redistimeseries.client import Client
import json

# rts = Client(host='localhost', port=6379, db=0)
r = redis.Redis(host='192.168.1.4', port=6379, db=0, password='Redis2019!')
p = r.pubsub()
p.subscribe('msrs_raspberry', 'msrs_sensor')
# rts.create('test', labels={'Time':'Series'})
# rts.add('test', 1, 1.12)
# rts.add('test', 2, 1.12)
# rts.get('test')
# rts.incrby('test',1)
# rts.range('test', 0, -1)
# rts.range('test', 0, -1, aggregation_type='avg', bucket_size_msec=10)
# rts.range('test', 0, -1, aggregation_type='sum', bucket_size_msec=10)
# rts.info('test').__dict__
while True:
  msg = p.get_message()
  if msg:
    res = json.loads('{' + str(msg['data'])[1:-1] + '}'.replace("'", '"'))
    if (type(res) == type(dict())):
      print(res) 