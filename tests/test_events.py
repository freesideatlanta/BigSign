import datetime
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import JsonValue, ValidationError

import discorder
import jsonolater
import scraper
from events import sign_events
from models import DiscordEvent, MeetupEvent, Settings, SignEvent
from visher import Eventer


def meetup_payload() -> dict[str, JsonValue]:
    return {
        "id": "123",
        "title": "Workshop",
        "status": "ACTIVE",
        "dateTime": "2026-10-04T18:30:00-04:00",
        "going": {"totalCount": 5},
        "eventHosts": [{"__ref": "Member:1"}],
        "feeSettings": None,
        "featuredEventPhoto": {"__ref": "Photo:1"},
        "unusedProviderField": True,
    }


def meetup_event() -> Eventer:
    return Eventer.from_meetup(
        MeetupEvent.model_validate(meetup_payload()), "https://example.com/photo.jpg"
    )


def discord_payload() -> DiscordEvent:
    return DiscordEvent(
        id=456,
        name="Workshop",
        start_time="2026-10-04T22:30:00+00:00",
        end_time="2026-10-05T00:30:00+00:00",
        interested_count=3,
        imageurl=None,
    )


class ModelTests(unittest.TestCase):
    def test_meetup_conversion(self) -> None:
        event = meetup_event()
        self.assertEqual(event.ID, "123")
        self.assertEqual(event.attendees, 4)
        self.assertEqual(event.start, "06:30PM")
        self.assertTrue(event.free)

    def test_timestamps_ignore_server_timezone_and_observe_dst(self) -> None:
        original_timezone = os.environ.get("TZ")
        try:
            for timezone in ("UTC", "America/New_York"):
                os.environ["TZ"] = timezone
                time.tzset()
                for month, display in ((10, "06:30PM"), (12, "05:30PM")):
                    payload = discord_payload()
                    payload.start_time = f"2026-{month:02}-04T22:30:00+00:00"
                    payload.end_time = None
                    discord_event = Eventer.from_discord(payload)
                    meetup = meetup_payload()
                    meetup["dateTime"] = payload.start_time
                    meetup_event = Eventer.from_meetup(
                        MeetupEvent.model_validate(meetup), ""
                    )
                    expected = datetime.datetime.fromisoformat(
                        payload.start_time
                    ).timestamp()
                    with self.subTest(timezone=timezone, month=month):
                        for event in (discord_event, meetup_event):
                            self.assertEqual(event.index, expected)
                            self.assertEqual(event.start, display)
        finally:
            if original_timezone is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = original_timezone
            time.tzset()

    def test_naive_timestamps_are_rejected(self) -> None:
        payload = discord_payload()
        payload.start_time = "2026-10-04T22:30:00"
        with self.assertRaisesRegex(ValueError, "timezone offset"):
            Eventer.from_discord(payload)
        with self.assertRaisesRegex(ValueError, "timezone offset"):
            Eventer.MUdateFormatter(payload.start_time)

    def test_meetup_rejects_nested_string_count(self) -> None:
        payload = meetup_payload()
        payload["going"] = {"totalCount": "5"}
        with self.assertRaises(ValidationError):
            MeetupEvent.model_validate(payload)

    def test_discord_rejects_string_and_boolean_ids(self) -> None:
        for invalid_id in ("456", True):
            payload = discord_payload().model_dump()
            payload["id"] = invalid_id
            with self.subTest(id=invalid_id), self.assertRaises(ValidationError):
                DiscordEvent.model_validate(payload)

    def test_assignment_validation(self) -> None:
        event = meetup_event()
        with self.assertRaises(ValidationError):
            setattr(event, "attendees", "4")
        self.assertEqual(event.attendees, 4)

    def test_output_rejects_wrong_types_and_extra_fields(self) -> None:
        data = sign_events([meetup_event()])[0].model_dump()
        for field, value in (("free", "true"), ("attendees", "4"), ("unknown", 1)):
            with self.subTest(field=field), self.assertRaises(ValidationError):
                SignEvent.model_validate({**data, field: value})

    def test_missing_and_empty_token_are_rejected(self) -> None:
        for value in (None, "", 123):
            with self.subTest(token=value), self.assertRaises(ValidationError):
                Settings.model_validate({"token": value})

    def test_discord_optional_end_and_cover(self) -> None:
        payload = discord_payload()
        payload.end_time = None
        event = Eventer.from_discord(payload)
        self.assertEqual(event.duration, datetime.timedelta())
        self.assertEqual(event.imageurl, "/static/Members-Only-Event.png")
        self.assertEqual(event.start, "06:30PM")

    def test_deduplication_is_repeatable(self) -> None:
        meetup = meetup_event()
        discord = Eventer.from_discord(discord_payload())
        for _ in range(2):
            events = sign_events([meetup, discord])
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].source, "Meetup")

    def test_deduplication_preserves_distinct_same_day_sessions(self) -> None:
        first = meetup_event()
        payload = discord_payload()
        payload.start_time = "2026-10-05T00:30:00+00:00"
        payload.end_time = None
        second = Eventer.from_discord(payload)
        self.assertEqual(first.date, second.date)
        self.assertEqual(
            sign_events([first, second]),
            [sign_events([first])[0], sign_events([second])[0]],
        )

    def test_json_output_round_trip_and_field_names(self) -> None:
        events = sign_events([meetup_event()])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.json"
            with patch("jsonolater.collect_events", return_value=events):
                jsonolater.events_json(path)
                self.assertEqual(
                    jsonolater.event_list_adapter.validate_json(path.read_bytes()),
                    events,
                )
                first_output = path.read_bytes()
                jsonolater.events_json(path)
                self.assertEqual(path.read_bytes(), first_output)
        self.assertEqual(
            set(events[0].model_dump()),
            {
                "id",
                "index",
                "title",
                "group",
                "date",
                "time",
                "venue",
                "free",
                "source",
                "description",
                "attendees",
                "image_url",
                "rsvp_link",
            },
        )

    def test_json_replacement_keeps_existing_readers_consistent(self) -> None:
        events = sign_events([meetup_event()])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "events.json"
            output.write_bytes(b"[]")
            output.chmod(0o640)
            with output.open("rb") as old_reader:
                with patch("jsonolater.collect_events", return_value=events):
                    jsonolater.events_json(output)
                self.assertEqual(old_reader.read(), b"[]")
            self.assertEqual(
                jsonolater.event_list_adapter.validate_json(output.read_bytes()), events
            )
            self.assertEqual(output.stat().st_mode & 0o777, 0o640)
            self.assertEqual(list(Path(directory).iterdir()), [output])

    def test_failed_json_replacement_preserves_previous_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "events.json"
            output.write_bytes(b"[]")
            with patch(
                "jsonolater.collect_events", return_value=sign_events([meetup_event()])
            ):
                with patch.object(
                    Path, "replace", side_effect=OSError("replace failed")
                ):
                    with self.assertRaises(OSError):
                        jsonolater.events_json(output)
            self.assertEqual(output.read_bytes(), b"[]")
            self.assertEqual(list(Path(directory).iterdir()), [output])


class CollectorTests(unittest.TestCase):
    def test_scraper_validates_page_and_skips_cancelled(self) -> None:
        cancelled = {**meetup_payload(), "id": "124", "status": "CANCELLED"}
        apollo = {
            "Event:123": meetup_payload(),
            "Event:124": cancelled,
            "Photo:1": {"highResUrl": "https://example.com/photo.jpg"},
            "OtherEventData:1": {"unused": True},
        }
        page = {"props": {"pageProps": {"__APOLLO_STATE__": apollo}}}
        response = MagicMock()
        response.content = (
            '<script id="__NEXT_DATA__" type="application/json">'
            + json.dumps(page)
            + "</script><script>unrelated</script>"
        ).encode()
        with patch("scraper.requests.get", return_value=response) as get:
            result = scraper.MeetupScrape()
        self.assertEqual(result, [meetup_event()])
        get.assert_called_once_with(scraper.url, timeout=30)
        response.raise_for_status.assert_called_once()

    def test_scraper_reports_missing_payload(self) -> None:
        response = MagicMock(content=b"<html></html>")
        with patch("scraper.requests.get", return_value=response):
            with self.assertRaisesRegex(ValueError, "__NEXT_DATA__"):
                scraper.MeetupScrape()

    def test_discord_uses_sdk_values_and_stringifies_cover(self) -> None:
        event = MagicMock()
        event.id = 456
        event.name = "Workshop"
        event.start_time = datetime.datetime.fromisoformat("2026-10-04T22:30:00+00:00")
        event.end_time = None
        event.user_count = 3
        event.cover_image = "https://example.com/cover.png"
        guild = MagicMock()
        guild.fetch_scheduled_events = AsyncMock(return_value=[event])
        client = MagicMock()
        client.guilds = [guild]
        client.event.side_effect = lambda callback: callback
        client.close = AsyncMock()
        client.is_closed.return_value = True

        async def start(token: str) -> None:
            self.assertEqual(token, "test-token")
            callback = client.event.call_args.args[0]
            await callback()

        client.start = AsyncMock(side_effect=start)
        with patch("discorder.discord.Client", return_value=client):
            result = discorder.discordEvents("test-token")
        self.assertEqual(result[0].imageurl, "https://example.com/cover.png")
        client.close.assert_awaited_once()

        # Errors in SDK callbacks must reach the collector rather than publish []
        # or a partially collected list as if validation had succeeded.
        event.user_count = "3"
        client.close.reset_mock()
        with patch("discorder.discord.Client", return_value=client):
            with self.assertRaises(ValidationError):
                discorder.discordEvents("test-token")
        client.close.assert_awaited_once()

    def test_discord_failures_preserve_published_events(self) -> None:
        for failure in ("login", "permission", "no_server"):
            with (
                self.subTest(failure=failure),
                tempfile.TemporaryDirectory() as directory,
            ):
                output = Path(directory) / "events.json"
                output.write_bytes(b"[]")
                client = MagicMock()
                client.event.side_effect = lambda callback: callback
                client.is_closed.return_value = False

                async def close() -> None:
                    client.is_closed.return_value = True

                client.close = AsyncMock(side_effect=close)
                guild = MagicMock()
                client.guilds = [] if failure == "no_server" else [guild]
                guild.fetch_scheduled_events = AsyncMock(
                    side_effect=discorder.discord.Forbidden(
                        MagicMock(status=403, reason="Forbidden"), "No permission"
                    )
                )

                async def start(token: str) -> None:
                    if failure == "login":
                        raise discorder.discord.LoginFailure("Invalid token")
                    await client.event.call_args.args[0]()

                client.start = AsyncMock(side_effect=start)
                with patch.dict(os.environ, {"TOKEN": "test-token"}):
                    with patch("events.sc.MeetupScrape", return_value=[meetup_event()]):
                        with patch("discorder.discord.Client", return_value=client):
                            with self.assertRaises(
                                (
                                    discorder.discord.LoginFailure,
                                    discorder.discord.Forbidden,
                                    RuntimeError,
                                )
                            ):
                                jsonolater.events_json(output)
                self.assertEqual(output.read_bytes(), b"[]")
                client.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
