import json
import time

from scraper import Scraper


def main():

    

    json_file = open("config/campusdual.json")
    data = json.load(json_file)
    username = data["username"]
    password = data["password"]

    worker = Scraper(username, False)
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
