import json

import schedule_fixer
import calendar_api
from scraper import Scraper


def run_once():

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

    worker.download_full_schedule()
    schedule_fixer.repair("data/" + username + "/schedule.json", "data/" + username + "/schedule-fixed.json")

    calendar = calendar_api.CalendarApi()
    f = open("data/" + username + "/schedule-fixed.json", "r")
    sch = json.load(f)
    f.close()
    calendar.sync_schedule(sch)

if __name__ == "__main__":
    run_once()