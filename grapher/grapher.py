import os
import psycopg2
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Configuração do banco de dados
DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASS')
}
TABLE_NAME = 'sensor_data'

UNIT_MAPPING = {
    "temperature": "°C",
    "humidity": "%",
    "gas": "ppm"
}

# Limite para notificações
VALUE_THRESHOLD = 50  # Limite arbitrário para acionar uma notificação


def fetch_sensor_data():
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor() as cursor:
            cursor.execute(f'SELECT DISTINCT sensor_type FROM {TABLE_NAME}')
            sensor_types = [sensor[0] for sensor in cursor.fetchall()]
            return sensor_types, conn
    except psycopg2.Error as e:
        st.error(f"Database error: {e}")
        return [], None


def plot_moving_average(df, selected_sensor):
    unit = UNIT_MAPPING.get(selected_sensor, "")
    df['moving_average'] = df['value'].rolling(window=5).mean()
    st.subheader('Moving Average')
    st.line_chart(df.set_index('timestamp')[['value', 'moving_average']])

    st.write(f"Eixo Y: Valores de {unit}")


def plot_distribution(df, selected_sensor):
    unit = UNIT_MAPPING.get(selected_sensor, "")
    st.subheader('Grouped Value Distribution')

    # Agrupar os valores em intervalos de 0.25
    bin_edges = np.arange(df['value'].min(), df['value'].max() + 0.25, 0.25)
    df['binned_value'] = pd.cut(df['value'], bins=bin_edges)

    # Extrair os limites inferiores dos intervalos e contar as ocorrências
    binned_counts = df['binned_value'].value_counts().sort_index()

    # Converter os intervalos para valores numéricos (limite inferior de cada intervalo)
    binned_counts.index = binned_counts.index.astype(
        str)  # Convertendo para string para exibição

    # Exibir gráfico de barras
    st.bar_chart(binned_counts)

    st.write(f"Eixo Y: Contagem dos valores")
    st.write(f"Eixo X: Intervalos de valores ({unit})")


def plot_histogram(df, selected_sensor):
    unit = UNIT_MAPPING.get(selected_sensor, "")
    st.subheader('Histogram of Values')

    hist_df = df['value'].value_counts().reset_index()
    hist_df.columns = ['value', 'count']

    st.bar_chart(hist_df.set_index('value'))

    st.write(f"Eixo Y: Contagem dos valores")
    st.write(f"Eixo X: Valores ({unit})")


def load_data(selected_sensor, timeframe, conn):
    with conn.cursor() as cursor:
        # Calcular o tempo de início com base no intervalo selecionado
        start_time = datetime.now() - pd.Timedelta(hours=timeframe)

        cursor.execute(f'''
            SELECT timestamp, value
            FROM {TABLE_NAME}
            WHERE sensor_type = %s AND timestamp > %s
            ORDER BY timestamp
        ''', (selected_sensor, start_time))

        data = cursor.fetchall()

        if data:
            # Converter os dados para DataFrame para Streamlit
            df = pd.DataFrame(data, columns=['timestamp', 'value'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
        else:
            st.warning(f"No data for sensor type: {selected_sensor}")
            return None


def main():
    st.title("Sensor Data Graph Viewer")

    # Barra lateral de navegação
    sidebar = st.sidebar.radio(
        "Escolha a Aba",
        ["Gráficos", "Notificações"]
    )

    # Aba de Gráficos
    if sidebar == "Gráficos":
        # Buscar tipos de sensores do banco de dados
        sensor_types, conn = fetch_sensor_data()

        if not sensor_types:
            st.warning(
                "No sensor data available or unable to connect to the database.")
            return

        # Barra lateral: cada tipo de sensor como um item da barra lateral
        selected_sensor = st.sidebar.radio("Select Sensor Type", sensor_types)

        # Intervalo de tempo padrão em horas (exemplo: 6 horas)
        default_timeframe = 6

        # Barra lateral: slider para selecionar o intervalo de tempo, em horas
        timeframe = st.sidebar.slider(
            "Select Timeframe (hours)",
            min_value=1,
            max_value=48,
            value=default_timeframe,  # Definir o intervalo de tempo padrão como 6 horas
            step=1,
            format="%d hours"
        )

        # Exibir o intervalo de tempo selecionado
        st.sidebar.write(f"Showing data for the last {timeframe} hours.")

        # Carregar e exibir os dados automaticamente quando o usuário alterar o tipo de sensor ou o intervalo de tempo
        if conn:
            df = load_data(selected_sensor, timeframe, conn)

            if df is not None:
                # Gráficos adicionais
                plot_moving_average(df, selected_sensor)
                plot_distribution(df, selected_sensor)
                # plot_histogram(df)

            conn.close()

    # Aba de Notificações
    elif sidebar == "Notificações":
        # Procurar dados que ultrapassem o valor limite
        st.subheader("Notificações de Limite de Sensor")

        sensor_types, conn = fetch_sensor_data()

        if not sensor_types:
            st.warning(
                "No sensor data available or unable to connect to the database.")
            return

        # Escolher o tipo de sensor
        selected_sensor = st.selectbox(
            "Selecione o tipo de sensor", sensor_types)

        # Carregar dados
        if conn:
            df = load_data(selected_sensor, timeframe=6, conn=conn)

            if df is not None:
                # Verificar se algum valor ultrapassa o limite
                exceeding_values = df[df['value'] > VALUE_THRESHOLD]

                if not exceeding_values.empty:
                    st.write(
                        f"**Notificação**: O sensor {selected_sensor} tem valores acima do limite!")
                    st.write(f"Valores que ultrapassaram o limite de {
                             VALUE_THRESHOLD}:")
                    st.dataframe(exceeding_values)
                else:
                    st.write("Nenhum valor ultrapassou o limite.")

            conn.close()


if __name__ == '__main__':
    main()
