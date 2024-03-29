#!/usr/bin/env python3

#Standard imports
import sqlite3
import datetime
from multiprocessing import Process
import time
import sys
import os.path

#Third party improts
import paho.mqtt.client as mqtt
import credentials
import schedule

broker = credentials.credentials['broker']
#broker = "test.mosquitto.org" #for testing purposes ONLY
machines = 2 #total number of machines. This will change once more machines are introduced

current_machines = [2] #list the machines id that will be running and connecting to the database, not in use yet

#This is to specify the directory of the DB. Having a ton of problems while trying 
#to do this on Linux but Windows worked fine -_-
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "data.db")
conn = sqlite3.connect(db_path, check_same_thread=False)

c = conn.cursor()

try:
  c.execute("""CREATE TABLE data_points (
              id integer,
              machine integer,
              state text,
              time text,
              count integer,
              operation real,
              shift real,
              encoder real,
              downTime integer,
              shiftTime integer,
              operationTime integer
            )""")
  print("Table has been created")

except:
  print("Table already exists")

def insert_data(machine, state, Ttime, count, operation, shift, encoder, downTime, shiftTime, operationTime):
  with conn:
    c.execute("INSERT INTO data_points VALUES (:id, :machine, :state, :time, :count, :operation,\
              :shift, :encoder, :downTime, :shiftTime, :operationTime)",
            {'id': current_id(machine) + 1, 'machine': machine, 'state': state, 'time': Ttime, 'count': count,
            'operation': operation, 'shift': shift, 'encoder': encoder,
             'downTime': downTime, 'shiftTime': shiftTime, 'operationTime': operationTime})
    print("Data has been put in table") #used for debugging, uncomment if you want

def current_id(machine): #gives each new row a unique id so the most recent N points can be called
  try:
    c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY id DESC LIMIT 1", {'machine': machine})
    return c.fetchone()[0]
  except:
    return 0

def retrieve_recent(machine):
  c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY id DESC LIMIT 1", {'machine': machine})
  data = c.fetchone() 
  if data == None:
    return (0,0,0,str(datetime.time(0)),0,0,0,0,0,0,0)
  else:
    return data

def retrieve_all(): #this is used for debugging
  c.execute("SELECT * FROM data_points")
  return c.fetchall()

# The callback for when the client receives a CONNECT response from the server.

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connection OK, status code: " + str(rc))

    else:
        print("Connection was refused! Retured: " + str(rc))
    # Subscribing in on_connect() - if we lose the connection and
    # reconnect then subscriptions will be renewed.

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    incoming_data = str(msg.payload.decode('ASCII'))
    
    print(msg.topic + " " + incoming_data)
    if '$' in incoming_data:
      incoming_data = incoming_data.split('$')
      
      machine = int(incoming_data[0])
      state = incoming_data[1]
      Ttime = incoming_data[2]
      count = int(incoming_data[3])
      operation = float(incoming_data[4])
      shift = float(incoming_data[5])
      encoder = float(incoming_data[6])
      downTime = int(incoming_data[7])
      shiftTime = int(incoming_data[8])
      operationTime = int(incoming_data[9])

      insert_data(machine, state, Ttime, count, operation, shift, encoder, downTime, shiftTime, operationTime) #puts the data into database
    else:
      print("Data does not have correct format")
 
# Create an MQTT client and attach our routines to it.
def main():
    #print(retrieve_all()) #prints all in database, used for debugging
    topics = []
    qos = 0
    for x in range(machines): # put how many machines there are here
        topics.append(("data/" + "machine" + str(x+1), qos))


    print("Topics being subscribed to:")
    for x in topics:
        print(x)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("\n" + '*'*30 + "\nConnecting to broker: " + broker)
    try:
      client.connect(broker, 1883, 60)
    except:
      print("Failed to connect to broker! Ending program")
      sys.exit()

    r = client.subscribe(topics)

    if r[0]==0:
        print("Subscribing was successful")

    else:
        print("subscribing was NOT unsuccessful")
    # Process network traffic and dispatch callbacks. This will also handle
    # reconnecting. Check the documentation at
    # https://github.com/eclipse/paho.mqtt.python
    # for information on how to use other loop*() functions
    client.loop_forever()

#This is intended to run right before app.py has started. 
main()
