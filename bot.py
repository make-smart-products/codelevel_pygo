"""Первая публикация CodeLevel через Telegram Bot API (Python 3.12+)."""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent


def read_config(path):
    config = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            if not separator:
                raise ValueError("В файле настроек ожидаются строки ИМЯ=значение.")
            config[key.strip()] = value.strip().strip("\"'")
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHANNEL"):
        if key in os.environ:
            config[key] = os.environ[key]
    return config


def api(token, method, **payload):
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        # Не выводим URL ошибки: он содержит токен.
        raise RuntimeError(f"Telegram вернул HTTP {error.code}. Проверьте токен, канал и права бота.") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError(
            "Запрос к Telegram не завершён. Перед повторной отправкой проверьте канал: "
            "сообщение могло быть опубликовано."
        ) from None
    if not result.get("ok"):
        raise RuntimeError("Telegram отклонил запрос. Проверьте настройки и права бота.")
    return result["result"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("preview", "check", "publish"))
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--post", type=Path, default=ROOT / "posts" / "welcome.txt")
    args = parser.parse_args()
    config = read_config(args.env_file)
    channel = config.get("TELEGRAM_CHANNEL") or "@codelevel_pygo"
    text = None
    if args.command != "check":
        text = args.post.read_text(encoding="utf-8-sig").strip()
        if not text or len(text.encode("utf-16-le")) // 2 > 4096:
            raise ValueError("Публикация должна содержать от 1 до 4096 символов UTF-16.")
    if args.command == "preview":
        print(f"Канал: {channel}\n\n{text}")
        return
    token = config.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise ValueError("Заполните TELEGRAM_BOT_TOKEN в локальном .env или укажите --env-file.")
    bot = api(token, "getMe")
    chat = api(token, "getChat", chat_id=channel)
    if chat.get("type") != "channel":
        raise ValueError("Указанный адрес не является Telegram-каналом.")
    member = api(token, "getChatMember", chat_id=chat["id"], user_id=bot["id"])
    if member.get("status") != "creator" and not (
        member.get("status") == "administrator" and member.get("can_post_messages")
    ):
        raise ValueError("Боту нужны права администратора с разрешением публикации.")
    if args.command == "check":
        print(f"Бот @{bot['username']} может публиковать в {channel}.")
        return
    result = api(token, "sendMessage", chat_id=chat["id"], text=text)
    print(f"Опубликовано. ID сообщения: {result['message_id']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
