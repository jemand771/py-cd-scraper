FROM python:3

# install chromium browser
RUN \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    chromium \
    && \
    apt-get clean

# download + install chromedriver
RUN CHROMEVER=$(chromium --product-version | grep -o "[^\.]*\.[^\.]*\.[^\.]*") && \
    DRIVERVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROMEVER") && \
    wget -O /tmp/driver.zip https://chromedriver.storage.googleapis.com/$DRIVERVER/chromedriver_linux64.zip
RUN unzip /tmp/driver.zip
RUN mv chromedriver /bin/chromedriver

# install pip packages
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

# TODO create app dir
# TODO maybe run as non-root user
COPY *.py /

CMD [ "python", "app.py" ]