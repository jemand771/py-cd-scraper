from __future__ import print_function
import datetime
import json
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

class CalendarApi:

    service = None
    CAL_ID = None

    def sync_schedule(self, schedule):

        calendar_events = self.get_all_calendar_events()
        to_add = self.get_events_to_add(schedule, calendar_events)
        to_del = self.get_events_to_delete(schedule, calendar_events)

        sim_updated_events = self.simulate_merge_changes(calendar_events, to_add, to_del)
        sim_to_add = self.get_events_to_add(schedule, sim_updated_events)
        sim_to_del = self.get_events_to_delete(schedule, sim_updated_events)

        if sim_to_add == 0 and sim_to_del == 0:
            del_events(to_del)
            add_events(to_add)
        else:
            print("CRITICAL merge error:")
            print("to_add:", to_add)
            print("to_del:", to_del)
            print("sim_to_add:", sim_to_add)
            print("sim_to_del:", sim_to_del)

        updated_events = self.get_all_calendar_events()
        up_to_add = self.get_events_to_add(schedule, sim_updated_events)
        up_to_del = self.get_events_to_delete(schedule, sim_updated_events)
        
        if sim_to_add != 0 or sim_to_del != 0:
            print("something REALLY bad happened while merging.")
            # this should never happen, but it will
            # TODO create handling for this edge case

    def get_gc_from_cd(self, cd_event):

        # TODO i hate timezones. did you know that. this thing will break
        # and oh boy HOW it will break.
        # well, not my problem for now
        event = {
            "summary": cd_event["title"],
            "description": "",
            "start": {
                "dateTime": cd_event["date"] + "T" + cd_event["start"] + ":00+01:00"
            },
            "end": {
                "dateTime": cd_event["date"] + "T" + cd_event["end"] + ":00+01:00"
            }
        }  # TODO convert from campus dual schedule format to google calendar
        return event

    def match_cd_gc(self, cd_event, gc_event):

        if get_gc_from_cd(cd_event) == gc_event:
            return True
        return False


    # compare a google calendar json to a cd schedule, return a list of elements to add
    def get_events_to_add(self, schedule, events):
        pass

    # compare a google calendar json to a cd schedule, return a list of elements ids to delete
    def get_events_to_delete(self, schedule, events):
        pass

    # get a list of all calendar events in the api format
    def get_all_calendar_events(self):
        
        return self.service.events().list(calendarId=self.CAL_ID).execute()["items"]

    # take a calendar api events list and pseudo-merge the proposed changes
    # this can be used to check the translation algorithms integrity
    def simulate_merge_changes(self, events, to_add, to_delete):
        pass

    # push events to google calendar
    def add_events(self, events):

        for event in events:
            self.service.events().insert(calendarId=self.CAL_ID, body=event).execute()

    # delete events with these event ids from google calendar
    def del_events(self, event_ids):
        
        for event_id in event_ids:
            self.service.events().delete(calendarId=self.CAL_ID, eventId=event_id).execute()

    def __init__(self):
        
        creds = None
        if os.path.exists("config/calendar-token.pickle"):
            with open("config/calendar-token.pickle", "rb") as token:
                creds = pickle.load(token)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "config/calendar-api.json", SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("config/calendar-token.pickle", "wb") as token:
                pickle.dump(creds, token)

        self.service = build("calendar", "v3", credentials=creds)

        f = open("config/calendar.json")
        cid = json.load(f)["cal_id"]
        self.CAL_ID = cid if cid is not None else "primary"