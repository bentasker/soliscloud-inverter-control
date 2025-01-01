from python

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY app /app

ENV API_URL=https://www.soliscloud.com:13333

CMD /app/server.py
