import os
from time import sleep
import pika
import json

print(' [*] Sending messages. Press CTRL+C to exit')

credentials = pika.PlainCredentials(
    os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq', credentials=credentials)
)

channel = connection.channel()
channel.queue_declare(queue='sensor_data')

channel.basic_publish(
    exchange='', routing_key='sensor_data', body='Hello World!')
print(" [x] Sent 'Hello World!'")

try:
    while True:
        sensor_data = json.dumps({"temperature": 25, "humidity": 50})

        channel.basic_publish(
            exchange='', routing_key='sensor_data', body=sensor_data)
        print(f" [x] Sent sensor data")
        sleep(100)
except KeyboardInterrupt:
    print("Closing connection...")
    connection.close()
