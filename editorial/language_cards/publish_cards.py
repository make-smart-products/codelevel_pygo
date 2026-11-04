"""Публикация пяти согласованных обзорных карточек после удаления старых постов."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
sys.path.insert(0,str(PROJECT))
sys.path.insert(0,str(PROJECT/'editorial'))
from bot import api, read_config
from build_pack import plain_text
from telegram_upload import upload


def main():
    config=read_config(PROJECT/'.env')
    token=config.get('TELEGRAM_BOT_TOKEN')
    if not token or (config.get('TELEGRAM_CHANNEL') or '@codelevel_pygo')!='@codelevel_pygo':
        raise ValueError('Нужны настройки канала @codelevel_pygo')
    me=api(token,'getMe')
    if me.get('username')!='codelevel_pygo_bot':
        raise ValueError('Токен другого бота')
    cards=json.loads((ROOT/'cards.json').read_text(encoding='utf-8'))
    path=PROJECT/'.skills-publication-state.json'
    state=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {
        'version':'illustrated-skills-v1','next_index':0,'last_sent_at':'1970-01-01T00:00:00+00:00',
        'pending':None,'batch':None}
    receipts_path=ROOT/'published.json'
    receipts=json.loads(receipts_path.read_text(encoding='utf-8')) if receipts_path.exists() else {'channel':'@codelevel_pygo','posts':[]}
    assets_path=ROOT/'assets.json'
    assets=json.loads(assets_path.read_text(encoding='utf-8')) if assets_path.exists() else {}
    if state.get('pending'):
        raise RuntimeError('Есть неподтверждённая доставка. Сначала проверьте канал.')
    for index,card in enumerate(cards):
        if index<state['next_index']:
            continue
        file=ROOT/'images'/(card['id']+'.png')
        if file.stat().st_size>=9*1024*1024:
            raise ValueError('Изображение слишком большое')
        if len(plain_text(card['caption']).encode('utf-16-le'))//2>1024:
            raise ValueError('Подпись слишком длинная')
        state['pending']={'index':index,'event_id':'overview-'+card['id'],'kind':'photo'}
        path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        result=upload(token,'sendPhoto','photo',file,chat_id='@codelevel_pygo',caption=card['caption'],parse_mode='HTML')
        photo=result['photo'][-1]
        assets[card['id']]={'file_id':photo['file_id'],'file_unique_id':photo['file_unique_id'],
            'path':'editorial/language_cards/images/'+file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        assets_path.write_text(json.dumps(assets,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        receipts['posts'].append({'id':card['id'],'message_id':result['message_id'],
            'url':f"https://t.me/codelevel_pygo/{result['message_id']}"})
        receipts_path.write_text(json.dumps(receipts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        state.update(next_index=index+1,last_sent_at=datetime.now(timezone.utc).isoformat(),
            last_message_id=result['message_id'],last_event_id='overview-'+card['id'],pending=None)
        path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print('Published',card['id'],result['message_id'],flush=True)
        time.sleep(3.1)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        main()
    except (ValueError,RuntimeError,OSError) as error:
        print('Ошибка:',str(error))
        sys.exit(1)
