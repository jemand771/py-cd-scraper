FROM python:3

# TODO create app dir
# TODO maybe run as non-root user
COPY *.py /
# TODO find a better file location for this
COPY dozent.json /

# install pip packages
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# install chromium browser
RUN apt-get update
RUN apt-get install -y chromium

# download + install chromedriver
RUN wget -O /tmp/driver.zip https://chromedriver.storage.googleapis.com/79.0.3945.36/chromedriver_linux64.zip
RUN unzip /tmp/driver.zip
RUN mv chromedriver /bin/chromedriver

CMD [ "python", "app.py" ]