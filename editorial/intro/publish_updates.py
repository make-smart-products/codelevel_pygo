"""Обновляет только существующие посты 19–23; новых сообщений не создаёт."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
sys.path.insert(0,str(PROJECT))
sys.path.insert(0,str(PROJECT/'editorial'))
from bot import api, read_config
from build_pack import plain_text


def edit_animation(token,channel,message_id,post,clip):
    path=ROOT/'media'/(clip['id']+'.mp4')
    thumbnail=ROOT/'media'/(clip['id']+'-poster.jpg')
    boundary=uuid.uuid4().hex
    media={'type':'animation','media':'attach://animation',
           'thumbnail':'attach://thumbnail','caption':post['caption_html'],'parse_mode':'HTML',
           'width':1080,'height':1350,'duration':24}
    fields={'chat_id':channel,'message_id':str(message_id),'media':json.dumps(media,ensure_ascii=False)}
    chunks=[]
    for name,value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode('utf-8'))
    for name,file,mime in [('animation',path,'video/mp4'),('thumbnail',thumbnail,'image/jpeg')]:
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{file.name}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
        chunks.append(file.read_bytes());chunks.append(b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    request=urllib.request.Request('https://api.telegram.org/bot'+token+'/editMessageMedia',
        data=b''.join(chunks),headers={'Content-Type':'multipart/form-data; boundary='+boundary},method='POST')
    try:
        with urllib.request.urlopen(request,timeout=120) as response:
            result=json.load(response)
    except urllib.error.HTTPError as error:
        try:
            reason=json.loads(error.read()).get('description','Telegram request rejected')
        except (ValueError,OSError):
            reason='Telegram request rejected'
        raise RuntimeError(f'HTTP {error.code}: '+reason.replace(token,'[redacted]')) from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise RuntimeError(f'Редактирование поста {message_id} не подтверждено. Проверь пост перед продолжением.') from None
    if not result.get('ok'):
        raise RuntimeError('Telegram не подтвердил редактирование.')
    return result['result']


def main():
    config=read_config(PROJECT/'.env')
    token=config.get('TELEGRAM_BOT_TOKEN')
    channel=config.get('TELEGRAM_CHANNEL') or '@codelevel_pygo'
    if not token or channel!='@codelevel_pygo':
        raise ValueError('Нужны настройки бота канала @codelevel_pygo.')
    me=api(token,'getMe')
    if me.get('username')!='codelevel_pygo_bot':
        raise ValueError('Токен принадлежит другому боту. Редактирование остановлено.')
    chat=api(token,'getChat',chat_id=channel)
    if chat.get('type')!='channel':
        raise ValueError('Не подтверждён тип канала.')
    posts=[json.loads(line) for line in (PROJECT/'editorial/pack/queue.jsonl').read_text(encoding='utf-8').splitlines()]
    clips=json.loads((ROOT/'storyboard.json').read_text(encoding='utf-8'))['clips']
    receipt_path=ROOT/'published.json'
    receipts=json.loads(receipt_path.read_text(encoding='utf-8')) if receipt_path.exists() else {'channel':channel,'messages':{}}
    for index,clip in enumerate(clips):
        post=posts[index]
        message_id=19+index
        if clip['message_id']!=message_id or post['id']!=f'cl-{index+1:04d}':
            raise ValueError('Нарушено соответствие постов и сообщений.')
        digest=hashlib.sha256((ROOT/'media'/(clip['id']+'.mp4')).read_bytes()).hexdigest()
        caption_digest=hashlib.sha256(post['caption_html'].encode()).hexdigest()
        previous=receipts['messages'].get(str(message_id),{})
        if previous.get('sha256')==digest and previous.get('caption_sha256')==caption_digest:
            print(f'Already confirmed: {message_id}',flush=True)
            continue
        result=edit_animation(token,chat['id'],message_id,post,clip)
        if result.get('message_id')!=message_id or not result.get('animation'):
            raise RuntimeError('Telegram не вернул ожидаемое сообщение с анимацией.')
        if result.get('caption')!=plain_text(post['caption_html']):
            raise RuntimeError('Подпись в ответе Telegram отличается от подготовленной.')
        animation=result['animation']
        receipts['messages'][str(message_id)]={
            'post_id':post['id'],'animation_file_id':animation['file_id'],
            'animation_file_unique_id':animation['file_unique_id'],'sha256':digest,
            'caption_sha256':caption_digest,'width':animation['width'],'height':animation['height'],
            'duration':animation['duration'],'confirmed_at':datetime.now(timezone.utc).isoformat(),
            'url':f'https://t.me/codelevel_pygo/{message_id}'}
        receipt_path.write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(f'Updated existing message {message_id}: {animation["width"]}x{animation["height"]}, {animation["duration"]}s',flush=True)
        time.sleep(1.2)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError,RuntimeError,OSError) as error:
        print('Ошибка: '+str(error),file=sys.stderr)
        sys.exit(1)
