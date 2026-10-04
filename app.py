from functools import cache

from flask import Flask, render_template

from events import collect_events
from models import SignEvent

app = Flask(__name__)
app.static_folder = "static"


@cache
def get_events() -> list[SignEvent]:
    return collect_events()


@app.route("/")
def index() -> str:
    sorted_events = sorted(get_events(), key=lambda event: event.index)
    return render_template("index.html", events=sorted_events)


@app.route("/event/<int:event_id>")
def event_detail(event_id: int) -> str | tuple[str, int]:
    event = next(
        (event for event in get_events() if str(event.id) == str(event_id)), None
    )
    if event:
        return render_template("event_detail.html", event=event)
    return "Event not found", 404


if __name__ == "__main__":
    app.run(debug=True)
