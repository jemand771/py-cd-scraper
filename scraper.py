import requests
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException


STATUS_CAMPUSDUAL_ERROR = -1
STATUS_INCORRECT_PASSWORD = 1
STATUS_OK = 0
TEXT_INCORRECT_PASSWORD = "Mandant, Name oder Kennwort ist nicht korrekt. Anmeldung wiederholen"
BASE_URL = "https://selfservice.campus-dual.de"
BASE_URL_ERP = "https://erp.campus-dual.de"
DOWNLOAD_PATH = "/home/willy/dl"  # TODO make this configurable
WAIT_DOWNLOAD = 5
WAIT_IMPLICIT = 3


class Scraper:

    driver = None

    def login(self, username, password):
        
        login_url = BASE_URL + "/index/login"
        self.driver.get(login_url)

        # cancel if not redirected
        if self.driver.current_url == login_url:
            print("auto-redirect doesn't seem to be working")
            return STATUS_CAMPUSDUAL_ERROR

        self.driver.find_element_by_id("sap-user").send_keys(username)
        self.driver.find_element_by_id("sap-password").send_keys(password)
        self.driver.find_element_by_id("LOGON_BUTTON").click()

        # wait for redirect to initial page
        for _ in range(10):
            if self.driver.current_url == login_url:
                print("login complete, page might be ready now")
                return STATUS_OK
            print("not ready yet")
            time.sleep(0.5)
        try:
            err_msg = self.driver.find_element_by_id("m1-txt")
            if err_msg.text == TEXT_INCORRECT_PASSWORD:
                print("username/password combo incorrect")
                return STATUS_INCORRECT_PASSWORD
        except NoSuchElementException:
            return STATUS_CAMPUSDUAL_ERROR

        return STATUS_CAMPUSDUAL_ERROR

    def logout(self):

        self.go("/index/logout")

    def exit(self):

        self.driver.close()

    def go(self, url):

        self.driver.get(BASE_URL + url)

    def download_documents(self):

        def get_doclist():

            self.go("/doc/download")
            # find iframe, then visit iframe page
            iframe = self.driver.find_element_by_css_selector("iframe")
            self.driver.get(iframe.get_attribute("src"))
            
            return self.driver.find_elements_by_css_selector("img[title='Anlage']")

        doclist = get_doclist()
        
        for i in range(len(doclist)):
            doc = get_doclist()[i]
            parent = doc.find_element_by_xpath("../..")
            link = parent.find_element_by_css_selector("a")
            link.click()
            time.sleep(3)
            xmp = self.driver.find_element_by_css_selector("xmp")
            src =xmp.get_attribute("innerHTML").split("iframe")[1].split("src=\"")[1].split("\"")[0]
            # TODO maybe implement a nicer way of doing this
            src = src.replace("&#x2f;", "/")
            src = src.replace("&#x7e;", "~")
            src = src.replace("&#x3f;", "?")
            src = src.replace("&#x3d;", "=")
            src = src.replace("&#x25;", "%")
            src = src.replace("&amp;", "&")
            print(link.text)

            self.driver.get(BASE_URL_ERP + src)
            time.sleep(WAIT_DOWNLOAD)  # wait for file to download
            # TODO move file from tmp path to somewhere sensible
            # TODO perform a file diff to check if anything has changed at all (and only if so, replace the file)

    def __init__(self, headless=True):

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        prefs = {"download.default_directory": DOWNLOAD_PATH,
            "plugins.always_open_pdf_externally" : True}
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        self.driver.implicitly_wait(WAIT_IMPLICIT)

