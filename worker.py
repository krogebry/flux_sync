from influxdb import InfluxDBClient
from pprint import PrettyPrinter


def worker(object):
    pp = PrettyPrinter(indent=4)
    pp.pprint(object)

    limit = 10000
    offset = 0

    left_client = InfluxDBClient(host='old.d.p.r.c', port=8086)
    right_client = InfluxDBClient(host='new.d.p.r.c', port=8086)

    left_client.switch_database("test")
    right_client.switch_database("test")

    date = object['date']
    hour = object['hour']
    m_name = object['m_name']

    running = True

    while running:
        query = f"select * from {m_name} " \
                f"where time > '{date}T{hour}:00:00Z' " \
                f"and time < '{date}T{hour}:59:59Z' " \
                f"limit {limit} offset {offset} "
        print(f"Query: {query}")
        results = left_client.query(query)
        points = results.get_points()
        buffer = []

        for point in points:
            buffer.append({
                "measurement": m_name,
                "time": point.pop('time'),
                "fields": point
            })

        print(f"Writing points for: {m_name} hour: {hour} / {len(buffer)}")
        right_client.write_points(buffer)
        print(f"Buffer: {len(buffer)} / {offset}")

        if len(buffer) < limit:
            running = False
        else:
            offset += limit

        buffer = []

    right_client.close()
    left_client.close()

    print(f"Done writing points for: {m_name} hour: {hour} / {len(buffer)}")

