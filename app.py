from flask import Flask, render_template
from datetime import datetime
import scraper as sc
import discorder as dc
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)
app.static_folder = 'static'
events_meetup = sc.MeetupScrape()
events_discord = dc.discordEvents(os.environ['TOKEN'])

events_obj = events_meetup + events_discord
events=[]
seen = set()
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
            'image_url': event.imageurl,
            'rsvp_link': 'caint rsvp on a tv'
        }
        events.append(dd)

@app.route('/')
def index():
    # Sort events by date (you can modify this based on your needs)
    sorted_events = sorted(events, key=lambda x: x['index'])
    return render_template('index.html', events=sorted_events)

@app.route('/event/<int:event_id>')
def event_detail(event_id):
    event = next((event for event in events if event.id == event_id), None)
    if event:
        return render_template('event_detail.html', event=event)
    return "Event not found", 404

if __name__ == '__main__':
    app.run(debug=True)
