from pathlib import Path

from pydantic import TypeAdapter

from events import collect_events
from models import SignEvent

event_list_adapter = TypeAdapter(list[SignEvent])


def events_json(output: Path = Path("eventsdata.json")) -> None:
    events = collect_events()
    output.write_bytes(event_list_adapter.dump_json(events))


if __name__ == "__main__":
    events_json()
