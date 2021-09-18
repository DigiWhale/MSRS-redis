# Simple example
import time
import redis
from datetime import datetime
from redistimeseries.client import Client
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
    count += 1
    rts.add('heading', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), count * .5)
    print(rts.get('heading'))
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