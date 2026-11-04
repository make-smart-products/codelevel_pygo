"""Редакционная замена первых пяти постов без сдвига нумерации курса."""

from html import escape
import json
from pathlib import Path

from build_pack import plain_text

ROOT=Path(__file__).resolve().parent


def apply_intro(posts):
    clips=json.loads((ROOT/'storyboard.json').read_text(encoding='utf-8'))['clips']
    receipts_path=ROOT/'published.json'
    receipts=json.loads(receipts_path.read_text(encoding='utf-8')) if receipts_path.exists() else {'messages':{}}
    for index,clip in enumerate(clips):
        post=posts[index]
        _,body=clip['caption'].split('\n\n',1)
        links=' · '.join(f'<a href="{escape(url,quote=True)}">Источник {i+1}</a>' for i,url in enumerate(clip['sources']))
        html=f'<b>CodeLevel · {index+1:04d}\n{escape(clip["title"])}</b>\n\n{escape(body)}\n\n{links}'
        if len(plain_text(html).encode('utf-16-le'))//2>1024:
            raise ValueError('Подпись превышает лимит Telegram: '+clip['id'])
        post.update(title=clip['title'],learning_goal=clip['goal'],topic='Введение: Python и Go',
            body_html=escape(body),html=html,caption_html=html,
            markdown=clip['caption']+'\n\nАнимация: ../intro/media/'+clip['id']+'.mp4',
            source_urls=clip['sources'],content_revision='python-go-motion-2026-11-04',
            animation={'path':'editorial/intro/media/'+clip['id']+'.mp4','duration':24,
                       'width':1080,'height':1350,'fps':24,'silent':True},
            published_message_id=clip['message_id'])
        receipt=receipts['messages'].get(str(clip['message_id']))
        if receipt:
            post['animation']['file_id']=receipt['animation_file_id']
    return posts
