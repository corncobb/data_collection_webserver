#!/bin/bash
sudo -H -u pi /usr/bin/python3 /home/pi/Desktop/data_collection_webserver/data_receiver.py &
sleep 3
sudo -H -u pi /usr/bin/python3 /home/pi/Desktop/data_collection_webserver/delete_data.py &
sleep 3
sudo -H -u pi /usr/bin/python3 /home/pi/Desktop/data_collection_webserver/app.py &