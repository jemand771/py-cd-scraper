from datetime import datetime
import json
import os
import time

import requests

import schedule_fixer
import calendar_api
from scraper import Scraper
from kill_helper import GracefulKiller


class ExamDeamon:

    def run_loop(self, sleeps):

        while True:
            self.run_once()
            print("sync sleeping for", sleeps, "seconds")
            for i in range(sleeps):
                if self.killer.kill_now:
                    print("shutdown event received during sleep, exiting")
                    exit()
                time.sleep(1)

    def run_once(self):

        json_file = open("config/campusdual.json")
        data = json.load(json_file)
        username = data["username"]
        password = data["password"]

        with open("config/discord.json") as f:
            js = json.load(f)
            self.hook = js["hook"]

        worker = Scraper(username)
        login = worker.login(password)
        print("login result", login)
        if login != 0:
            worker.exit()
            exit(login)
        
        if self.killer.kill_now:
            print("login successful, but program is being terminated. not downloading schedule. NOT notifying discord. exiting")
            exit()

        if self.killer.kill_now:
            print("download completed, but program is being terminated. NOT notifying discord. exiting")
            exit()

        tempfile = "config/temp.json"
        if not os.path.exists(tempfile):
            with open(tempfile, "w+") as f:
                json.dump([], f)

        with open(tempfile) as f:
            known = json.load(f)
        results = worker.download_exam_results(False)
        ex_nicks_results = [group["title"] + " /" + exam["title"] + " [" + exam["period"] + "]" for group in
                            results for exam in group["exams"]]
        new_results = [x for x in ex_nicks_results if x not in known]
        print(new_results)
        if new_results:

            self.send_discord_notification(None, new_results)
            with open(tempfile, "w") as f:
                json.dump(known + new_results, f, indent=2)
            return

        print("nothing new, going to sleep")

    def send_discord_notification(self, available, results):
        message = "beep-boop! "
        message += str(len(results)) + " new exam result(s) are available:\n```\n"
        message += "\n".join(results + ["```"])

        dt = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
        message += "\n(this message was generated on " + dt + " server time)"
        requests.post(self.hook, json={"content": message})

    def __init__(self):
        
        self.killer = GracefulKiller()
        self.hook = ""
