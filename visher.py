import datetime

# each event gets an object to itself


discordDelt = datetime.timedelta(hours=-4)


class Eventer:
    def __init__(self, eventjson, source):
        self.data = eventjson
        if source == "Meetup":
            self.ID = eventjson["id"]
            self.attendees = eventjson["going"]["totalCount"] - len(
                eventjson["eventHosts"]
            )
            self.date, self.duration, self.start, self.index = self.MUdateFormatter(
                eventjson["dateTime"]
            )
            self.title = eventjson["title"]
            self.source = source
            if eventjson["feeSettings"]:
                self.free = False
            else:
                self.free = True
            self.imageid = eventjson["featuredEventPhoto"]["__ref"]
            self.imageurl = ""
        elif source == "Discord":
            self.ID = eventjson["id"]
            self.attendees = eventjson["interested_count"]
            self.date, self.duration, self.start, self.index = self.DCdateFormatter()
            self.title = eventjson["name"]
            self.free = True
            self.imageid = ""
            self.imageurl = (
                eventjson["imageurl"]
                if eventjson["imageurl"] is not None
                else "/static/Members-Only-Event.png"
            )
            self.source = source

    def updateimageURL(self, url):
        self.imageurl = url

    def DCdateFormatter(self):
        startDtTs = (
            datetime.datetime.strptime(
                self.data["start_time"][:-6], "%Y-%m-%dT%H:%M:%S"
            )
            + discordDelt
        )
        datestring = startDtTs.strftime("%A, %d %B %Y")
        starttime = startDtTs.strftime("%I:%M%p")
        index = startDtTs.timestamp()
        duration = datetime.datetime.strptime(
            self.data["end_time"][:-6], "%Y-%m-%dT%H:%M:%S"
        ) - datetime.datetime.strptime(
            self.data["start_time"][:-6], "%Y-%m-%dT%H:%M:%S"
        )
        return (datestring, duration, starttime, index)

    def MUdateFormatter(self, DT):
        DtTs = datetime.datetime.strptime(DT[:-6], "%Y-%m-%dT%H:%M:%S")
        index = DtTs.timestamp()
        datestring = DtTs.strftime("%A, %d %B %Y")
        duration = DT[-5:]
        starttime = DtTs.strftime("%I:%M%p")
        return (datestring, duration, starttime, index)
