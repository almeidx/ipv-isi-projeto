FROM python

WORKDIR /app

COPY requirements.txt receiver.py ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

CMD [ "python3", "receiver.py" ]
