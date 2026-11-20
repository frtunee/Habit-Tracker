from flask import Flask, render_template, request
from datetime import date, timedelta, time, datetime
import json
from pathlib import Path
from calendar import monthrange

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
        remove_habit = request.form.get("remove_habit")
        action = request.form.get("action")

        if remove_habit is not None:
            if remove_habit in habits:
                habits.remove(remove_habit)

                old_checkmarks = {
                    entry
                    for entry in completed
                    if entry.startswitch(f"{remove_habit}|")
                }
                completed.difference_update(old_checkmarks)

                save_data()

        elif action == "save":
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
        days_in_month = monthrange(today.year, today.month)[1]

        for days_in_month in range(1, days_in_month + 1):
            dates.append(date(today.year, today.month, days_in_month))

    return render_template(
        "index.html",
        habits=habits,
        dates=dates,
        completed=completed,
        day_number=day_number,
        remaining_seconds=remaining_seconds,
        start_date=start_date,
        today=today,
    )

now = datetime.now()
today = now.date()

tomorrow = today + timedelta(days=1)
midnight = datetime.combine(tomorrow, time.min)
remaining_seconds = int((midnight - now).total_seconds())


if __name__ == "__main__":
    app.run(debug=True)