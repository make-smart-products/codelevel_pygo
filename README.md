# CodeLevel | Python & Go

Канал: https://t.me/codelevel_pygo

Python 3.12+, без сторонних библиотек. Команды выполняются в папке проекта.

1. Скопируйте `.env.example` в `.env` и заполните `TELEGRAM_BOT_TOKEN` локально.
2. `python bot.py preview` — просмотр первого поста без подключения к Telegram.
3. `python bot.py check` — проверка бота, канала и прав без публикации.
4. `python bot.py publish` — отправка первого поста в канал.

Можно указать другой файл настроек: `python bot.py check --env-file C:\path\to\.env`.
Формат: строки `TELEGRAM_BOT_TOKEN=...` и `TELEGRAM_CHANNEL=@codelevel_pygo`.
Переменные окружения с такими же именами имеют приоритет.

Пост хранится в `posts/welcome.txt`. Другой пост: `python bot.py publish --post posts/another.txt`.
Каждый запуск `publish` отправляет отдельное сообщение; автоматических повторов нет.
При сетевой ошибке проверьте канал перед повторным запуском.

Токен не сохраняется в коде и не выводится в сообщениях об ошибках API.
Файл `.env` исключён из git.

## Облачные публикации

GitHub Actions: `.github/workflows/publish.yml`, cron `17 */3 * * *` (UTC).
Это 00:17, 03:17, 06:17, 09:17, 12:17, 15:17, 18:17 и 21:17 по Москве.
Работает при выключенном ноутбуке и закрытом Codex. GitHub может задерживать
или пропускать запуски: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

В Actions Secrets хранится `TELEGRAM_BOT_TOKEN`. В код и git токен не попадает.
Для ручной проверки запускайте workflow с `check_only=true` (по умолчанию).
`check_only=false` публикует очередное задание, если в текущем трёхчасовом окне
расписания ещё не было поста. Используются окна с началом на 17-й минуте.
Задержки GitHub могут менять фактический интервал между сообщениями.

Посты чередуют Python и Go. `content.py` создаёт задания по 8 темам для каждого
языка, изменяя числовые данные в каждом цикле. Ответ и объяснение скрыты под
спойлером. Это шаблонные упражнения, без платных сервисов и ИИ API.
Для развития программы обучения добавляйте новые темы в `content.py`.

Состояние в `.publication-state.json` сохраняется коммитами перед отправкой
и после неё. Повторные параллельные запуски исключены настройкой concurrency.
При неопределённом результате отправки следующий запуск останавливается,
чтобы не дублировать пост. Проверьте канал: если пост доставлен, увеличьте
`next_index` на 1, запишите время в `last_sent_at` (ISO UTC) и ID сообщения;
если не доставлен, оставьте индекс. Затем установите `pending: null`.
Остановка расписания: GitHub → Actions → CodeLevel every 3 hours → Disable workflow.

Проверки: `python -m unittest discover -s tests -v`.

## Аватарка

`assets/channel-avatar.png` создана встроенным ImageGen.
Промпт сохранён в `assets/avatar-prompt.txt`.
Установить фото: `python channel_photo.py assets/channel-avatar.png`.
Боту требуется право изменения профиля канала.

Документация API: https://core.telegram.org/bots/api#sendmessage
