"""Сборка отдельной редакционной очереди. Ничего не отправляет в Telegram."""

from collections import Counter
from html import escape
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(html):
    parser = VisibleText()
    parser.feed(html)
    return ''.join(parser.parts)


def build(posts, expected_count, output=None):
    output = output or ROOT / 'pack'
    output.mkdir(parents=True, exist_ok=True)
    if len(posts) != expected_count:
        raise ValueError(f'Ожидалось {expected_count} публикаций, получено {len(posts)}')
    fingerprints = set()
    for index, post in enumerate(posts, 1):
        if post['number'] != index:
            raise ValueError('Нарушена последовательность публикаций')
        text = plain_text(post['html'])
        if not 150 <= len(text.encode('utf-16-le')) // 2 <= 4096:
            raise ValueError(f'Неподходящая длина публикации {index}')
        # Нумерация и заголовки не должны скрывать одинаковые тексты.
        body = re.sub(r'\s+', ' ', plain_text(post['body_html'])).strip()
        fingerprint = hashlib.sha256(body.encode()).hexdigest()
        if fingerprint in fingerprints:
            raise ValueError(f'Повтор содержимого в публикации {index}')
        fingerprints.add(fingerprint)
        if not post['source_urls'] or not post['learning_goal']:
            raise ValueError(f'Нет источника или учебной цели у публикации {index}')
    with (output / 'queue.jsonl').open('w', encoding='utf-8') as stream:
        for post in posts:
            stream.write(json.dumps(post, ensure_ascii=False) + '\n')
    modules = list(dict.fromkeys(post['module'] for post in posts))
    index_lines = ['# Редакционная очередь CodeLevel', '', f'Всего публикаций: {len(posts)}.', '',
                   'Материалы подготовлены. Отправка отслеживается отдельно в .course-publication-state.json.', '']
    for module_index, module in enumerate(modules, 1):
        selected = [p for p in posts if p['module'] == module]
        filename = f'{module_index:02d}.md'
        lines = [f'# {module}', '']
        for post in selected:
            lines.extend([f"## {post['number']:04d}. {post['title']}", '', post['markdown'], '',
                          'Источники: ' + ', '.join(post['source_urls']), '', '---', ''])
        (output / filename).write_text('\n'.join(lines), encoding='utf-8')
        index_lines.append(f'- [{module} — {selected[0]["number"]}–{selected[-1]["number"]}]({filename})')
    (output / 'README.md').write_text('\n'.join(index_lines)+'\n', encoding='utf-8')
    report = {'post_count':len(posts), 'modules':dict(Counter(p['module'] for p in posts)),
              'unique_bodies':len(fingerprints), 'telegram_length_check':'passed',
              'publication_status':'prepared_delivery_progress_in_course_state',
              'queue_sha256':hashlib.sha256((output/'queue.jsonl').read_bytes()).hexdigest()}
    (output / 'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    payload = json.dumps(posts, ensure_ascii=False).replace('<', '\\u003c')
    template = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>CodeLevel · редакционная очередь</title>
<style>body{font:16px system-ui;margin:0;background:#f4f5f7;color:#20252c}header{padding:28px 5%;background:#fff;border-bottom:1px solid #ddd}h1{font-size:26px;margin:0 0 12px}input,select,button{font:inherit;padding:10px;margin:5px 8px 5px 0}main{max-width:840px;margin:24px auto;padding:0 16px}article{background:white;padding:26px;margin:20px 0;border:1px solid #ddd;line-height:1.65}pre{overflow:auto;background:#f3f5f6;padding:14px}small{color:#59636e}a{color:#125f98}.post{white-space:pre-wrap}nav{display:flex;align-items:center;gap:8px}button{cursor:pointer}details{margin-top:16px}</style>
<header><h1>CodeLevel · редакционная очередь</h1><p>Подготовленные публикации. Просмотр не отправляет сообщения в канал.</p>
<input id="q" placeholder="Поиск по теме и тексту"><select id="module"><option value="">Все модули</option></select><span id="count"></span></header>
<main><nav><button id="prev">Назад</button><span id="page"></span><button id="next">Далее</button></nav><div id="posts"></div></main>
<script>const posts=__DATA__;const $=id=>document.getElementById(id);let page=0;const size=5;
for(const name of [...new Set(posts.map(p=>p.module))]){const o=document.createElement('option');o.value=name;o.textContent=name;$('module').append(o)}
function draw(){const q=$('q').value.toLowerCase();const m=$('module').value;const filtered=posts.filter(p=>(!m||p.module===m)&&(!q||JSON.stringify(p).toLowerCase().includes(q)));page=Math.max(0,Math.min(page,Math.max(0,Math.ceil(filtered.length/size)-1)));$('posts').replaceChildren();$('count').textContent=filtered.length+' публикаций';$('page').textContent=(page+1)+' / '+Math.max(1,Math.ceil(filtered.length/size));$('prev').disabled=page===0;$('next').disabled=(page+1)*size>=filtered.length;
for(const p of filtered.slice(page*size,(page+1)*size)){const article=document.createElement('article');const label=document.createElement('small');label.textContent=p.module+' · '+p.number+' / '+posts.length;article.append(label);const body=document.createElement('div');body.className='post';body.innerHTML=p.html.replace(/<tg-spoiler>/g,'<details><summary>Ответ</summary>').replace(/<\\/tg-spoiler>/g,'</details>');article.append(body);for(const url of p.source_urls){const a=document.createElement('a');a.href=url;a.textContent='Источник';a.target='_blank';a.rel='noopener';article.append(a,document.createTextNode(' '))}$('posts').append(article)}}
$('q').oninput=$('module').onchange=()=>{page=0;draw()};$('prev').onclick=()=>{page--;draw()};$('next').onclick=()=>{page++;draw()};draw();</script></html>'''
    (output / 'index.html').write_text(template.replace('__DATA__', payload),encoding='utf-8')
    return report


def make_post(number, module, title, goal, sections, sources, **extra):
    html_parts = []
    md_parts = []
    for kind, text in sections:
        if kind == 'code':
            html_parts.append('<pre>'+escape(text)+'</pre>')
            md_parts.append('```\n'+text+'\n```')
        elif kind == 'answer':
            html_parts.append('<tg-spoiler>'+escape(text)+'</tg-spoiler>')
            md_parts.append('**Разбор:** '+text)
        else:
            html_parts.append(escape(text))
            md_parts.append(text)
    body = '\n\n'.join(html_parts)
    full = f'<b>CodeLevel · {number:04d}\n{escape(title)}</b>\n\n{body}\n\n#CodeLevel #Разработка'
    return {'id':f'cl-{number:04d}', 'number':number, 'module':module, 'title':title,
            'learning_goal':goal, 'body_html':body, 'html':full, 'markdown':'\n\n'.join(md_parts),
            'parse_mode':'HTML', 'source_urls':sources, 'status':'prepared', **extra}
