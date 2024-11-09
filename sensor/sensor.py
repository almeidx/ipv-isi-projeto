import os
from time import sleep
import pika
import json
import numpy as np

QUEUE_NAME = 'sensor_data'


def generate_sensor_value(sensor_type: str):
    match sensor_type:
        case 'temperature':
            return np.random.normal(20, 5)
        case 'gas_concentration':
            return np.random.normal(100, 10)
        case 'humidity':
            return np.random.normal(50, 10)
        case _:
            raise ValueError('Invalid sensor type')


def main():
    sensor_type = os.getenv('SENSOR_TYPE')

    if sensor_type is None or sensor_type not in ['temperature', 'gas_concentration', 'humidity']:
        raise ValueError(
            'Invalid sensor type. Must be one of: temperature, gas_concentration, humidity'
        )

    credentials = pika.PlainCredentials(
        os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            credentials=credentials
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    try:
        while True:
            sensor_data = json.dumps({
                'value': generate_sensor_value(sensor_type),
                'sensor_type': sensor_type
            })

            channel.basic_publish(
                exchange='', routing_key=QUEUE_NAME, body=sensor_data)
            print(f"Sent sensor data", sensor_data)
            sleep(0.1)
    except KeyboardInterrupt:
        print("Closing connection...")
        connection.close()


if __name__ == '__main__':
    main()
