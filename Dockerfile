from python:alpine

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

COPY app /app

ENV API_URL=https://www.soliscloud.com:13333
ENV DO_AUTH=true
ENV RETRIES_ENABLED=true
ENV RETRY_DELAY=3

LABEL org.opencontainers.image.source https://github.com/bentasker/soliscloud-inverter-control

CMD /app/server.py
