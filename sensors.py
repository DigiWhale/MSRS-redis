# Simple example
import time
import redis
import json
import random
from datetime import datetime
from redistimeseries.client import Client
import math
import plotly.express as px
import pandas as pd
import ast


def calculate_new_coordinates(prev_lat, prev_lon, heading, distance):
    R = 6378.1 #Radius of the Earth
    brng = heading * (math.pi / 180) #Heading is converted to radians.
    d = distance #Distance in km

    lat1 = prev_lat * (math.pi / 180) #Current lat point converted to radians
    lon1 = prev_lon * (math.pi / 180) #Current lon point converted to radians

    lat2 = math.asin(math.sin(lat1)*math.cos(d/R) + math.cos(lat1)*math.sin(d/R)*math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1), math.cos(d/R)-math.sin(lat1)*math.sin(lat2))

    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)

    return {'lat': lat2, 'lon': lon2}
  
def log_dict_list_to_csv(dict_list, filename):
    with open(filename, 'w') as f:
        for d in dict_list:
            f.write(','.join(str(d[k]) for k in d) + '\n')

r = redis.StrictRedis(host='192.168.1.4', port=6379, db=0, password='Redis2019!', charset="utf-8", decode_responses=True)
p = r.pubsub()
p.subscribe('msrs_raspberry')
rts = Client(redis.Redis(host="localhost", port=6379, db=0))
count = 0
total_distance = 0
lat = 0
lon = 0
new_position = {'lat': 0, 'lon': 0}
position_list = []
try:
    rts.create('heading', labels={'Time':'Series'})
    rts.create('altitude', labels={'Time':'Series'})
    rts.create('angle', labels={'Time':'Series'})
    rts.create('distance', labels={'Time':'Series'})
    rts.create('speed', labels={'Time':'Series'})
except:
    pass
while True:
    try:
      msg = p.get_message()
      if msg:
        print(msg)
        res = json.loads(str(msg['data']).replace("'", ""))
        # res = ast.literal_eval(str(msg['data'])[2:-1])
        if (type(res) == type(dict())):
          if (res['sensor_type'] == 6):
            # print(res['sensor_type'], res['sensor_value']['altitude'])
            rts.add('altitude', '*', res['sensor_value']['altitude'], duplicate_policy='last')
          elif (res['sensor_type'] == 3):
            # print(res['sensor_type'], res['sensor_value']['velocity_1'])
            # print(res['sensor_type'], res['sensor_value']['distance_1'])
            rts.add('speed', '*', res['sensor_value']['velocity_1'], duplicate_policy='last')
            rts.add('distance', '*', res['sensor_value']['distance_1'], duplicate_policy='last')
            total_distance += res['sensor_value']['distance_1']

          elif (res['sensor_type'] == 4):
            # print(res['sensor_type'], res['sensor_value']['heading_3'])
            rts.add('heading', '*', res['sensor_value']['heading_3'], duplicate_policy='last')
          elif (res['sensor_type'] == 5):
            # print(res['sensor_type'], res['sensor_value']['angle_2'])
            rts.add('angle', '*', res['sensor_value']['angle_2'], duplicate_policy='last')


        # print('Travelled ', rts.get('distance'), 'with a heading of ', rts.get('heading'), 'and a total distance of ', total_distance)
        heading = rts.get('heading')
        distance = rts.get('distance')
        angle = rts.get('angle')
        # print(heading[1], distance[1])
        new_position = calculate_new_coordinates(lat, lon, heading[1], distance[1])
        if lat != new_position['lat'] or lon != new_position['lon']:
          lat = new_position['lat']
          lon = new_position['lon']
          print('Heading: ', heading[1], 'Distance:', distance[1], 'Total distance: ', total_distance, 'Angle: ', angle[1])
          position_list.append({'lat': lat, 'lon': lon})
        

    except:
        log_dict_list_to_csv(position_list, 'position_list.csv')
        df = pd.DataFrame(position_list)

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size_max=8, zoom=18, center={'lat': 0, 'lon': 0})
        fig.update_layout(mapbox_style="dark", mapbox_accesstoken='pk.eyJ1IjoiZnJzdHlsc2tpZXIiLCJhIjoiY2tmdDFveTI5MGxraDJxdHMzYXM4OXFiciJ9.96hyKcaRFBFzH6xcsN3CYQ')
        fig.write_html('/home/pi/Desktop/map.html')
        print("Logged positions")
        break