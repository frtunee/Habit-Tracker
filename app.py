from flask import Flask, render_template, request
from datetime import date, timedelta, time, datetime
import json
from pathlib import Path
from calendar import monthrange
import os
from flask_sqlalchemy import SQLAlchemy
from zoneinfo import ZoneInfo

APP_TIMEZONE = ZoneInfo("Europe/Prague")

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///habits.db")

# SQLAlchemy's psycopg driver uses this URL form.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

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

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    day = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "day", name="unique_habit_day"),
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

    now = datetime.now(APP_TIMEZONE)
    today = now.date()

    tomorrow = today + timedelta(days=1)
    midnight = datetime.combine(tomorrow, time.min, tzinfo=APP_TIMEZONE)

    remaining_seconds = int(midnight.timestamp() - now.timestamp())

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

@app.route("/toggle-checkbox", methods=["POST"])
def toggle_checkbox():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Invalid checkbox data"}, 400

    entry = data.get("entry")
    is_checked = data.get("checked")

    if not isinstance(entry, str) or not isinstance(is_checked, bool):
        return {"error": "Invalid checkbox data"}, 400

    if is_checked:
        completed.add(entry)
    else:
        completed.discard(entry)

    save_data()
    return {"saved": True}

@app.route("/second-page")
def second_page():
    year = datetime.now(APP_TIMEZONE).year
    heatmap_months = []

    for month_number in range(1, 13):
        month_start = date(year, month_number, 1)
        days_in_month = monthrange(year, month_number)[1]

        # Start the calendar row on Monday.
        cells = [None] * month_start.weekday()

        for day_in_month in range(1, days_in_month + 1):
            day = date(year, month_number, day_in_month)
            count = 0

            for entry in completed:
                saved_date = entry.rsplit("|", 1)[-1]
                if saved_date == day.isoformat():
                    count += 1

            cells.append({
                "date": day,
                "count": count,
                "level": min(count, 4),
            })

        # Fill the final week with blank spaces.
        while len(cells) % 7 != 0:
            cells.append(None)

        heatmap_months.append({
            "name": month_start.strftime("%b"),
            "cells": cells,
        })

    return render_template(
        "second_page.html",
        active_page="second",
        year=year,
        heatmap_months=heatmap_months,
    )

with app.app_context():
    db.create_all()
if __name__ == "__main__":
    app.run(debug=True)
