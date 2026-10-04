import datetime
from typing import Self

from models import DiscordEvent, EventId, EventSource, MeetupEvent, StrictModel

discordDelt = datetime.timedelta(hours=-4)
type FormattedDate = tuple[str, str | datetime.timedelta, str, float]


class Eventer(StrictModel):
    ID: EventId
    attendees: int
    date: str
    duration: str | datetime.timedelta
    start: str
    index: float
    title: str
    source: EventSource
    free: bool
    imageid: str = ""
    imageurl: str = ""

    @classmethod
    def from_meetup(cls, event: MeetupEvent, image_url: str) -> Self:
        date, duration, start, index = cls.MUdateFormatter(event.dateTime)
        return cls(
            ID=event.id,
            attendees=event.going.totalCount - len(event.eventHosts),
            date=date,
            duration=duration,
            start=start,
            index=index,
            title=event.title,
            source="Meetup",
            free=not bool(event.feeSettings),
            imageid=event.featuredEventPhoto.ref,
            imageurl=image_url,
        )

    @classmethod
    def from_discord(cls, event: DiscordEvent) -> Self:
        date, duration, start, index = cls.DCdateFormatter(event)
        return cls(
            ID=event.id,
            attendees=event.interested_count,
            date=date,
            duration=duration,
            start=start,
            index=index,
            title=event.name,
            source="Discord",
            free=True,
            imageurl=event.imageurl or "/static/Members-Only-Event.png",
        )

    def updateimageURL(self, url: str) -> None:
        self.imageurl = url

    @staticmethod
    def DCdateFormatter(event: DiscordEvent) -> FormattedDate:
        start_dt = datetime.datetime.fromisoformat(event.start_time).replace(
            tzinfo=None
        )
        display_dt = start_dt + discordDelt
        duration = (
            datetime.datetime.fromisoformat(event.end_time).replace(tzinfo=None)
            - start_dt
            if event.end_time is not None
            else datetime.timedelta()
        )
        return (
            display_dt.strftime("%A, %d %B %Y"),
            duration,
            display_dt.strftime("%I:%M%p"),
            display_dt.timestamp(),
        )

    @staticmethod
    def MUdateFormatter(dt: str) -> FormattedDate:
        start_dt = datetime.datetime.fromisoformat(dt).replace(tzinfo=None)
        return (
            start_dt.strftime("%A, %d %B %Y"),
            dt[-5:],
            start_dt.strftime("%I:%M%p"),
            start_dt.timestamp(),
        )
