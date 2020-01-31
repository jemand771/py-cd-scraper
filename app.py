import json
import time

from scraper import Scraper


def main():

    worker = Scraper(False)

    with open("credentials/campusdual.json") as json_file:
        data = json.load(json_file)
        login = worker.login(data["username"], data["password"])
        print("login result", login)
        if login != 0:
            worker.exit()
            exit()

    worker.download_documents()

    worker.logout()
    worker.exit()


if __name__ == "__main__":
    main()
