import psycopg2
import matplotlib.pyplot as plt
import os
from datetime import datetime

DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASS')
}
TABLE_NAME = 'sensor_data'
OUTPUT_DIR = 'graphs'


def generate_graphs():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    conn = psycopg2.connect(**DB_PARAMS)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT DISTINCT sensor_type FROM {TABLE_NAME}')
            sensor_types = cursor.fetchall()

            for sensor in sensor_types:
                sensor_type = sensor[0]

                cursor.execute(f'''
                    SELECT timestamp, value
                    FROM {TABLE_NAME}
                    WHERE sensor_type = %s
                    ORDER BY timestamp
                ''', (sensor_type,))

                data = cursor.fetchall()

                if data:
                    timestamps = [datetime.fromisoformat(
                        str(ts[0])) for ts in data]
                    values = [float(value[1]) for value in data]

                    plt.figure(figsize=(10, 5))
                    plt.plot(timestamps, values, marker='o')
                    plt.xlabel('Timestamp')
                    plt.ylabel('Value')
                    plt.title(f'Sensor Type: {sensor_type}')
                    plt.xticks(rotation=45)
                    plt.gcf().autofmt_xdate()
                    plt.tight_layout()

                    graph_path = os.path.join(
                        OUTPUT_DIR, f'{sensor_type}_graph.png')
                    plt.savefig(graph_path)
                    plt.close()

                    print(f'Graph saved: {graph_path}')
                else:
                    print(f'No data for sensor type: {sensor_type}')

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()


if __name__ == '__main__':
    generate_graphs()
