from __future__ import print_function
from datetime import datetime
import json
import pickle
import os.path
import time

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SIMULATE_BEFORE_MERGE = False # this should be set to true, in case i f*ck up any of the conversion
REQUEST_SLEEP = 0.5

class CalendarApi:

    service = None
    CAL_ID = None

    def sync_schedule(self, schedule):

        # TODO handle duplicate events
        calendar_events = self.get_all_calendar_events()
        to_add = self.get_events_to_add(schedule, calendar_events)
        to_del = self.get_events_to_delete(schedule, calendar_events)

        print("to add:", len(to_add))
        print("to del:", len(to_del))
        print("sleeping (you have 5 seconds to cancel the potential API inferno)")
        time.sleep(5)
        
        sim_to_add = list()
        sim_to_del = list()
        if SIMULATE_BEFORE_MERGE:
            sim_updated_events = self.simulate_merge_changes(calendar_events, to_add, to_del)
            sim_to_add = self.get_events_to_add(schedule, sim_updated_events)
            sim_to_del = self.get_events_to_delete(schedule, sim_updated_events)

        if len(sim_to_add) == 0 and len(sim_to_del) == 0:
            self.del_events(to_del)
            self.add_events(to_add)
        else:
            print("CRITICAL merge error:")
            print("to_add:", to_add)
            print("to_del:", to_del)
            print("sim_to_add:", sim_to_add)
            print("sim_to_del:", sim_to_del)

        if SIMULATE_BEFORE_MERGE:
            updated_events = self.get_all_calendar_events()
            up_to_add = self.get_events_to_add(schedule, sim_updated_events)
            up_to_del = self.get_events_to_delete(schedule, sim_updated_events)
        
            if len(sim_to_add) != 0 or len(sim_to_del) != 0:
                print("something REALLY bad happened while merging.")
                # this should never happen, but it will
                # TODO create handling for this edge case
        
        print("if there were no errors up to this point, the merge was successful! :)")

    def get_gc_from_cd(self, cd_event):

        # TODO i hate timezones. did you know that. this thing will break
        # and oh boy HOW it will break.
        # well, not my problem for now
        event = {
            "summary": cd_event["title"],
            "description": "aa",
            "location": "somewhere over the rainbow",
            "start": {
                "dateTime": cd_event["date"] + "T" + cd_event["start"] + ":00+01:00"
            },
            "end": {
                "dateTime": cd_event["date"] + "T" + cd_event["end"] + ":00+01:00"
            }
        }  # TODO convert from campus dual schedule format to google calendar
        return event

    def match_calendar_events(self, event1, event2, strict=False):

        fields = ["summary", "description", "location"]
        if strict:  # i am not sure if i will ever use this feature
            fields.append("id")

        for field in fields:
            if not field in event1:
                # print("field", field, "not in event1")
                return False
            if not field in event2:
                # print("field", field, "not in event2")
                return False
            if event1[field] != event2[field]:
                # print("field", field, "mismatch:", event1[field], ":", event2[field])
                return False

        # compare start/end time (this will hurt)
        for field in ("start", "end"):
            dt1 = event1[field]["dateTime"]
            dt2 = event2[field]["dateTime"]
            if not self.dirty_time_compare(dt1, dt2):
                return False
            
        return True

    def delete_all_events(self):

        events = list()
        for event in self.get_all_calendar_events():
            events.append(event["id"])
        self.del_events(events)

    # warning. dirty dirty code ahead. do not read if you're afraid of the spaghetti monster
    # edit: hey i might have found a neat-ish solution
    def dirty_time_compare(self, date1, date2):
        
        # day match
        # if date1.split("T")[0] != date2.split("T")[0]:
        #     return False
        form = "%Y-%m-%dT%H:%M:%S%z"
        # dt1 = datetime.strptime(date1, form)
        # dt2 = datetime.strptime(date2, form)
        dt1 = datetime.fromisoformat(date1)
        dt2 = datetime.fromisoformat(date2)
        diff = (dt1 - dt2).total_seconds()
        if diff == 0:
            return True
        return False

    # compare a google calendar json to a cd schedule, return a list of elements to add
    def get_events_to_add(self, schedule, events):
        
        to_add = list()
        for cd_event in schedule:
            create = True
            for gc_event in events:
                if self.match_calendar_events(self.get_gc_from_cd(cd_event), gc_event):
                    create = False
                    break
            if create:
                to_add.append(self.get_gc_from_cd(cd_event))
        return to_add


    # compare a google calendar json to a cd schedule, return a list of elements ids to delete
    def get_events_to_delete(self, schedule, events):
        
        to_del = list()
        for calendar_event in events:
            delete = True
            for cd_event in schedule:
                if self.match_calendar_events(self.get_gc_from_cd(cd_event), calendar_event):
                    delete = False
                    break
            if delete:
                to_del.append(calendar_event["id"])
        return to_del
                    

    # get a list of all calendar events in the api format
    def get_all_calendar_events(self):
        
        all_events = list()
        page_token = None
        while True:
            events = self.service.events().list(calendarId=self.CAL_ID, pageToken=page_token).execute()
            for event in events['items']:
                all_events.append(event)
            page_token = events.get('nextPageToken')
            if not page_token:
                break
        # return self.service.events().list(calendarId=self.CAL_ID).execute()["items"]
        return all_events

    # take a calendar api events list and pseudo-merge the proposed changes
    # this can be used to check the translation algorithms integrity
    def simulate_merge_changes(self, events, to_add, to_delete):
        pass

    # push events to google calendar
    def add_events(self, events):

        index = 1
        for event in events:
            print("adding", index, "/", len(events))
            index += 1
            self.service.events().insert(calendarId=self.CAL_ID, body=event).execute()
            time.sleep(REQUEST_SLEEP)

    # delete events with these event ids from google calendar
    def del_events(self, event_ids):
        
        index = 1
        for event_id in event_ids:
            print("deleting", index, "/", len(event_ids))
            index += 1
            self.service.events().delete(calendarId=self.CAL_ID, eventId=event_id).execute()
            time.sleep(REQUEST_SLEEP)

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
