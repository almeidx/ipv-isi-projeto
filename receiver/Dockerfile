FROM python

WORKDIR /app

COPY requirements.txt receiver.py ./
RUN pip install -r requirements.txt

CMD [ "python3", "receiver.py" ]
