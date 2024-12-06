FROM python

WORKDIR /app

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY grapher.py ./

CMD [ "streamlit", "run", "grapher.py" ]
