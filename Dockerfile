FROM python:3

# install chromium browser
RUN apt-get update
RUN apt-get install -y chromium

# download + install chromedriver
RUN wget -O /tmp/driver.zip https://chromedriver.storage.googleapis.com/83.0.4103.39/chromedriver_linux64.zip
RUN unzip /tmp/driver.zip
RUN mv chromedriver /bin/chromedriver

# install pip packages
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# TODO create app dir
# TODO maybe run as non-root user
COPY *.py /

CMD [ "python", "app.py" ]