import json
import time

from scraper import Scraper


def main():

    

    json_file = open("credentials/campusdual.json")
    data = json.load(json_file)

    worker = Scraper(data["username"], False)
    login = worker.login(data["password"])
    print("login result", login)
    if login != 0:
        worker.exit()
        exit()

    worker.download_documents()

    print("worker is done, exiting")
    worker.logout()
    worker.exit()


if __name__ == "__main__":
    main()
