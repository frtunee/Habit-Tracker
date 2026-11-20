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
        encoding="utf-8"
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
                    if entry.startswith(f"{remove_habit}|")
                }
                completed.difference_update(old_checkmarks)

                save_data()

        elif action == "save":
            selected_month_text = request.form.get("selected_month")

            if selected_month_text:
                month_prefix = selected_month_text + "-"
                checks_from_other_months = {
                    entry
                    for entry in completed
                    if not entry.rsplit("|", 1)[-1].startswith(month_prefix)
                }

                completed.clear()
                completed.update(checks_from_other_months)
                completed.update(request.form.getlist("completed"))
                save_data()

        elif action == "add_habit":
            new_habit = request.form.get("new_habit", "").strip()

            if new_habit and new_habit not in habits:
                habits.append(new_habit)
                save_data()

    now = datetime.now()
    today = now.date()

    tomorrow = today + timedelta(days=1)
    midnight = datetime.combine(tomorrow, time.min)
    remaining_seconds = int((midnight - now).total_seconds())

    if today < start_date:
        day_number = None
    else:
        day_number = (today - start_date).days + 1

    current_month = date(today.year, today.month, 1)

    months = []
    month_cursor = date(start_date.year, start_date.month, 1)

    while month_cursor <= current_month:
        months.append(month_cursor)

        if month_cursor.month == 12:
            month_cursor = date(month_cursor.year + 1, 1, 1)
        else:
            month_cursor = date(month_cursor.year, month_cursor.month + 1, 1)

    if request.method == "POST":
        requested_month = request.form.get("selected_month")
    else:
        requested_month = request.args.get("month")

    try:
        year_text, month_text = requested_month.split("-")
        selected_month = date(int(year_text), int(month_text), 1)
    except (AttributeError, ValueError):
        selected_month = current_month

    if selected_month not in months:
        selected_month = current_month

    days_in_month = monthrange(selected_month.year, selected_month.month)[1]
    dates = []

    for day_in_month in range(1, days_in_month + 1):
        dates.append(date(selected_month.year, selected_month.month, day_in_month))

    return render_template(
        "index.html",
        habits=habits,
        dates=dates,
        completed=completed,
        day_number=day_number,
        remaining_seconds=remaining_seconds,
        start_date=start_date,
        today=today,
        months=months,
        selected_month=selected_month,
        active_page="home",
    )

now = datetime.now()
today = now.date()

tomorrow = today + timedelta(days=1)
midnight = datetime.combine(tomorrow, time.min)
remaining_seconds = int((midnight - now).total_seconds())

@app.route("/second-page")
def second_page():
    year = date.today().year
    year_start = date(year, 1,1)
    next_year_start = date(year + 1, 1, 1)
    days_in_year = (next_year_start - year_start).days

    heatmap_days = []

    for offset in range(days_in_year):
        day = year_start + timedelta(days=offset)
        count = 0

        for entry in completed:
            saved_data = entry.rsplit("|", 1)[-1]

            if saved_data == day.isoformat():
                count += 1

        heatmap_days.append({
            "date": day,
            "count": count,
            "level": min(count, 4),
        })

    return render_template(
        "second_page.html",
        active_page="second",
        year=year,
        heatmap_days=heatmap_days,
    )


if __name__ == "__main__":
    app.run(debug=True)