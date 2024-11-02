import os
import pika
import json

credentials = pika.PlainCredentials(
    os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
connection = pika.BlockingConnection(
    pika.ConnectionParameters(
        host='rabbitmq',
        credentials=credentials
    )
)

channel = connection.channel()
channel.queue_declare(queue='sensor_data')


def callback(ch, method, properties, body):
    try:
        # Try to parse as JSON
        data = json.loads(body)
        print(f" [x] Received sensor data: {data}")
    except json.JSONDecodeError:
        # Handle non-JSON messages
        print(f" [x] Received message: {body}")


channel.basic_consume(queue='sensor_data',
                      auto_ack=True,
                      on_message_callback=callback)

print(' [*] Waiting for messages. Press CTRL+C to exit')
try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("Closing connection...")
    connection.close()
