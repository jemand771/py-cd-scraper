FROM python:3

# TODO create app dir
# TODO maybe run as non-root user
COPY *.py /

# install pip packages
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

CMD [ "python", "app.py" ]