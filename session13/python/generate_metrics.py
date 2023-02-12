# pip install psycopg2

import psycopg2
from datetime import datetime
import decimal, time, random

def write_to_db(data):

    try:
        connection = psycopg2.connect(user="jb",
                                      password="jb",
                                      host="127.0.0.1",
                                      port="5432",
                                      database="jb")
        cursor = connection.cursor()
        insert_query = """ insert into sensor_telemetry (datetime, device_id, metric, reading) values
        (%s, %s, %s, %s) """
        cursor.execute(insert_query, (datetime.now(), data.get("device"), data.get("metric"),
                                          data.get("reading")))
        connection.commit()

    except (Exception, psycopg2.Error) as error:
        print("PROBLEMS: ", error)

    finally:
        if connection:
            cursor.close()
            connection.close()


while True :
    for x in range(0,14):
        for y in range (0,6):
            write_to_db({ "device" : x, "metric" :'M-' + str(y), "reading": decimal.Decimal(random.randrange(10, 1389))})
time.sleep(5)
