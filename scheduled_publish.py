"""Облачная публикация с сохранением прогресса до и после отправки."""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from bot import ROOT, api, read_config
from content import render

STATE = ROOT / ".publication-state.json"


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise RuntimeError("Публикация по расписанию разрешена только в GitHub Actions.")
    for command in (
        ["git", "add", "--", STATE.name],
        ["git", "commit", "-m", "Update publication progress [skip ci]"],
        ["git", "push", "origin", "HEAD:main"],
    ):
        subprocess.run(command, cwd=ROOT, check=True, capture_output=True)


def publish(state, now, send, persist):
    if state.get("pending"):
        raise RuntimeError("Предыдущая доставка не подтверждена. Проверьте канал и pending в .publication-state.json.")
    last_sent = datetime.fromisoformat(state["last_sent_at"])
    if now - last_sent < timedelta(hours=3):
        print("С предыдущей публикации ещё не прошло 3 часа.")
        return
    index = state["next_index"]
    text = render(index)
    state["pending"] = {"index": index, "reserved_at": now.isoformat()}
    # Если резервирование не попало в GitHub, сообщение не отправляется.
    persist(state)
    result = send(text)
    state.update(next_index=index+1, last_sent_at=now.isoformat(), last_message_id=result["message_id"], pending=None)
    persist(state)
    print(f"Опубликована задача #{index+1}. ID сообщения: {result['message_id']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Проверить подключение без отправки")
    parser.add_argument("--preview", action="store_true", help="Показать следующий пост без подключения")
    args = parser.parse_args()
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if args.preview:
        print(render(state["next_index"]))
        return
    config = read_config(ROOT / ".env")
    token = config.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Секрет TELEGRAM_BOT_TOKEN не настроен.")
    channel = config.get("TELEGRAM_CHANNEL") or "@codelevel_pygo"
    bot = api(token, "getMe")
    chat = api(token, "getChat", chat_id=channel)
    member = api(token, "getChatMember", chat_id=chat["id"], user_id=bot["id"])
    if chat.get("type") != "channel" or not member.get("can_post_messages"):
        raise ValueError("Не подтверждены канал и права публикации бота.")
    if args.check:
        print("Облачная проверка успешна. Публикация не выполнялась.")
        return
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("Для локального просмотра используйте --preview.")
    publish(state, datetime.now(timezone.utc),
            lambda text: api(token, "sendMessage", chat_id=chat["id"], text=text, parse_mode="HTML"), save_state)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
