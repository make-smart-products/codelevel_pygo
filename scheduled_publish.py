"""Облачная публикация с сохранением прогресса до и после отправки."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from bot import ROOT, api, read_config
from content import course_posts, render

STATE = ROOT / ".course-publication-state.json"
POSTS_PER_RUN = 5


def send_course_post(token, chat_id, text):
    post = next((item for item in course_posts() if item['html'] == text), None)
    if post is None:
        raise ValueError('Пост отсутствует в редакционной очереди.')
    animation = post.get('animation')
    if animation:
        if not animation.get('file_id'):
            raise RuntimeError('Анимация поста ещё не загружена в Telegram.')
        return api(token, 'sendAnimation', chat_id=chat_id, animation=animation['file_id'],
                   caption=post['caption_html'], parse_mode='HTML')
    return api(token, 'sendMessage', chat_id=chat_id, text=text, parse_mode='HTML')


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
        raise RuntimeError("Предыдущая доставка не подтверждена. Проверьте канал и pending в .course-publication-state.json.")
    if state['next_index'] >= len(course_posts()):
        print('Все публикации учебной программы отправлены. Очередь завершена.')
        return
    # Сравниваем окна cron, а не прошедшие секунды: задержка предыдущего
    # запуска GitHub не должна отменять следующий плановый выпуск.
    slot = int((now.timestamp() - 17 * 60) // (60 * 60))
    last_sent = datetime.fromisoformat(state["last_sent_at"])
    # Вычисляем из времени: старые last_slot относились к трёхчасовым окнам.
    last_slot = int((last_sent.timestamp() - 17 * 60) // (60 * 60))
    batch = state.get("batch")
    if not batch and slot <= last_slot:
        print("В текущем часовом окне публикация уже выполнена.")
        return
    if not batch:
        batch = {"slot": slot, "end_index": min(state["next_index"] + POSTS_PER_RUN, len(course_posts()))}
        state["batch"] = batch
    while state["next_index"] < batch["end_index"]:
        index = state["next_index"]
        text = render(index)
        post_id = course_posts()[index]['id']
        state["pending"] = {"index": index, "post_id": post_id, "reserved_at": now.isoformat()}
        # Каждый пост резервируется отдельно; при неопределённой доставке
        # серия останавливается, уже подтверждённые посты не повторяются.
        persist(state)
        result = send(text)
        state.update(next_index=index+1, last_post_id=post_id, last_slot=slot, last_sent_at=now.isoformat(), last_message_id=result["message_id"], pending=None)
        if index + 1 == batch["end_index"]:
            state["batch"] = None
        persist(state)
        print(f"Опубликован пост курса #{index+1}. ID сообщения: {result['message_id']}")
        if state["batch"]:
            time.sleep(3.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Проверить подключение без отправки")
    parser.add_argument("--preview", action="store_true", help="Показать следующий пост без подключения")
    args = parser.parse_args()
    if (ROOT / 'course-retired.json').exists() and not args.check and not args.preview:
        print('Публикация прежнего курса остановлена: канал переведён на новый формат.')
        return
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if args.preview:
        start = state["next_index"]
        end = min((state.get("batch") or {}).get("end_index", start + POSTS_PER_RUN), len(course_posts()))
        if start >= end:
            print('Все публикации учебной программы отправлены.')
            return
        print("\n\n-----\n\n".join(render(index) for index in range(start, end)))
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
            lambda text: send_course_post(token, chat['id'], text), save_state)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
