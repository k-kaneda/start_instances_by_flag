# -*- coding: utf-8 -*-

from __future__ import print_function

import sys
import json
from datetime import date

import boto3
import requests
from icalendar import Calendar, Event

REGION_NAME = "us-west-2"
CALENDAR_URL = "https://calendar.google.com/calendar/ical/ja.japanese%23holiday%40group.v.calendar.google.com/public/basic.ics"
NTP_URL = "http://ntp-b1.nict.go.jp/cgi-bin/json"

print("Loading function")

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # 祝日判定処理
    ntpReq = requests.get(NTP_URL)
    ntp = json.loads(ntpReq.text)

    calReq = requests.get(CALENDAR_URL)
    cal = Calendar.from_ical(calReq.text)

    for ev in cal.walk():
        if ev.name == "VEVENT":
            start_dt = ev.decoded("dtstart")

            # 祝日なら処理終了
            if start_dt.strftime("%Y-%m-%d") == date.fromtimestamp(ntp["st"]).strftime("%Y-%m-%d"):
                print("It's a holiday today.")
                return

    # インスタンス起動処理
    ec2 = boto3.resource('ec2')

    instances = ec2.instances.filter(Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}])
    instance_list = list(instances.all())

    if len(instance_list) > 0:
        for instance in instances:
            for tag in instance.tags:
                # AutoStartタグがyesのインスタンスを起動
                if tag["Key"] == "AutoStart" and tag["Value"] == "yes":
                    instance.start()
                    print(instance.private_ip_address + " is started.")

    print("Instances are started.")
