#!/usr/bin/env python
__author__ = 'Justin Bollinger'

import RPi.GPIO as GPIO
import smtplib
from email.mime.text import MIMEText
import json
from astral import Astral
import datetime
import time
import pytz
import sys

def door_change():
    print "Door Changed"
    GPIO.output(door_relay_pin, GPIO.HIGH)
    time.sleep(30)
    GPIO.output(door_relay_pin, GPIO.LOW)

def sendtext(me, you, msg):
    s = smtplib.SMTP(email_host)
    s.login(email_username, email_password)
    s.sendmail(me, you, msg.as_string())
    s.quit()

config_file = sys.argv[1]

#Parse config.json for configuration data
with open(config_file) as data_file:
    config = json.load(data_file)

email_username = str(config["email_username"])
email_password = str(config["email_password"])
email_host = str(config["email_host"])
mail_from_address = str(config["mail_from_address"])
mail_to_address = str(config["mail_to_address"]).strip('[]').split(',')

textenabled = config["textenabled"]
door_sensor_pin = int(config["door_sensor_pin"])
door_relay_pin = int(config["door_relay_pin"])
city_name = config["city_name"]
timezone = config["timezone"]


#initilize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(door_sensor_pin, GPIO.IN)
GPIO.setup(door_relay_pin, GPIO.OUT)
MAG_SENSOR = GPIO.input(door_sensor_pin)

#init delay before setting the door_sensor state
time.sleep(5)

current_state = GPIO.input(door_sensor_pin)
previous_state = GPIO.input(door_sensor_pin)

#Specify text messages
startupmsg = MIMEText('')
startupmsg['From'] = mail_from_address
startupmsg['To'] = ", ".join(mail_to_address)
startupmsg['Subject'] = 'chickencoop raspberry pi startingup'


openmsg = MIMEText('')
openmsg['From'] = mail_from_address
openmsg['To'] = ", ".join(mail_to_address)
openmsg['Subject'] = 'Coop door opened'

closedmsg = MIMEText('')
closedmsg['From'] = mail_from_address
closedmsg['To'] = ", ".join(mail_to_address)
closedmsg['Subject'] = 'Coop door closed'
if textenabled:
    sendtext(mail_from_address, mail_to_address, startupmsg)
#initilize astral object and create sun object
a = Astral()
a.solar_depression = 'civil'
city = a[city_name]
sun = city.sun(date=datetime.date.today(), local=True)


pytz.timezone(timezone)
try:
    while True:
        door_sensor = GPIO.input(door_sensor_pin)
        now = datetime.datetime.now(pytz.timezone(timezone))
        dusk_today = city.sun(date=now,local=True)['dusk']
        dawn_today = city.sun(date=now,local=True)['dawn']
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        #check to see if the door should be closed .  If time is between dusk today and dawn tomorrow the door
        # should be closed.
        if dusk_today < now or now < dawn_today:
            if door_sensor == 1:
                current_state = 1
                print "Close Door"
                door_change()
            else:
                print "Door is already Closed" + now.strftime('%H%m')
        #Check to see if the door should be open.  If time is between dawn today and dusk today the door should be
        # open.
        elif dawn_today < now < dusk_today:
            if door_sensor == 0:
                current_state = 0
                print "Open Door"
                door_change()
            else:
                print "Door is already Open" + now.strftime('%H%m')
        else:
            print 'Error time not valid'
            quit(1)
        if current_state != previous_state:
            if current_state == 0:
                if textenabled:
                    sendtext(mail_from_address, mail_to_address, openmsg)
                previous_state = current_state
            else:
                if textenabled:
                    sendtext(mail_from_address, mail_to_address, closedmsg)
                previous_state = current_state
except KeyboardInterrupt:
    GPIO.cleanup()
    exit()
