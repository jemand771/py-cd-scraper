FROM python:3

COPY *.py /

CMD [ "python", "app.py" ]