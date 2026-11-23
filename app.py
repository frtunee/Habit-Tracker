from flask import Flask, render_template, request
from datetime import date, timedelta, time, datetime
from calendar import monthrange
import os
from flask_sqlalchemy import SQLAlchemy
from zoneinfo import ZoneInfo
from flask_migrate import Migrate

APP_TIMEZONE = ZoneInfo("Europe/Prague")

app = Flask(__name__)

database_url = os.environ.get("DATABASE_URL", "sqlite:///habits.db")

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
migrate = Migrate(app, db)

start_date = date(2026, 11, 23)

default_habits = ["Train", "Learn Python"]

class Habit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    completions = db.relationship(
        "Completion",
        backref="habit",
        cascade="all, delete-orphan",
    )


class Completion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey("habit.id"), nullable=False)
    day = db.Column(db.Date, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("habit_id", "day", name="unique_habit_day"),
    )

def get_tracker_data():
    habit_rows = db.session.execute(
        db.select(Habit).order_by(Habit.id)
    ).scalars().all()

    completion_rows = db.session.execute(
        db.select(Completion, Habit)
        .join(Habit)
    ).all()

    completed = {
        f"{habit.name}|{completion.day.isoformat()}"
        for completion, habit in completion_rows
    }

    return habit_rows, completed    

@app.route("/", methods =["GET", "POST"])
def home():
    if request.method == "POST":

        remove_habit = request.form.get("remove_habit")
        action = request.form.get("action")

        if remove_habit is not None:
            habit = db.session.execute(
                db.select(Habit).filter_by(name=remove_habit)
            ).scalar_one_or_none()

            if habit is not None:
                db.session.delete(habit)
                db.session.commit()

        elif action == "add_habit":
            new_habit = request.form.get("new_habit", "").strip()

            if new_habit:
                existing_habit = db.session.execute(
                    db.select(Habit).filter_by(name=new_habit)
                ).scalar_one_or_none()

                if existing_habit is None:
                    db.session.add(Habit(name=new_habit))
                    db.session.commit()

    habits, completed = get_tracker_data()

    now = datetime.now(APP_TIMEZONE)

    today = now.date()
    tomorrow = today + timedelta(days=1)
    midnight = datetime.combine(
        tomorrow,
        time.min,
        tzinfo=APP_TIMEZONE,
    )
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

@app.route("/toggle-checkbox", methods=["POST"])
def toggle_checkbox():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "Invalid checkbox data"}, 400

    entry = data.get("entry")
    is_checked = data.get("checked")

    if not isinstance(entry, str) or not isinstance(is_checked, bool):
        return {"error": "Invalid checkbox data"}, 400

    try:
        habit_name, day_text = entry.rsplit("|", 1)
        completion_day = date.fromisoformat(day_text)
    except ValueError:
        return {"error": "Invalid checkbox entry"}, 400

    habit = db.session.execute(
        db.select(Habit).filter_by(name=habit_name)
    ).scalar_one_or_none()

    if habit is None:
        return {"error": "Habit not found"}, 404

    completion = db.session.execute(
        db.select(Completion).filter_by(
            habit_id=habit.id,
            day=completion_day,
        )
    ).scalar_one_or_none()

    if is_checked and completion is None:
        db.session.add(Completion(habit_id=habit.id, day=completion_day))
    elif not is_checked and completion is not None:
        db.session.delete(completion)

    db.session.commit()
    return {"saved": True}

@app.route("/second-page")
def second_page():
    year = datetime.now(APP_TIMEZONE).year
    heatmap_months = []
    completion_rows = db.session.execute(
        db.select(Completion.day, db.func.count(Completion.id))
        .group_by(Completion.day)
    ).all()

    completion_counts = {
        day: count
        for day, count in completion_rows
    }

    for month_number in range(1, 13):
        month_start = date(year, month_number, 1)
        days_in_month = monthrange(year, month_number)[1]

        cells = [None] * month_start.weekday()

        for day_in_month in range(1, days_in_month + 1):
            day = date(year, month_number, day_in_month)
            count = completion_counts.get(day, 0)

            cells.append({
                "date": day,
                "count": count,
                "level": min(count, 4),
            })

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
