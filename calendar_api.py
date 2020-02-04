from __future__ import print_function
import datetime
import json
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarApi:

    service = None
    CAL_ID = None

    def sync_schedule(self, schedule):

        print(schedule, self.CAL_ID)

    def __init__(self):
        
        creds = None
        if os.path.exists('config/calendar-token.pickle'):
            with open('config/calendar-token.pickle', 'rb') as token:
                creds = pickle.load(token)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'config/calendar-api.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('config/calendar-token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)

        f = open("config/calendar.json")
        cid = json.load(f)["cal_id"]
        self.CAL_ID = cid if cid is not None else "primary"
