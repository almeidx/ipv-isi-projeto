FROM python AS deps

ARG SENSOR_TYPE

RUN test -n "$SENSOR_TYPE"

ENV SENSOR_TYPE=$SENSOR_TYPE

WORKDIR /app

COPY requirements.txt sensor.py ./
RUN pip install -r requirements.txt

CMD [ "python3", "sensor.py" ]
