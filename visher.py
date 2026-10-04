import datetime
from typing import Self
from zoneinfo import ZoneInfo

from models import DiscordEvent, EventId, EventSource, MeetupEvent, StrictModel

DISPLAY_TIME_ZONE = ZoneInfo("America/New_York")


def parse_datetime(value: str) -> datetime.datetime:
    result = datetime.datetime.fromisoformat(value)
    if result.utcoffset() is None:
        raise ValueError("Event timestamps must include a timezone offset")
    return result


def format_start(value: str) -> tuple[str, str, float]:
    start = parse_datetime(value)
    display = start.astimezone(DISPLAY_TIME_ZONE)
    return (
        display.strftime("%A, %d %B %Y"),
        display.strftime("%I:%M%p"),
        start.timestamp(),
    )


class Eventer(StrictModel):
    ID: EventId
    attendees: int
    date: str
    duration: datetime.timedelta | None = None
    start: str
    index: float
    title: str
    source: EventSource
    free: bool
    imageurl: str = ""

    @classmethod
    def from_meetup(cls, event: MeetupEvent, image_url: str) -> Self:
        date, start, index = format_start(event.dateTime)
        return cls(
            ID=event.id,
            attendees=event.going.totalCount - len(event.eventHosts),
            date=date,
            start=start,
            index=index,
            title=event.title,
            source="Meetup",
            free=not bool(event.feeSettings),
            imageurl=image_url,
        )

    @classmethod
    def from_discord(cls, event: DiscordEvent) -> Self:
        date, start, index = format_start(event.start_time)
        duration = (
            parse_datetime(event.end_time) - parse_datetime(event.start_time)
            if event.end_time is not None
            else None
        )
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
