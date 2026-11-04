"""Онлайн-копия SQLite: python backup.py data/tasks.db backups/tasks-backup.db."""
from contextlib import closing
from pathlib import Path
import sqlite3
import sys


def backup(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_file() or destination.exists() or source == destination:
        raise ValueError('Нужны существующая база и новый путь назначения')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Резервируем имя до подключения, чтобы не перезаписать готовую копию.
    with destination.open('xb'):
        pass
    destination.chmod(0o600)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src, closing(sqlite3.connect(destination)) as dst:
        src.backup(dst)
        if dst.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Проверка целостности копии не пройдена')


if __name__=='__main__':
    backup(*sys.argv[1:])
    print('Резервная копия создана и проверена.')
