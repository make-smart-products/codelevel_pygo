"""Заменить аватарку канала: python channel_photo.py assets/channel-avatar.png."""

from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid

from bot import ROOT, api, read_config


def main():
    config = read_config(ROOT / ".env")
    token = config.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Токен не настроен.")
    channel = config.get("TELEGRAM_CHANNEL") or "@codelevel_pygo"
    bot = api(token, "getMe")
    chat = api(token, "getChat", chat_id=channel)
    member = api(token, "getChatMember", chat_id=chat["id"], user_id=bot["id"])
    if member.get("status") != "creator" and not member.get("can_change_info"):
        raise ValueError("Боту нужно право администратора «Изменение профиля канала».")
    photo = Path(sys.argv[1]).read_bytes()
    boundary = uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat["id"]}\r\n'
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="avatar.png"\r\n'
        'Content-Type: image/png\r\n\r\n'
    ).encode() + photo + f"\r\n--{boundary}--\r\n".encode()
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/setChatPhoto", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST",
    )
    import json
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"Telegram вернул HTTP {error.code} при смене фото.") from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError("Сетевая ошибка при смене фото. Проверьте аватарку канала.") from None
    if not result.get("ok"):
        raise RuntimeError("Telegram отклонил смену фото.")
    updated = api(token, "getChat", chat_id=chat["id"])
    if not updated.get("photo"):
        raise RuntimeError("Telegram принял запрос, но новое фото не подтверждено.")
    print("Фото канала обновлено и подтверждено Telegram.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, RuntimeError, OSError, IndexError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        sys.exit(1)
