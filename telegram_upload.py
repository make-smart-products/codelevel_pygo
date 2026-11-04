"""Multipart uploads without printing token-bearing URLs."""

import json
from pathlib import Path
import urllib.error
import urllib.request
import uuid


def upload(token, method, field, path, **fields):
    path = Path(path)
    boundary = uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        if isinstance(value, (dict, list, bool)):
            value = json.dumps(value, ensure_ascii=False)
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode('utf-8'))
    mime = 'image/png' if path.suffix.lower() == '.png' else 'image/jpeg'
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{path.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
    chunks.extend([path.read_bytes(), f'\r\n--{boundary}--\r\n'.encode()])
    request = urllib.request.Request('https://api.telegram.org/bot'+token+'/'+method,
        data=b''.join(chunks),headers={'Content-Type':'multipart/form-data; boundary='+boundary},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        try:
            description = json.loads(error.read()).get('description','Telegram rejected upload')
        except (ValueError,OSError):
            description = 'Telegram rejected upload'
        raise RuntimeError(f'HTTP {error.code}: '+description.replace(token,'[redacted]')) from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise RuntimeError('Доставка файла не подтверждена. Проверьте канал перед повтором.') from None
    if not result.get('ok'):
        raise RuntimeError('Telegram не подтвердил загрузку.')
    return result['result']
