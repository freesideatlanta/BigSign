import requests
from bs4 import BeautifulSoup

from models import MeetupEvent, MeetupPage, MeetupPhoto
from visher import Eventer

url = "https://www.meetup.com/freeside-atlanta/events/"


def MeetupScrape() -> list[Eventer]:
    res = requests.get(url, timeout=30)
    res.raise_for_status()
    soup = BeautifulSoup(res.content, "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None:
        raise ValueError("Meetup page is missing its __NEXT_DATA__ payload")
    page = MeetupPage.model_validate_json(script.get_text())
    props = page.props.pageProps.apollo_state
    event_list: list[Eventer] = []
    for key, value in props.items():
        if not key.startswith("Event:"):
            continue
        event = MeetupEvent.model_validate(value)
        if event.status == "CANCELLED":
            continue
        photo = MeetupPhoto.model_validate(props[event.featuredEventPhoto.ref])
        event_list.append(Eventer.from_meetup(event, photo.highResUrl))
    return event_list
