#!/usr/bin/env python3.8

import datetime
from rq import Queue
from redis import Redis
from pprint import PrettyPrinter
from worker import worker
from influxdb import InfluxDBClient

q = Queue(connection=Redis())
pp = PrettyPrinter(indent=4)

left_client = InfluxDBClient(host='old.d.p.r.c', port=8086)
right_client = InfluxDBClient(host='new.d.p.r.c', port=8086)

now = datetime.datetime.today()

left_client.switch_database("test")
right_client.switch_database("test")

measurements = left_client.query("SHOW MEASUREMENTS")
for meas in measurements.get_points():
    m_name = meas['name']

    for h in range(0, 23):
        for d in range(1, 25):
            obj = {
                "date": f"2020-05-{d:02}",
                "hour": h,
                "m_name": m_name
            }
            print(f"Enqueing job for: {obj['date']} / {h} / {m_name}")
            q.enqueue(worker, obj, result_ttl=0)

