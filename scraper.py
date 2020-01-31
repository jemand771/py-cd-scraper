import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


STATUS_CAMPUSDUAL_ERROR = -1
STATUS_INCORRECT_PASSWORD = 1
STATUS_OK = 0
TEXT_INCORRECT_PASSWORD = "Mandant, Name oder Kennwort ist nicht korrekt. Anmeldung wiederholen"
BASE_URL = "https://selfservice.campus-dual.de"
DOWNLOADS_FOLDER = "download"


class Scraper():

    driver = None


    def login(self, username, password):
        
        login_url = BASE_URL + "/index/login"
        self.driver.get(login_url)

        # cancel if not redirected
        if(self.driver.current_url == login_url):
            print("auto-redirect doesn't seem to be working")
            return STATUS_CAMPUSDUAL_ERROR

        self.driver.find_element_by_id("sap-user").send_keys(username)
        self.driver.find_element_by_id("sap-password").send_keys(password)
        self.driver.find_element_by_id("LOGON_BUTTON").click()

        # wait for redirect to initial page
        for _ in range(10):
            if(self.driver.current_url == login_url):
                print("login complete, page might be ready now")
                return STATUS_OK
            print("not ready yet")

        err_msg = self.driver.find_element_by_id("m1-txt")
        if err_msg.text == TEXT_INCORRECT_PASSWORD:
            print("username/password combo incorrect")
            return STATUS_INCORRECT_PASSWORD

        return STATUS_CAMPUSDUAL_ERROR


    def logout(self):

        self.go("/index/logout")


    def exit(self):

        self.driver.close()


    def go(self, url):

        self.driver.get(BASE_URL + url)

    
    def download_documents(self):

        self.go("/doc/download")
        # find iframe, then visit iframe page
        iframe = self.driver.find_element_by_css_selector("iframe")
        self.driver.get(iframe.get_attribute("src"))
        
        doclist = self.driver.find_elements_by_css_selector("img[title='Anlage']")
        for doc in doclist:
            parent = doc.find_element_by_xpath("../..")
            link = parent.find_element_by_css_selector("a")
            print(link.text)
    

    def __init__(self, headless=True):

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        self.driver.implicitly_wait(3)
