import os
from datetime import datetime
from zoneinfo import ZoneInfo

import flask
import functions_framework
import requests
from google.cloud import firestore

db = firestore.Client()
webhook_url = os.environ["DISCORD_WEBHOOK_URL"]


def get_todays_birthdays(month: int, day: int) -> list[dict]:
    query = (
        db.collection("birthdays")
        .where(filter=firestore.FieldFilter("month", "==", month))
        .where(filter=firestore.FieldFilter("day", "==", day))
    )
    return [doc.to_dict() for doc in query.stream()]


def build_message(name: str, note: str | None) -> str:
    msg = f"🎂 今日は {name} の誕生日です！おめでとう！🎉"
    if note:
        msg += f"\n{note}"
    return msg


def send_discord_message(content: str) -> None:
    response = requests.post(webhook_url, json={"content": content}, timeout=10)
    response.raise_for_status()


@functions_framework.http
def birthday_notify(_request: flask.Request) -> tuple[str, int]:
    jst = ZoneInfo("Asia/Tokyo")
    today = datetime.now(tz=jst)
    month, day = today.month, today.day

    docs = get_todays_birthdays(month, day)

    if not docs:
        print(f"No birthdays today. ({month}/{day})")
        return ("No birthdays today.", 200)

    errors = []

    for doc in docs:
        name = doc.get("name", "（名前未設定）")
        note = doc.get("note") or None # 空文字の場合もNone
        message = build_message(name, note)
        try:
            send_discord_message(message)
            print(f"Notified: {name}")
        except Exception as e:
            errors.append(f"{name}: {e}")

    if errors:
        error_msg = f"Completed with errors: {'; '.join(errors)}"
        print(error_msg)
        return (error_msg, 500)

    result = f"Notified {len(docs)} birthday(s)."
    print(result)
    return (result, 200)
