from python

COPY ../requirements.txt /requirements.txt

RUN pip install -f /requirements.txt \

COPY app /app
COPY ../soliscloud_control.py /app/

CMD /app/server.py

