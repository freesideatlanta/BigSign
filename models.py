"""Strict contracts for source data and the sign's JSON output."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue

type EventSource = Literal["Meetup", "Discord"]
type EventId = str | int


class StrictModel(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", validate_assignment=True)


class SourceModel(StrictModel):
    # Providers include fields the sign does not consume.
    model_config = ConfigDict(extra="ignore")


class MeetupGoing(SourceModel):
    totalCount: int


class MeetupPhotoReference(SourceModel):
    ref: str = Field(alias="__ref")


class MeetupEvent(SourceModel):
    id: EventId
    title: str
    status: str
    dateTime: str
    going: MeetupGoing
    eventHosts: list[JsonValue]
    feeSettings: dict[str, JsonValue] | None
    featuredEventPhoto: MeetupPhotoReference


class MeetupPhoto(SourceModel):
    highResUrl: str


class MeetupPageProps(SourceModel):
    apollo_state: dict[str, JsonValue] = Field(alias="__APOLLO_STATE__")


class MeetupProps(SourceModel):
    pageProps: MeetupPageProps


class MeetupPage(SourceModel):
    props: MeetupProps


class DiscordEvent(StrictModel):
    id: int
    name: str
    start_time: str
    end_time: str | None
    interested_count: int
    imageurl: str | None


class Settings(StrictModel):
    token: str = Field(min_length=1, repr=False)


class SignEvent(StrictModel):
    id: EventId
    index: float
    title: str
    date: str
    time: str
    free: bool
    source: EventSource
    attendees: int
    image_url: str | None
