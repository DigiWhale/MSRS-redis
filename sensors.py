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
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
from dotenv import load_dotenv
import os

load_dotenv()

def send_mail(send_from, send_to, subject, message, files=['/home/pi/Desktop/map.html', '/home/pi/MSRS-redis/position_list.csv'],
              server="smtp.gmail.com", port=587, username=os.environ.get("EMAIL"), password=os.environ.get("PASSWORD"),
              use_tls=True):
    """Compose and send email with provided info and attachments.

    Args:
        send_from (str): from name
        send_to (list[str]): to name(s)
        subject (str): message title
        message (str): message body
        files (list[str]): list of file paths to be attached to email
        server (str): mail server host name
        port (int): port number
        username (str): server auth username
        password (str): server auth password
        use_tls (bool): use TLS mode
    """
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(message))

    for path in files:
        part = MIMEBase('application', "octet-stream")
        with open(path, 'rb') as file:
            part.set_payload(file.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename={}'.format(Path(path).name))
        msg.attach(part)

    smtp = smtplib.SMTP(server, port)
    if use_tls:
        smtp.starttls()
    smtp.login(username, password)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.quit()


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
        # print('{' + str(msg['data'])[1:-1] + '}')
        res = json.loads('{' + str(msg['data'])[1:-1] + '}')
        # res = ast.literal_eval(str(msg['data'])[2:-1])
        if (type(res) == type(dict()) and len(res) > 2):
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
            rts.add('angle', '*', res['sensor_value']['yaw_2'], duplicate_policy='last')

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
          position_list.append({'lat': lat, 'lon': lon, 'total_distance': total_distance, 'angle': angle[1], 'heading': heading[1]})
        

    except:
        log_dict_list_to_csv(position_list, 'position_list.csv')
        df = pd.DataFrame(position_list)

        fig = px.scatter_mapbox(df, lat='lat', lon='lon', size_max=8, zoom=18, center={'lat': 0, 'lon': 0})
        fig.update_layout(mapbox_style="dark", mapbox_accesstoken='pk.eyJ1IjoiZnJzdHlsc2tpZXIiLCJhIjoiY2tmdDFveTI5MGxraDJxdHMzYXM4OXFiciJ9.96hyKcaRFBFzH6xcsN3CYQ')
        fig.write_html('/home/pi/Desktop/map.html')
        send_mail('frstylskier@gmail.com', ['andrew.2.humphrey@gmail.com'], 'map', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("Logged positions")
        break