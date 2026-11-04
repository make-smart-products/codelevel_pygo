from pathlib import Path
from contextlib import closing
import sqlite3
import os
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bot import Store, TelegramError
from backup import backup


class BotTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory(dir=os.environ.get('TEST_TMPDIR'))
        self.addCleanup(self.folder.cleanup)
        self.path=Path(self.folder.name)/'notes.db'
        self.store=Store(self.path,42)
        self.next_update=1

    def command(self,text,owner=42,chat_type='private'):
        update={'update_id':self.next_update,'message':{'text':text,'chat':{'id':owner,'type':chat_type},'from':{'id':owner}}}
        self.next_update+=1
        self.store.process(update)
        return update

    def rows(self):
        with closing(sqlite3.connect(self.path)) as db:
            return db.execute('SELECT id,kind,body,done FROM items ORDER BY id').fetchall()

    def test_create_list_done_delete(self):
        self.command('/add Сделать тесты')
        self.command('/note Идея проекта')
        self.assertEqual(len(self.rows()),2)
        self.command('/done 1')
        self.assertEqual(self.rows()[0][3],1)
        self.command('/done 2')
        self.assertEqual(self.rows()[1][3],0)
        self.command('/delete 1')
        self.assertEqual(self.rows()[0][0],2)

    def test_only_owner_private_chat(self):
        self.command('/add Чужая запись',owner=99)
        self.command('/add Из группы',chat_type='group')
        self.assertEqual(self.rows(),[])
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM outbox').fetchone()[0],0)

    def test_duplicate_update_not_applied(self):
        update=self.command('/add Один раз')
        self.store.process(update)
        self.assertEqual(len(self.rows()),1)
        self.assertEqual(self.store.offset(),2)

    def test_bad_arguments_and_sql_injection(self):
        for text in ['/add   ','/add '+'x'*1501,'/done -1','/delete 1 OR 1=1','/list 0']:
            self.command(text)
        self.assertEqual(self.rows(),[])
        self.command("/note '); DROP TABLE items; --")
        self.assertEqual(len(self.rows()),1)

    def test_unicode_search(self):
        self.command('/note Программирование')
        self.command('/search ПРОГРАММИРОВАНИЕ')
        with closing(sqlite3.connect(self.path)) as db:
            replies=[r[0] for r in db.execute('SELECT text FROM outbox')]
        self.assertTrue(any('#1' in r and 'Программирование' in r for r in replies))

    def test_persistence_and_backup(self):
        self.command('/add Сохранить')
        self.assertEqual(Store(self.path,42).offset(),2)
        target=Path(self.folder.name)/'backup.db'
        backup(self.path,target)
        with closing(sqlite3.connect(target)) as db:
            self.assertEqual(db.execute('SELECT body FROM items').fetchone()[0],'Сохранить')

    def test_sent_replies_not_resent(self):
        self.command('/add Проверка')
        telegram=Mock()
        self.store.deliver(telegram,pause=lambda _:None)
        self.store.deliver(telegram,pause=lambda _:None)
        self.assertEqual(telegram.call.call_count,1)

    def test_unknown_delivery_blocks_retry(self):
        self.command('/add Проверка')
        telegram=Mock()
        telegram.call.side_effect=TelegramError('timeout')
        with self.assertRaises(TelegramError):
            self.store.deliver(telegram,pause=lambda _:None)
        other=Mock()
        with self.assertRaises(RuntimeError):
            self.store.deliver(other,pause=lambda _:None)
        other.call.assert_not_called()
        self.store.resolve(1,delivered=True)
        self.store.deliver(other,pause=lambda _:None)
        other.call.assert_not_called()

    def test_confirmed_failed_delivery_can_be_retried(self):
        self.command('/add Проверка')
        telegram=Mock()
        telegram.call.side_effect=TelegramError('timeout')
        with self.assertRaises(TelegramError):
            self.store.deliver(telegram,pause=lambda _:None)
        self.store.resolve(1,delivered=False)
        good=Mock()
        self.store.deliver(good,pause=lambda _:None)
        good.call.assert_called_once()

    def test_paging(self):
        for i in range(7):
            self.command('/add Задача '+str(i))
        self.command('/list 2')
        with closing(sqlite3.connect(self.path)) as db:
            last=[r[0] for r in db.execute('SELECT text FROM outbox ORDER BY id DESC LIMIT 3')]
        self.assertEqual(sum('#' in row for row in last),2)


if __name__=='__main__':
    unittest.main()
