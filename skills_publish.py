"""Иллюстрированные уроки и quiz каждые 10 минут, по 5 материалов."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from bot import ROOT, api, read_config
from go_server_content import GO_HTTP_EVENTS
from skills_content import CARDS, make_event
from telegram_upload import upload

STATE=ROOT/'.skills-publication-state.json'
POSTS_PER_RUN=5
INTERVAL_SECONDS=600
SCHEDULE_OFFSET_SECONDS=7*60


def queued_event(index, state):
    start = state.get('go_http_start')
    if start is None or index < start:
        return make_event(index)
    if index < start + len(GO_HTTP_EVENTS):
        return GO_HTTP_EVENTS[index - start]
    return make_event(index - len(GO_HTTP_EVENTS))


def image_fingerprint(event):
    if event.get('image_path'):
        return 'sha256:' + hashlib.sha256((ROOT / event['image_path']).read_bytes()).hexdigest()
    assets = json.loads((CARDS / 'assets.json').read_text(encoding='utf-8'))
    asset = assets[event['asset']]
    if asset.get('sha256'):
        return 'sha256:' + asset['sha256']
    return 'telegram:' + asset['file_unique_id']


def save_state(state):
    if os.environ.get('GITHUB_ACTIONS')!='true':
        raise RuntimeError('Фиксация облачного прогресса разрешена в GitHub Actions.')
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for command in (['git','add','--',STATE.name],
                    ['git','commit','-m','Update illustrated skills progress [skip ci]'],
                    ['git','push','origin','HEAD:main']):
        subprocess.run(command,cwd=ROOT,check=True,capture_output=True)


def send_event(token,channel,event):
    image = event.get('image_path')
    if image:
        photo = 'attach://picture'
    else:
        assets=json.loads((CARDS/'assets.json').read_text(encoding='utf-8'))
        photo=assets[event['asset']]['file_id']
    if event['kind']=='photo':
        if image:
            return upload(token, 'sendPhoto', 'photo', ROOT / image,
                chat_id=channel, caption=event['caption'], parse_mode='HTML')
        return api(token,'sendPhoto',chat_id=channel,photo=photo,caption=event['caption'],parse_mode='HTML')
    if event['kind']=='quiz':
        fields=dict(chat_id=channel,type='quiz',is_anonymous=True,
            question=event['question'],options=[{'text':value} for value in event['options']],
            # Поддержка нового и прежнего имени поля. Индекс в обоих одинаков.
            correct_option_ids=[event['correct']],correct_option_id=event['correct'],
            explanation=event['explanation'],allows_multiple_answers=False,
            description=event['description'],description_parse_mode='HTML',
            media={'type':'photo','media':photo})
        if image:
            result = upload(token, 'sendPoll', 'picture', ROOT / image, **fields)
        else:
            result = api(token, 'sendPoll', **fields)
        if result.get('poll',{}).get('type')!='quiz':
            raise RuntimeError('Telegram не подтвердил режим викторины. Проверьте канал.')
        return result
    raise ValueError('Неизвестный тип материала')


def publish_batch(state,now,send,persist,pause=time.sleep):
    if state.get('pending'):
        raise RuntimeError('Есть неподтверждённая отправка: проверьте канал и pending перед продолжением.')
    slot=int((now.timestamp()-SCHEDULE_OFFSET_SECONDS)//INTERVAL_SECONDS)
    last=datetime.fromisoformat(state['last_sent_at'])
    last_slot=int((last.timestamp()-SCHEDULE_OFFSET_SECONDS)//INTERVAL_SECONDS)
    batch=state.get('batch')
    if not batch and slot<=last_slot:
        print('В текущем 10-минутном окне материалы уже опубликованы.')
        return
    if not batch:
        batch={'slot':slot,'end_index':state['next_index']+POSTS_PER_RUN}
        state['batch']=batch
        # Начинаем практикум на границе новой пятёрки. Старую очередь продолжим после него.
        state.setdefault('go_http_start', state['next_index'])
    if 'used_image_hashes' not in state:
        state['used_image_hashes'] = sorted({
            image_fingerprint(queued_event(index, state))
            for index in range(state['next_index'])
        })
    while state['next_index']<batch['end_index']:
        index=state['next_index']
        event=queued_event(index, state)
        picture = image_fingerprint(event)
        if picture in state['used_image_hashes']:
            print(f"Ожидается новая иллюстрация для {event['id']}. Повторная картинка не отправлена.", flush=True)
            return
        digest=hashlib.sha256(json.dumps(event,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        state['pending']={'index':index,'event_id':event['id'],'kind':event['kind'],'sha256':digest}
        persist(state)  # Не отправляем, если резервирование не удалось сохранить.
        result=send(event)
        state['used_image_hashes'].append(picture)
        state.update(next_index=index+1,last_event_id=event['id'],last_message_id=result['message_id'],
            last_sent_at=now.isoformat(),pending=None)
        if index+1==batch['end_index']:
            state['batch']=None
        persist(state)
        print(f"Published {event['kind']} {event['id']}: {result['message_id']}",flush=True)
        if state['batch']:
            pause(3.1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    state=json.loads(STATE.read_text(encoding='utf-8'))
    if args.preview:
        batch = state.get('batch')
        state.setdefault('go_http_start', batch['end_index'] if batch else state['next_index'])
        print(json.dumps([queued_event(i, state) for i in range(state['next_index'],state['next_index']+5)],ensure_ascii=False,indent=2))
        return
    config=read_config(ROOT/'.env')
    token=config.get('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError('Не настроен TELEGRAM_BOT_TOKEN.')
    channel=config.get('TELEGRAM_CHANNEL') or '@codelevel_pygo'
    me=api(token,'getMe')
    chat=api(token,'getChat',chat_id=channel)
    member=api(token,'getChatMember',chat_id=chat['id'],user_id=me['id'])
    if chat.get('type')!='channel' or not member.get('can_post_messages'):
        raise ValueError('Не подтверждены канал и права публикации.')
    if args.check:
        print('Подключение проверено. Публикация не выполнялась.')
        return
    if os.environ.get('GITHUB_ACTIONS')!='true':
        raise ValueError('Публикации выполняются облачным workflow. Для просмотра используйте --preview.')
    publish_batch(state,datetime.now(timezone.utc),
        lambda event:send_event(token,chat['id'],event),save_state)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError) as error:
        print('Ошибка: '+str(error),file=sys.stderr)
        sys.exit(1)
