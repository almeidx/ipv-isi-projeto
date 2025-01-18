import os
import json
from datetime import datetime
import pika
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

QUEUE_NAME = 'sensor_data'
TABLE_NAME = 'sensor_data'

connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    host=os.getenv('POSTGRES_HOST'),
    database=os.getenv('POSTGRES_DB'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASS')
)


@contextmanager
def get_db_connection():
    conn = connection_pool.getconn()
    try:
        yield conn
    finally:
        connection_pool.putconn(conn)


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sensor_id SMALLINT,
                    sensor_type TEXT,
                    value REAL
                )
            ''')
            conn.commit()


def callback(ch, method, _properties, body):
    try:
        data = json.loads(body)

        sensor_id = data['sensor_id']
        sensor_type = data['sensor_type']
        value = data['value']
        timestamp = datetime.now().isoformat()

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'''
                    INSERT INTO {TABLE_NAME} (timestamp, sensor_id, sensor_type, value)
                    VALUES (%s, %s, %s, %s)
                ''', (timestamp, sensor_id, sensor_type, value))
                conn.commit()

        print(f"[{timestamp}] Recorded data from sensor {sensor_id} ({sensor_type}): {value}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    init_db()

    credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST'), credentials=credentials)
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print(f"Starting consumer. Saving data to PostgreSQL")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down consumer...")
        channel.stop_consuming()
    finally:
        connection.close()
        connection_pool.closeall()


if __name__ == "__main__":
    main()
