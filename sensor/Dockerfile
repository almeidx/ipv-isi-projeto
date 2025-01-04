FROM python:3.13

ARG SENSOR_TYPE
ARG SENSOR_ID

RUN test -n "$SENSOR_TYPE"
RUN test -n "$SENSOR_ID"

ENV SENSOR_TYPE=$SENSOR_TYPE
ENV SENSOR_ID=$SENSOR_ID

WORKDIR /app

COPY requirements.txt sensor.py ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

CMD [ "python3", "sensor.py" ]
