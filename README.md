# Project Overview

Practical project developed for the ISI (Integração em Sistemas Inteligentes) course at the Instituto Politécnico de Viseu.

## Project Structure

The project is organized into three main components, each in its own directory:

1. **Sensor**:
	- Simulates sensors generating data.
	- Publishes data to the message queue.

1. **Receiver**:
	- Subscribes to the message queue to consume sensor data.
	- Inserts the data into the database for persistence.

1. **Grapher**:
	- Serves as the frontend application.
	- Fetches data from the database and provides a visual representation.

## How to Run

This section provides instructions for running the project. The project uses Docker (version 27.0.3) for containerized deployment.

1. Pull required images:
	```
	docker compose pull
	```

1. Build the services:
	```
	docker compose build
	```

1. Start the simulators and receiver:
	```
	docker compose up -d sensor_temp_1 sensor_temp_2 sensor_gas_1 sensor_gas_2 sensor_smoke_1 sensor_smoke_2
	```

1. Start the frontend:
	```
	docker compose up grapher
	```

1. Access the application:

	After starting the frontend, a URL will be displayed. Open it in your browser to view the application.

