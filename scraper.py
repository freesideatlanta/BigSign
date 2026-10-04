import json

import requests
from bs4 import BeautifulSoup

from visher import Eventer

url = "https://www.meetup.com/freeside-atlanta/events/"


def MeetupScrape():
    res = requests.get(url)
    soup = BeautifulSoup(res.content, "html.parser")
    money = soup.find_all("script")[-1]
    json_obj = json.loads(money.contents[0])
    props = json_obj["props"]["pageProps"]["__APOLLO_STATE__"]
    event_list = []
    for item in props:
        if "Event" in item:
            if props[item]["status"] == "CANCELLED":
                pass
            else:
                event = Eventer(props[item], "Meetup")
                event.updateimageURL(props[event.imageid]["highResUrl"])
                event_list.append(event)
        else:
            pass
    return event_list
