import os
import json
from datetime import datetime
import pika
import sqlite3
from pathlib import Path

QUEUE_NAME = 'sensor_data'
DB_FILE_PATH = '/app/db.sqlite3'
TABLE_NAME = 'sensor_data'

db_file = Path(DB_FILE_PATH)

if not db_file.exists():
    db_file.touch()


def init_db():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sensor_type TEXT,
            value REAL
        )
        ''')
        conn.commit()


def callback(ch, method, properties, body):
    try:
        data = json.loads(body)

        sensor_type = data['sensor_type']
        value = data['value']
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
            INSERT INTO {TABLE_NAME} (timestamp, sensor_type, value)
            VALUES (?, ?, ?)
            ''', (timestamp, sensor_type, value))
            conn.commit()

        print(f"Recorded data: {timestamp}, {sensor_type}, {value}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Error processing message: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    init_db()

    credentials = pika.PlainCredentials(
        os.getenv('RABBITMQ_USER'),
        os.getenv('RABBITMQ_PASS')
    )

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=os.getenv('RABBITMQ_HOST'),
            credentials=credentials
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print(f"Starting consumer. Saving data to {db_file}")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("Shutting down consumer...")
        channel.stop_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
