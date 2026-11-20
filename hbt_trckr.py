from datetime import date
from datetime import datetime, timedelta, time

start_date = date(2026, 11, 20)

today = date(2026, 11, 20)

days_number = (today - start_date).days + 1

if today < start_date:
    print("The tracker hasn't started yet.")
else:
    print(f"Day: {days_number}")

now = datetime.now()

tomorrow = now.date() + timedelta(days=1)
midnight = datetime.combine(tomorrow, time.min)
remaining = midnight - now

total_seconds = int(remaining.total_seconds())
hours, leftover_seconds = divmod(total_seconds, 60 * 60)
minutes, seconds = divmod(leftover_seconds, 60)

print(f"{hours:02}:{minutes:02}:{seconds:02} remaining")

habits = ["Train", "Learn Python"]

dates = []
for offset in range(5):
   offset_date = start_date + timedelta(days=offset)
   dates.append(offset_date)

print("Habit", end=" ")
for day in dates:
    print(day.strftime("%d.%m."), end=" ")
print()

for habit in habits:
    print(habit,":", end="")

    for day in dates:
        print("[ ]", end="")

    print()

completed = []

print(" Log Habits ")
for habit in habits:
    habit_status = []
    for day in dates:
        answer = input(f"Status for {habit} on {day.strftime("%d.%m.")}? (y/n): ").strip().lower()

        if answer == "y":
            habit_status.append(True)
        else:
            habit_status.append(False)

    completed.append(habit_status)

print("- Habit Grid -")
print("Habit",":", end="")
for day in dates:
    print(day.strftime("%d.%m. "), end="")
print()

for habit, habit_status in zip(habits, completed):
    print(habit,": ", end="")

    for status in habit_status:
        if status:
            print("[x]  ", end="")
        else:
            print("[ ]  ", end="")

    print()