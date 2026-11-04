"""Личный Telegram-бот заметок и задач. Итог публикации 60. Python 3.12+."""

import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
HELP = ('Личные заметки и задачи\n\n/add текст — новая задача\n/note текст — заметка\n'
        '/list [страница] — активные задачи\n/notes [страница] — заметки\n'
        '/done ID — завершить задачу\n/delete ID — удалить запись\n/search текст — поиск\n'
        '/export [страница] — экспорт записей в JSON сообщениями\n/help — команды')


def config():
    values = {}
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, separator, value = line.partition('=')
                if not separator:
                    raise ValueError('В .env нужны строки ИМЯ=значение')
                values[key.strip()] = value.strip().strip('"\'')
    for key in ('TELEGRAM_BOT_TOKEN','TELEGRAM_OWNER_ID','NOTES_DB'):
        if key in os.environ:
            values[key] = os.environ[key]
    return values


class TelegramError(RuntimeError):
    pass


class Telegram:
    def __init__(self, token):
        self.token = token

    def call(self, method, **payload):
        request = urllib.request.Request('https://api.telegram.org/bot'+self.token+'/'+method,
            data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'},method='POST')
        try:
            with urllib.request.urlopen(request,timeout=70) as response:
                result = json.load(response)
        except (urllib.error.URLError,TimeoutError,OSError):
            # Исключения urllib содержат URL с токеном — не передаём их дальше.
            raise TelegramError('Запрос Telegram не подтверждён: '+method) from None
        if not result.get('ok'):
            raise TelegramError('Telegram отклонил метод '+method)
        return result['result']


class Store:
    def __init__(self, path, owner_id):
        self.path, self.owner_id = Path(path), int(owner_id)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as db, db:
            db.executescript('''CREATE TABLE IF NOT EXISTS items(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL CHECK(kind IN ('task','note')),
                body TEXT NOT NULL CHECK(length(body) BETWEEN 1 AND 1500),
                done INTEGER NOT NULL DEFAULT 0 CHECK(done IN (0,1)),
                created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value INTEGER NOT NULL);
                INSERT OR IGNORE INTO settings VALUES('next_offset',0);
                CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,text TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending'
                CHECK(state IN ('pending','sending','sent')));
                CREATE INDEX IF NOT EXISTS idx_items_kind_done ON items(kind,done,id);
                CREATE INDEX IF NOT EXISTS idx_outbox_state ON outbox(state,id);''')

    def connection(self):
        db = sqlite3.connect(self.path,timeout=5)
        db.row_factory = sqlite3.Row
        db.create_function('casefold',1,lambda text:text.casefold(),deterministic=True)
        return closing(db)

    def offset(self):
        with self.connection() as db:
            return db.execute("SELECT value FROM settings WHERE key='next_offset'").fetchone()[0]

    def process(self, update):
        update_id = update.get('update_id')
        if not isinstance(update_id,int):
            return
        with self.connection() as db, db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute("SELECT value FROM settings WHERE key='next_offset'").fetchone()[0]
            if update_id < previous:
                return
            message = update.get('message',{})
            chat = message.get('chat',{})
            sender = message.get('from',{})
            if chat.get('type')=='private' and sender.get('id')==self.owner_id and chat.get('id')==self.owner_id:
                text = message.get('text')
                if isinstance(text,str):
                    replies = self.command(db,text)
                    for reply in replies:
                        for start in range(0,len(reply),1700):
                            db.execute('INSERT INTO outbox(chat_id,text) VALUES (?,?)',(self.owner_id,reply[start:start+1700]))
            db.execute("UPDATE settings SET value=? WHERE key='next_offset'",(update_id+1,))

    def command(self, db, text):
        command, _, argument = text.strip().partition(' ')
        command = command.split('@',1)[0].lower()
        argument = argument.strip()
        if command in ('/start','/help'):
            return [HELP]
        if command in ('/add','/note'):
            if not 1 <= len(argument) <= 1500:
                return ['После команды нужен текст длиной 1–1500 символов.']
            kind = 'task' if command=='/add' else 'note'
            cursor=db.execute('INSERT INTO items(kind,body,created_at) VALUES (?,?,?)',
                (kind,argument,datetime.now(timezone.utc).isoformat()))
            return [f'Сохранено: #{cursor.lastrowid}']
        if command in ('/done','/delete'):
            if not argument.isascii() or not argument.isdecimal() or len(argument)>12 or int(argument)<1:
                return ['Укажи положительный ID записи, например /done 12.']
            item_id = int(argument)
            if command=='/delete':
                result=db.execute('DELETE FROM items WHERE id=?',(item_id,))
                return ['Запись удалена.' if result.rowcount else 'Запись не найдена.']
            result=db.execute("UPDATE items SET done=1 WHERE id=? AND kind='task' AND done=0",(item_id,))
            return ['Задача завершена.' if result.rowcount else 'Активная задача не найдена.']
        if command in ('/list','/notes','/export'):
            if argument and (not argument.isascii() or not argument.isdecimal() or len(argument)>7 or int(argument)<1):
                return ['Номер страницы должен быть положительным целым числом.']
            page=int(argument or '1')
            if command=='/export':
                rows=db.execute('SELECT * FROM items ORDER BY id LIMIT 1 OFFSET ?', (page-1,)).fetchall()
                count=db.execute('SELECT count(*) FROM items').fetchone()[0]
                if not rows:
                    return ['На этой странице записей нет.']
                result=json.dumps(dict(rows[0]),ensure_ascii=False)
                return [f'Экспорт: {page}/{count}\n{result}\n\nСледующая запись: /export {page+1}' if page<count else f'Экспорт: {page}/{count}\n{result}\n\nПоследняя запись.']
            where="kind='task' AND done=0" if command=='/list' else "kind='note'"
            rows=db.execute('SELECT * FROM items WHERE '+where+' ORDER BY id DESC LIMIT 5 OFFSET ?',((page-1)*5,)).fetchall()
            count=db.execute('SELECT count(*) FROM items WHERE '+where).fetchone()[0]
            return self.format_rows(rows,f'Страница {page}. Всего: {count}.\nКоманда страницы: {command} {page+1}')
        if command=='/search':
            if not 1<=len(argument)<=200:
                return ['После /search нужен запрос длиной 1–200 символов.']
            rows=db.execute('SELECT * FROM items WHERE instr(casefold(body),casefold(?))>0 ORDER BY id DESC LIMIT 10',(argument,)).fetchall()
            return self.format_rows(rows,'До 10 последних совпадений. Уточни запрос для более точного поиска.')
        return ['Неизвестная команда. Используй /help.']

    @staticmethod
    def format_rows(rows, heading):
        if not rows:
            return ['Записей не найдено.']
        # Каждый элемент отдельным сообщением: запись до 1500 символов
        # гарантированно помещается в лимит Telegram даже с emoji UTF-16.
        replies=[heading]
        for row in rows:
            state='готово' if row['done'] else ('задача' if row['kind']=='task' else 'заметка')
            replies.append(f"#{row['id']} · {state}\n{row['body']}")
        return replies

    def deliver(self, telegram, pause=time.sleep):
        with self.connection() as db:
            uncertain=db.execute("SELECT id FROM outbox WHERE state='sending' LIMIT 1").fetchone()
            if uncertain:
                raise RuntimeError(f'Доставка #{uncertain[0]} не подтверждена. Проверь чат и выполни resolve.')
        while True:
            with self.connection() as db, db:
                db.execute('BEGIN IMMEDIATE')
                row=db.execute("SELECT * FROM outbox WHERE state='pending' ORDER BY id LIMIT 1").fetchone()
                if not row:
                    return
                db.execute("UPDATE outbox SET state='sending' WHERE id=?",(row['id'],))
            telegram.call('sendMessage',chat_id=row['chat_id'],text=row['text'])
            with self.connection() as db, db:
                db.execute("UPDATE outbox SET state='sent' WHERE id=?",(row['id'],))
            pause(1.1)

    def resolve(self, outbox_id, delivered):
        with self.connection() as db, db:
            result=db.execute("UPDATE outbox SET state=? WHERE id=? AND state='sending'",
                ('sent' if delivered else 'pending',outbox_id))
            if not result.rowcount:
                raise ValueError('Неопределённая доставка с таким ID не найдена')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['run','check','resolve'])
    parser.add_argument('--outbox-id',type=int)
    decision=parser.add_mutually_exclusive_group()
    decision.add_argument('--delivered',action='store_true')
    decision.add_argument('--retry',action='store_true')
    args=parser.parse_args()
    values=config()
    token=values.get('TELEGRAM_BOT_TOKEN')
    owner=values.get('TELEGRAM_OWNER_ID','')
    if not owner.isdecimal() or int(owner)<=0:
        raise ValueError('Задай TELEGRAM_OWNER_ID — числовой ID владельца')
    path=Path(values.get('NOTES_DB','data/notes.db'))
    if not path.is_absolute():
        path=ROOT/path
    store=Store(path,int(owner))
    if args.command=='resolve':
        if not args.outbox_id or not (args.delivered or args.retry):
            raise ValueError('Нужны --outbox-id и --delivered либо --retry')
        store.resolve(args.outbox_id,args.delivered)
        print('Статус доставки обновлён.')
        return
    if not token:
        raise ValueError('Задай токен отдельного Telegram-бота в локальном .env')
    telegram=Telegram(token)
    me=telegram.call('getMe')
    webhook=telegram.call('getWebhookInfo')
    if webhook.get('url'):
        raise ValueError('Для этого бота настроен webhook. Отключи его перед long polling.')
    if args.command=='check':
        print('Подключён бот @'+me['username']+'. Long polling доступен. Сообщения не отправлялись.')
        return
    print('Бот запущен. Остановка: Ctrl+C. Тексты заметок в журнал не выводятся.')
    while True:
        store.deliver(telegram)
        try:
            updates=telegram.call('getUpdates',offset=store.offset(),timeout=50,allowed_updates=['message'])
        except TelegramError:
            print('Не удалось получить обновления. Повтор через 5 секунд.')
            time.sleep(5)
            continue
        for update in updates:
            store.process(update)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except KeyboardInterrupt:
        print('Бот остановлен.')
    except (ValueError,RuntimeError,OSError) as error:
        print('Ошибка: '+str(error),file=sys.stderr)
        sys.exit(1)
