import os
import stat
import tempfile
from pathlib import Path

from pydantic import TypeAdapter

from events import collect_events
from models import SignEvent

event_list_adapter = TypeAdapter(list[SignEvent])


def events_json(output: Path = Path("eventsdata.json")) -> None:
    events = collect_events()
    data = event_list_adapter.dump_json(events)
    mode = stat.S_IMODE(output.stat().st_mode) if output.exists() else 0o644
    # Keep staging on the same filesystem so replacement is atomic for readers.
    with tempfile.TemporaryDirectory(
        dir=output.parent, prefix=f".{output.name}."
    ) as directory:
        temporary = Path(directory) / output.name
        with temporary.open("wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        temporary.replace(output)


if __name__ == "__main__":
    events_json()
