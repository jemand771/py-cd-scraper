import json
import time

import schedule_fixer
import calendar_api
from scraper import Scraper
from kill_helper import GracefulKiller


FORBIDDEN_DATES = ["2020-04-" + str(i).zfill(2) for i in list(range(6, 11)) + list(range(13, 18)) + list(range(20, 25)) + list(range(27, 31))] + ["2020-05-01"]


class CalendarDeamon:

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

        worker = Scraper(username)
        login = worker.login(password)
        print("login result", login)
        if login != 0:
            worker.exit()
            exit(login)
        
        if self.killer.kill_now:
            print("login successful, but program is being terminated. not downloading schedule. NOT pushing to calendar. exiting")
            exit()

        worker.download_full_schedule()
        schedule_fixer.repair("data/" + username + "/schedule.json", "data/" + username + "/schedule-fixed.json")

        if self.killer.kill_now:
            print("download completed, but program is being terminated. NOT pushing to calendar. exiting")
            exit()

        calendar = calendar_api.CalendarApi()
        f = open("data/" + username + "/schedule-fixed.json", "r")
        sch = json.load(f)
        f.close()
        calendar.sync_schedule([s for s in sch if s["date"] not in FORBIDDEN_DATES])

    def __init__(self):
        
        self.killer = GracefulKiller()
