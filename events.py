"""Collect and normalize events for the sign's JSON output."""

import os
from collections.abc import Iterable

from dotenv import load_dotenv

import discorder as dc
import scraper as sc
from models import Settings, SignEvent
from visher import Eventer


def sign_events(events: Iterable[Eventer]) -> list[SignEvent]:
    result: list[SignEvent] = []
    seen: set[tuple[str, float]] = set()
    for event in events:
        key = (event.title, event.index)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            SignEvent(
                id=event.ID,
                index=event.index,
                title=event.title,
                date=event.date,
                time=event.start,
                free=event.free,
                source=event.source,
                attendees=event.attendees,
                image_url=event.imageurl,
            )
        )
    return result


def collect_events() -> list[SignEvent]:
    load_dotenv()
    settings = Settings.model_validate({"token": os.environ.get("TOKEN")})
    return sign_events(sc.MeetupScrape() + dc.discordEvents(settings.token))
