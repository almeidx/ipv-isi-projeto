FROM python

WORKDIR /app

COPY requirements.txt grapher.py ./

RUN pip install -r requirements.txt

CMD [ "python3", "grapher.py" ]
