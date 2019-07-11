#!/usr/bin/env python3

import time
import sqlite3
import os

import schedule
import credentials

#This is to specify the directory of the DB. Having a ton of problems while trying 
#to do this on Linux but Windows worked fine -_-
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "data.db")
conn = sqlite3.connect(db_path, check_same_thread=False)

c = conn.cursor()

current_machines = [2] #machine id number

def current_id(machine): #gives each new row a unique id so the most recent N points can be called
  try:
    c.execute("SELECT * FROM data_points WHERE machine=:machine ORDER BY id DESC LIMIT 1", {'machine': machine})
    return c.fetchone()[0]
  except:
    return 0

def delete_data(): #the machine number needs to be passed in order to delete the data

    global current_machines

    for x in current_machines:

      machine_id = current_id(x) - 4320 #Will keep 4320 data points, or 3 days worth of data
      with conn:
        c.execute("DELETE FROM data_points WHERE id<=:id", {'id': machine_id}) #deletes data points that are greater than 7 days old
      time.sleep(2) #sleep for 2 second to prevent deletion from happening too quickly and corrupting the database

    print("Data has been removed")

schedule.every().day.at("01:00").do(delete_data) #everyday at 1 am clean the DB

def main():
  print("delete_data.py script has started")
  while True:
      schedule.run_pending()
      time.sleep(60)

main()