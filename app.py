from flask import Flask, render_template, request
from datetime import date, timedelta, time, datetime
import json
from pathlib import Path

app = Flask(__name__)

start_date = date(2026, 11, 20)

default_habits = ["Train", "Learn Python"]
data_file = Path(__file__).with_name("habits.json")

if data_file.exists():
    saved_data = json.loads(data_file.read_text(encoding="utf-8"))

    if isinstance(saved_data, list):
        habits = default_habits.copy()
        completed = set(saved_data)
    else:
        habits = saved_data.get("habits", default_habits.copy())
        completed = set(saved_data.get("completed", []))
else:
    habits = default_habits.copy()
    completed = set()

def save_data():
    saved_data = {
        "habits": habits,
        "completed": sorted(completed),
    }
    data_file.write_text(
        json.dumps(saved_data, indent=2),
        encoding="utf-á"
    )

@app.route("/", methods =["GET", "POST"])
def home():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "save":
            completed.clear()
            completed.update(request.form.getlist("completed"))
            save_data()

        elif action == "add_habit":
            new_habit = request.form.get("new_habit", "").strip()

            if new_habit and new_habit not in habits:
                habits.append(new_habit)
                save_data()

    today = date.today()

    if today < start_date:
        day_number = None
        dates = []
    else:
        day_number = (today - start_date).days + 1

        dates = []
        for offset in range(day_number):
            dates.append(start_date + timedelta(days=offset))

    return render_template(
        "index.html",
        habits=habits,
        dates=dates,
        completed=completed,
        day_number=day_number,
        remaining_seconds=remaining_seconds,
    )

now = datetime.now()
today = now.date()

tomorrow = today + timedelta(days=1)
midnight = datetime.combine(tomorrow, time.min)
remaining_seconds = int((midnight - now).total_seconds())


if __name__ == "__main__":
    app.run(debug=True)