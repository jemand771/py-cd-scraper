import json
import threading
import time

from scraper import Scraper
import deamon_calendar


CALENDAR_SYNC_SLEEP = 60 * 15  # every 15 minutes


def main():

    sync_thread = threading.Thread(target=deamon_calendar.run_loop, args=(CALENDAR_SYNC_SLEEP,))
    sync_thread.start()

    print("startup complete")
    return

    json_file = open("config/campusdual.json")
    data = json.load(json_file)
    username = data["username"]
    password = data["password"]

    worker = Scraper(username)
    login = worker.login(password)
    print("login result", login)
    if login != 0:
        worker.exit()
        exit()

    # TODO implement multiprocessing
    # worker.download_documents()
    # worker.download_timeline()
    # worker.download_full_schedule()
    # worker.download_general()

    print("worker is done, exiting")
    worker.logout()
    worker.exit()


if __name__ == "__main__":
    main()
