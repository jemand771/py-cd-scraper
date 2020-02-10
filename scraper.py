import filecmp
import hashlib
import json
import os
from pathlib import Path
import requests
import shutil
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from tika import parser

import schedule_fixer


# general settings go here
STATUS_CAMPUSDUAL_ERROR = -1
STATUS_INCORRECT_PASSWORD = 1
STATUS_OK = 0
TEXT_INCORRECT_PASSWORD = "Mandant, Name oder Kennwort ist nicht korrekt. Anmeldung wiederholen"
BASE_URL = "https://selfservice.campus-dual.de"
BASE_URL_ERP = "https://erp.campus-dual.de"
WAIT_DOWNLOAD = 5
WAIT_IMPLICIT = 3


class Scraper:

    # run specific variables and settings go here
    driver = None
    USERNAME = None
    PASSWORD = None
    HEADLESS = None
    TEMP_DIR = "./tmp"
    DATA_DIR = "./data"

    # TODO maybe create a login decorator for all scrape cases, ensuring that the user is logged in before data is fetched
    def login(self, password):
        
        self.PASSWORD = password
        login_url = BASE_URL + "/index/login"
        self.driver.get(login_url)

        # cancel if not redirected
        if self.driver.current_url == login_url:
            print("auto-redirect doesn't seem to be working")
            return STATUS_CAMPUSDUAL_ERROR

        self.driver.find_element_by_id("sap-user").send_keys(self.USERNAME)
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

    def download_exam_results(self, write_file=True):

        self.go("/acwork/index")
        
        modules = []
        lastmod = None
        rows = self.driver.find_elements_by_css_selector("table#acwork tbody tr")
        for row in rows:
            cols = row.find_elements_by_css_selector("td")
            # TODO select mode from number of cols
            

    def download_general(self, write_file=True):

        self.go("/index/login")

        header = self.driver.find_element_by_css_selector("div#header")
        uni_name = header.find_element_by_css_selector("h3 a").text
        stinfo = header.find_element_by_css_selector("div#studinfo table tbody tr td").get_attribute("innerHTML")

        fullname = stinfo.split(" (")[0].split("</strong>")[1]
        group = stinfo.split("</strong>")[2].split("<br>")[0].strip(" ")
        subject = stinfo.split("<br>")[1].strip(" ").strip("\n").strip(" ")

        data = {
            "uni_name": uni_name,
            "student": {
                "firstname": fullname.split(", ")[1],
                "lastname": fullname.split(", ")[0],
                "matnum": self.USERNAME,
                "group": group
            },
            "subject": subject
        }

        if write_file:
            file = open(self.DATA_DIR + 'general.json', 'w')
            json.dump(data, file)
            file.close()

    def download_documents(self):

        def get_doclist():

            self.go("/doc/download")
            # find iframe, then visit iframe page
            iframe = self.driver.find_element_by_css_selector("iframe")
            self.driver.get(iframe.get_attribute("src"))
            
            return self.driver.find_elements_by_css_selector("img[title='Anlage']")

        doclist = get_doclist()
        
        for i in range(len(doclist)):
            if i != 3: continue
            # clean up before downloading
            try:
                os.remove(self.TEMP_DIR + "/Form.pdf")
            except FileNotFoundError:
                pass
            doc = get_doclist()[i]
            parent = doc.find_element_by_xpath("../..")
            link = parent.find_element_by_css_selector("a")
            doctitle = link.text
            link.click()
            time.sleep(5)  # with 3 seconds, this sometimes crashed. # TODO investigate
            xmp = self.driver.find_element_by_css_selector("xmp")
            src = xmp.get_attribute("innerHTML").split("iframe")[1].split("src=\"")[1].split("\"")[0]
            # TODO maybe implement a nicer way of doing this
            src = src.replace("&#x2f;", "/")
            src = src.replace("&#x7e;", "~")
            src = src.replace("&#x3f;", "?")
            src = src.replace("&#x3d;", "=")
            src = src.replace("&#x25;", "%")
            src = src.replace("&amp;", "&")
            print(doctitle)

            self.driver.get(BASE_URL_ERP + src)
            time.sleep(WAIT_DOWNLOAD)  # wait for file to download

            do_copy = False
            infile = self.TEMP_DIR + "Form.pdf"
            outfile = self.DATA_DIR + doctitle + ".pdf"
            try:
                text1 = parser.from_file(infile)["content"]
                text2 = parser.from_file(outfile)["content"]
                if text1 != text2:
                    do_copy = True
            except FileNotFoundError:
                print(doctitle + ".pdf not found, writing new")
                do_copy = True
            if do_copy:
                shutil.copyfile(self.TEMP_DIR + "Form.pdf", self.DATA_DIR + doctitle + ".pdf")
                print("updated", doctitle)
            else:
                print(doctitle, "hasn't changed, not replacing")

    def download_timeline(self, write_file=True):
        """
        download the timeline, consisting of 6 "FS"
        each divided into "Theorie" and "Praxis"
        Dates saved as raw DD.MM.YYYY
        """
        
        self.go("/dash/timeline")
        alltapes = self.driver.find_elements_by_css_selector("div.timeline-event-tape")
        alllabels = self.driver.find_elements_by_css_selector("div.timeline-event-label")
        if len(alllabels) != len(alltapes):
            print("error! number of tapes does not match number of labels")
            return -1
        semesters = list()
        currsemester = None
        theory = True
        for i in reversed(range(len(alltapes))):
            tape = alltapes[i]
            label = alllabels[i]
            dates = tape.get_attribute("title")
            
            start = dates.split(" ")[0]
            end = dates.split(" ")[2]

            sp = label.text.split(" ")
            if len(sp) == 2:
                if sp[1] == "FS":
                    # start of a new semester, save old one (except for first)
                    if sp[0] != "1.":
                        semesters.append(currsemester)
                    else:
                        if currsemester is not None:
                            semesters.append(currsemester)
                            break
                    currsemester = dict()
                    currsemester["start"] = start
                    currsemester["end"] = end
            else:
                if label.text not in ("Praxis", "Theorie", ""):
                    print("error parsing phases")
                    return None
                if theory:
                    if start != currsemester["start"]:
                        print("something seems to be wrong:", start, "does not equal", currsemester["start"])
                    currsemester["tend"] = end
                else:
                    if end != currsemester["end"]:
                        print("something seems to be wrong:", end, "does not equal", currsemester["end"])
                    currsemester["pstart"] = start
                theory = not theory
        
        if write_file:
            file = open(self.DATA_DIR + 'blocks.json', 'w')
            json.dump(semesters, file)
            file.close()

    def download_full_schedule(self):

        self.go("/room/index")
        maindiv = self.driver.find_element_by_css_selector("div#main")
        script = maindiv.find_element_by_css_selector("script")
        js = script.get_attribute("innerHTML")
        lines = js.split("\n")
        api_hash = None
        for line in lines:
            if not "hash=\"" in line:
                continue
            if api_hash is not None:
                print("ERROR: unsure on which hash to choose")
                return
            api_hash = line.split("\"")[1]
        lessons = list()

        url = BASE_URL + "/room/json?userid=" + self.USERNAME + "&hash=" + api_hash
        r = requests.get(url, verify=False)
        if r.status_code != 200:
            print("error querrying json api!")
            return
        file = open(self.DATA_DIR + "schedule.json", 'w')
        json.dump(r.json(), file)
        file.close()
        schedule_fixer.repair(self.DATA_DIR + "schedule.json", self.DATA_DIR + "schedule-fixed.json")

    def __init__(self, username, headless=True):
        
        self.HEADLESS = headless
        self.USERNAME = username
        self.TEMP_DIR = self.TEMP_DIR.replace(".", os.path.dirname(os.path.realpath(__file__))) + "/" + username + "/"
        self.DATA_DIR = self.DATA_DIR.replace(".", os.path.dirname(os.path.realpath(__file__))) + "/" + username + "/"
        print(self.TEMP_DIR, self.DATA_DIR)
        Path(self.TEMP_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        prefs = {"download.default_directory": self.TEMP_DIR,
            "plugins.always_open_pdf_externally" : True}
        chrome_options.add_experimental_option("prefs", prefs)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(1920, 1080)
        self.driver.implicitly_wait(WAIT_IMPLICIT)
