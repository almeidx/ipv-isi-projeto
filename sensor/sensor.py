import os
from time import sleep
import pika
import json
import numpy as np

QUEUE_NAME = 'sensor_data'


def generate_sensor_value(sensor_id: int, sensor_type: str):
    previous_value = None

    while True:
        trend_factor = np.random.normal(0, 0.1)
        noise_factor = np.random.normal(0, 5)

        if sensor_type == 'temperature':
            if previous_value is None:
                new_value = 20
            else:
                new_value = previous_value + trend_factor + noise_factor

            new_value = np.clip(new_value, -10, 50)
        elif sensor_type == 'gas':
            if previous_value is None:
                new_value = 100
            else:
                new_value = previous_value + trend_factor + noise_factor

            new_value = np.clip(new_value, 0, 1000)
        elif sensor_type == 'smoke':
            if previous_value is None:
                new_value = 4
            else:
                new_value = previous_value + trend_factor + noise_factor

            new_value = np.clip(new_value, 0, 5)
        else:
            raise ValueError(f"Invalid sensor type: {sensor_type}")

        previous_value = new_value

        sensor_data = {
            'value': float(new_value),
            'sensor_id': sensor_id,
            'sensor_type': sensor_type
        }

        credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST'), credentials=credentials)
        )
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME)
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=json.dumps(sensor_data))

        print(f"Sent sensor data: {sensor_data}")
        connection.close()

        sleep(0.1)


def main():
    sensor_id = int(os.getenv('SENSOR_ID'))
    sensor_type = os.getenv('SENSOR_TYPE')

    if sensor_type not in ['temperature', 'gas', 'smoke']:
        raise ValueError('Invalid sensor type. Must be one of: temperature, gas, or smoke')

    generate_sensor_value(sensor_id, sensor_type)


if __name__ == '__main__':
    main()
