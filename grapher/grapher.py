import os
import psycopg2
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objs as go

DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASS')
}
TABLE_NAME = 'sensor_data'

UNIT_MAPPING = {
    "temperature": "°C",
    "smoke": "V",
    "gas": "ppm"
}

VALUE_THRESHOLDS = {
    "temperature": 30,
    "smoke": 5,
    "gas": 100
}


def fetch_sensor_data():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT DISTINCT sensor_type, sensor_id FROM {TABLE_NAME}')
            results = cursor.fetchall()

            sensor_types = sorted(set(result[0] for result in results))
            sensor_ids = {
                sensor_type: sorted(
                    set(result[1] for result in results if result[0] == sensor_type)
                ) for sensor_type in sensor_types
            }

            return sensor_types, sensor_ids, conn
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        return [], {}, None


def load_data(selected_sensor_type, selected_sensor_ids, timeframe, conn):
    if not selected_sensor_ids:
        st.warning("No sensor IDs selected")
        return None

    with conn.cursor() as cursor:
        start_time = datetime.now() - pd.Timedelta(hours=timeframe)

        query = f'''
            SELECT timestamp, value, sensor_id
            FROM {TABLE_NAME}
            WHERE sensor_type = %s AND sensor_id IN %s AND timestamp > %s
            ORDER BY timestamp
        '''

        cursor.execute(query, (selected_sensor_type, tuple(selected_sensor_ids), start_time))

        data = cursor.fetchall()

        if data:
            df = pd.DataFrame(data, columns=['timestamp', 'value', 'sensor_id'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            st.warning(f"No data for sensor type: {selected_sensor_type}")
            return None


def plot_multi_sensor_line(df, selected_sensor_type):
    if df is None or df.empty:
        st.warning("No data to plot")
        return

    unit = UNIT_MAPPING.get(selected_sensor_type, "")

    fig = px.line(df, x='timestamp', y='value', color='sensor_id',
                  title=f'{selected_sensor_type.capitalize()} Sensor Data',
                  labels={'value': f'Value ({unit})', 'timestamp': 'Timestamp'})

    fig.update_layout(xaxis_title='Timestamp', yaxis_title=f'Value ({unit})', legend_title='Sensor ID')

    st.plotly_chart(fig)


def plot_moving_average(df, selected_sensor_type):
    unit = UNIT_MAPPING.get(selected_sensor_type, "")

    df_ma = df.groupby('sensor_id').apply(
        lambda x: x.assign(moving_average=x['value'].rolling(window=5).mean())
    ).reset_index(drop=True)

    fig = go.Figure()

    for sensor_id in df['sensor_id'].unique():
        sensor_data = df_ma[df_ma['sensor_id'] == sensor_id]

        fig.add_trace(go.Scatter(
            x=sensor_data['timestamp'],
            y=sensor_data['value'],
            mode='lines',
            name=f'Sensor {sensor_id} - Raw'
        ))

        fig.add_trace(go.Scatter(
            x=sensor_data['timestamp'],
            y=sensor_data['moving_average'],
            mode='lines',
            name=f'Sensor {sensor_id} - Moving Avg',
            line=dict(dash='dot')
        ))

    fig.update_layout(
        title='Moving Average',
        xaxis_title='Timestamp',
        yaxis_title=f'Value ({unit})',
        legend_title='Sensor Data'
    )

    st.plotly_chart(fig)


def plot_distribution(df, selected_sensor_type):
    unit = UNIT_MAPPING.get(selected_sensor_type, "")
    st.subheader('Grouped Value Distribution')

    distribution_data = []
    for sensor_id in df['sensor_id'].unique():
        sensor_df = df[df['sensor_id'] == sensor_id]

        bin_edges = np.arange(sensor_df['value'].min(), sensor_df['value'].max() + 0.25, 0.25)
        sensor_df['binned_value'] = pd.cut(sensor_df['value'], bins=bin_edges)

        binned_counts = sensor_df['binned_value'].value_counts().sort_index()
        binned_counts.index = binned_counts.index.astype(str)

        for bin_range, count in binned_counts.items():
            distribution_data.append({
                'Sensor ID': sensor_id,
                'Bin': bin_range,
                'Count': count
            })

    dist_df = pd.DataFrame(distribution_data)
    fig = px.bar(dist_df, x='Bin', y='Count', color='Sensor ID', title='Value Distribution by Sensor')

    fig.update_layout(
        xaxis_title=f'Value Intervals ({unit})',
        yaxis_title='Count',
        legend_title='Sensor ID'
    )

    st.plotly_chart(fig)


def main():
    st.title("Sensor Data Graph Viewer")

    sidebar = st.sidebar.radio("Escolha a Aba", ["Gráficos", "Notificações"])

    if sidebar == "Gráficos":
        sensor_types, sensor_ids, conn = fetch_sensor_data()

        if not sensor_types:
            st.warning("No sensor data available or unable to connect to the database.")
            return

        selected_sensor = st.sidebar.selectbox("Select Sensor Type", sensor_types)

        available_sensor_ids = sensor_ids.get(selected_sensor, [])
        selected_sensor_ids = st.sidebar.multiselect(
            f"Select {selected_sensor} Sensor IDs",
            available_sensor_ids,
            default=available_sensor_ids
        )

        default_timeframe = 6
        timeframe = st.sidebar.slider(
            "Select Timeframe (hours)",
            min_value=1,
            max_value=48,
            value=default_timeframe,
            step=1,
            format="%d hours"
        )

        st.sidebar.write(f"Showing data for the last {timeframe} hours.")

        if conn:
            df = load_data(selected_sensor, selected_sensor_ids, timeframe, conn)

            if df is not None:
                plot_multi_sensor_line(df, selected_sensor)
                plot_moving_average(df, selected_sensor)
                plot_distribution(df, selected_sensor)

            conn.close()

    elif sidebar == "Notificações":
        st.subheader("Notificações de Limite de Sensor")

        sensor_types, sensor_ids, conn = fetch_sensor_data()

        if not sensor_types:
            st.warning("No sensor data available or unable to connect to the database.")
            return

        selected_sensor = st.selectbox("Selecione o tipo de sensor", sensor_types)

        available_sensor_ids = sensor_ids.get(selected_sensor, [])
        selected_sensor_ids = st.multiselect(
            f"Select {selected_sensor} Sensor IDs",
            available_sensor_ids,
            default=available_sensor_ids
        )

        if conn:
            df = load_data(selected_sensor, selected_sensor_ids, timeframe=6, conn=conn)

            if df is not None:
                threshold = VALUE_THRESHOLDS.get(selected_sensor, float('inf'))
                direction = 'acima' if selected_sensor != 'smoke' else 'abaixo'
                exceeding_values = df[df['value'] > threshold if direction == 'acima' else df['value'] < threshold]

                if not exceeding_values.empty:
                    st.write(f"**Notificação**: Valores {direction} do limite de {threshold}")
                    st.dataframe(exceeding_values)
                else:
                    st.write("Nenhum valor ultrapassou o limite.")

            conn.close()


if __name__ == '__main__':
    main()
