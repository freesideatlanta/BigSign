from flask import Flask, render_template
from datetime import datetime
import scraper as sc
import discorder as dc
from dotenv import load_dotenv
import os
import json


load_dotenv()
events_meetup = sc.MeetupScrape()
events_discord = dc.discordEvents(os.environ['TOKEN'])

events_obj = events_meetup + events_discord
events=[]
seen = set()
def events_json():
      for event in events_obj:
          key = (event.title,event.date)
          if key not in seen:
              seen.add(key)
              dd = {
                  'id': event.ID,
                  'index': event.index,
                  'title': event.title,
                  'group': 'Humans, hopefully',
                  'date': event.date,
                  'time': event.start,
                  'venue': 'FreesideProbably',
                  'free': event.free,
                  'source':event.source,
                  'description': 'maybe in the future we can distill the description using an LLM',
                  'attendees': event.attendees,
                  'image_url': str(event.imageurl),
                  'rsvp_link': 'caint rsvp on a tv'
              }
              events.append(dd)
      print(events)
      with open("eventsdata.json","w") as final:
            json.dump(events,final)
events_json()
