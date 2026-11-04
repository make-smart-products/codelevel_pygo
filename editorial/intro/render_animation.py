"""Авторская motion-графика: 5 MP4 по 24 секунды, 1080×1350, без звука.

Рендер сцен — Pillow, кодирование H.264 — установленный imageio_ffmpeg.
Не использует сетевые изображения, чужие видеоролики или вымышленные бенчмарки.
"""

import argparse
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'media'
W,H=1080,1350
BG='#0b1320'; PANEL='#122236'; LINE='#30465b'
WHITE='#f3f6fa'; MUTED='#a8b8c8'; PY='#ffd46b'; GO='#51d1e8'; RED='#ff918c'


@lru_cache(maxsize=100)
def font(size=36,bold=False,mono=False):
    filename='consolab.ttf' if mono and bold else 'consola.ttf' if mono else 'segoeuib.ttf' if bold else 'segoeui.ttf'
    path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/filename
    if not path.exists():
        raise RuntimeError('Нужен шрифт Segoe UI / Consolas или адаптация путей для своей ОС.')
    return ImageFont.truetype(str(path),size)


def ease(value):
    value=max(0,min(1,value))
    return value*value*(3-2*value)


def text(draw,xy,value,size=36,fill=WHITE,bold=False,mono=False,anchor='lt'):
    draw.text(xy,str(value),font=font(size,bold,mono),fill=fill,anchor=anchor)


def wrap(value,width,size=36,bold=False,mono=False):
    f=font(size,bold,mono)
    lines=[]
    for paragraph in value.split('\n'):
        line=''
        for word in paragraph.split():
            candidate=(line+' '+word).strip()
            if line and f.getlength(candidate)>width:
                lines.append(line);line=word
            else:
                line=candidate
        lines.append(line)
    return lines


def paragraph(draw,x,y,value,width=928,size=36,fill=WHITE,bold=False,max_lines=4,mono=False):
    lines=wrap(value,width,size,bold,mono)
    if len(lines)>max_lines:
        raise ValueError(f'Текст не помещается: {value!r} ({len(lines)} строк)')
    for line in lines:
        text(draw,(x,y),line,size,fill,bold,mono)
        y+=round(size*1.35)
    return y


def panel(draw,box,outline=LINE,fill=PANEL,radius=24,width=2):
    draw.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)


def arrow(draw,start,end,color=LINE,width=4):
    draw.line([start,end],fill=color,width=width)
    x,y=end
    angle=math.atan2(y-start[1],x-start[0])
    points=[end,(x-15*math.cos(angle-.5),y-15*math.sin(angle-.5)),(x-15*math.cos(angle+.5),y-15*math.sin(angle+.5))]
    draw.polygon(points,fill=color)


def dot(draw,x,y,color,radius=9):
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color)


def common(clip,scene,clip_index,scene_index):
    image=Image.new('RGB',(W,H),BG)
    d=ImageDraw.Draw(image)
    text(d,(76,50),'CODELEVEL  /  PYTHON + GO',23,MUTED,True)
    text(d,(1004,50),f'{clip_index+1:02d} / 05',23,MUTED,mono=True,anchor='rt')
    size=66
    while len(wrap(scene['title'],928,size,True))>2:
        size-=2
    paragraph(d,76,140,scene['title'],size=size,bold=True,max_lines=2)
    paragraph(d,76,332,scene['subtitle'],size=33,fill=MUTED,max_lines=3)
    paragraph(d,76,1175,scene['note'],size=27,fill=MUTED,max_lines=3)
    text(d,(76,1299),'УСТРОЙСТВО  ·  ВЫБОР  ·  ПРАКТИКА',19,MUTED)
    text(d,(1004,1299),f'{scene_index+1}/3',21,MUTED,mono=True,anchor='rt')
    return image


def pipeline(d,y,values,color):
    text(d,(76,y-65),values[0],28,color,True)
    xs=[76,420,764]
    for i,label in enumerate(values[1:]):
        panel(d,(xs[i],y,xs[i]+240,y+115))
        text(d,(xs[i]+120,y+39),label,31,WHITE,True,anchor='mt')
        if i<2:
            arrow(d,(xs[i]+245,y+58),(xs[i+1]-12,y+58))


def static_scene(clip,scene,ci,si):
    im=common(clip,scene,ci,si);d=ImageDraw.Draw(im);k=scene['kind']
    if k=='pipelines':
        pipeline(d,570,scene['left'],PY);pipeline(d,880,scene['right'],GO)
    elif k=='types':
        for y,label,color in [(470,'PYTHON',PY),(790,'GO',GO)]:
            panel(d,(76,y,1004,y+270));text(d,(110,y+30),label,28,color,True)
        text(d,(110,550),'value = 21',35,WHITE,mono=True)
        text(d,(110,870),'var value int = 21',35,WHITE,mono=True)
    elif k=='deploy':
        pipeline(d,570,['PYTHON','.py','Окружение','Запуск'],PY)
        pipeline(d,880,['GO','go build','Бинарник','Запуск'],GO)
        text(d,(76,735),'Интерпретатор + зависимости',29,MUTED)
        text(d,(76,1045),'Среда Go включена в исполняемый файл',29,MUTED)
    elif k=='bullets':
        color=PY if scene['accent']=='python' else GO
        text(d,(76,478),scene['language'],38,color,True)
        for i,label in enumerate(scene['items']):
            y=565+i*175
            panel(d,(76,y,1004,y+140))
            text(d,(110,y+40),f'0{i+1}',30,color,mono=True)
            paragraph(d,200,y+34,label,width=760,size=35,max_lines=2)
    elif k=='tradeoff':
        panel(d,(250,470,830,575));text(d,(540,506),'Требования проекта',36,WHITE,True,anchor='mt')
        arrow(d,(450,580),(292,705),PY);arrow(d,(630,580),(788,705),GO)
        panel(d,(76,725,510,1005),PY);panel(d,(570,725,1004,1005),GO)
        text(d,(110,765),'PYTHON',30,PY,True);text(d,(604,765),'GO',30,GO,True)
        paragraph(d,110,835,'Выразительность\nБиблиотеки\nБыстрый прототип',width=365,size=32,max_lines=3)
        paragraph(d,604,835,'Проверки сборки\nКонкурентность\nПоставка сервиса',width=365,size=32,max_lines=3)
        text(d,(540,1085),'Измеряем на своём сценарии',34,WHITE,True,anchor='mt')
    elif k=='async':
        text(d,(76,472),'ОДИН EVENT LOOP',28,PY,True)
        panel(d,(76,540,1004,660));text(d,(110,578),'выполнение',32,WHITE)
        for i,name in enumerate(['Запрос A','Запрос B','Запрос C']):
            x=76+i*328;panel(d,(x,805,x+272,1010))
            text(d,(x+136,842),name,30,WHITE,True,anchor='mt')
            text(d,(x+136,920),'ожидание сети',25,MUTED,anchor='mt')
            arrow(d,(x+136,670),(x+136,790),LINE)
        text(d,(540,1080),'await отдаёт управление циклу',32,PY,anchor='mt')
    elif k=='goroutines':
        for i in range(4):
            x=76+i*238;panel(d,(x,475,x+214,560),GO)
            text(d,(x+107,501),f'G{i+1}',32,GO,True,anchor='mt')
        text(d,(540,605),'ПЛАНИРОВЩИК GO',25,MUTED,anchor='mt')
        for i in range(3):
            y=690+i*130;panel(d,(76,y,1004,y+90))
            text(d,(110,y+28),f'Поток ОС {i+1}',29,MUTED)
        text(d,(76,1110),'Количество потоков на схеме условное',25,MUTED)
    elif k=='cpu':
        rows=[('CPython с GIL','Чистый Python-код',PY),('Go','Работа на ядрах ОС',GO),('Free-threaded Python','Проверка совместимости',PY)]
        for i,(label,note,color) in enumerate(rows):
            y=475+i*205;panel(d,(76,y,1004,y+170))
            text(d,(110,y+24),label,31,color,True)
            text(d,(110,y+92),note,26,MUTED)
            for j in range(3):
                x=740+j*75;panel(d,(x,y+54,x+55,y+114),LINE,radius=8)
    elif k=='routes':
        panel(d,(280,470,800,575));text(d,(540,503),'Главная задача?',38,WHITE,True,anchor='mt')
        arrow(d,(400,580),(290,710),PY);arrow(d,(680,580),(790,710),GO)
        panel(d,(76,730,510,1075),PY);panel(d,(570,730,1004,1075),GO)
        text(d,(110,768),'PYTHON',32,PY,True);text(d,(604,768),'GO',32,GO,True)
        paragraph(d,110,850,'Бот, автоматизация\nДанные, ML\nПрототип',width=365,size=32,max_lines=4)
        paragraph(d,604,850,'API, CLI\nСетевой сервис\nИнфраструктура',width=365,size=32,max_lines=4)
    elif k=='checklist':
        for i,label in enumerate(scene['items']):
            y=470+i*125;panel(d,(76,y,1004,y+101))
            panel(d,(105,y+29,145,y+69),LINE,radius=7)
            text(d,(178,y+28),label,33,WHITE)
    elif k=='project':
        pipeline(d,600,['СЕЙЧАС','Python','Bot API','Человек'],PY)
        panel(d,(76,880,1004,1060));text(d,(110,920),'ПОЗЖЕ: GO',28,GO,True)
        text(d,(110,982),'CLI или worker под отдельную задачу',33,WHITE)
    elif k=='survey':
        for tick in [0,25,50,75,100]:
            x=76+928*tick/100
            d.line((x,550,x,1030),fill=LINE,width=1)
            text(d,(x,1065),str(tick),26,MUTED,mono=True,anchor='mt')
        text(d,(76,485),'ДОЛЯ УЧАСТНИКОВ ВОПРОСА, %',25,MUTED)
        for y,label,pct,color in [(585,'Python','58,0%',PY),(835,'Go','16,5%',GO)]:
            text(d,(76,y),label,44,color,True)
            text(d,(1004,y-4),pct,54,WHITE,True,anchor='rt')
            panel(d,(76,y+92,1004,y+146),LINE,fill=BG,radius=12)
    elif k=='outlook':
        for y,label,body,color in [(480,'PYTHON','Данные · ML · автоматизация',PY),(735,'GO','API · CLI · инфраструктура',GO)]:
            panel(d,(76,y,1004,y+205),color)
            text(d,(110,y+32),label,32,color,True)
            text(d,(110,y+108),body,36,WHITE)
        text(d,(540,1040),'Перспективы зависят от вашей цели',33,WHITE,True,anchor='mt')
    elif k=='skills':
        for i,label in enumerate(['Данные','Алгоритмы','Тесты','Сеть','Архитектура']):
            y=475+i*120;panel(d,(76,y,1004,y+95))
            text(d,(110,y+27),f'{i+1:02d}',29,MUTED,mono=True)
            text(d,(205,y+25),label,34,WHITE,True)
    else:
        raise ValueError('Неизвестная сцена '+k)
    return im


def animated_layer(image,scene,seconds):
    d=ImageDraw.Draw(image);p=max(0,min(1,seconds/8));k=scene['kind']
    if k in ('pipelines','deploy','project'):
        for y,color in ([(570,PY),(880,GO)] if k!='project' else [(600,PY)]):
            for i in range(2):
                start=321+i*344;end=408+i*344
                phase=(seconds*.55-i*.33)%1
                dot(d,start+(end-start)*phase,y+58,color,10)
            active=int(seconds*.8)%3
            x=76+active*344;d.rounded_rectangle((x,y,x+240,y+115),radius=24,outline=color,width=3)
    elif k=='types':
        switched=seconds>=2.2
        text(d,(110,625),'value = "21"' if switched else 'value + 1',35,PY,mono=True)
        text(d,(110,955),'value = "21"',35,GO,mono=True)
        text(d,(970,695),'Имя может сменить привязку' if switched else 'Тип объекта — int',28,PY,anchor='rt')
        if seconds>=3.2:
            text(d,(970,1015),'Ошибка типов при сборке',29,RED,True,anchor='rt')
            d.line((110,1000,415,1000),fill=RED,width=3)
    elif k=='bullets':
        i=min(2,int(seconds/2.2));y=565+i*175
        color=PY if scene['accent']=='python' else GO
        d.rounded_rectangle((76,y,1004,y+140),radius=24,outline=color,width=3)
        d.rectangle((76,y+25,82,y+115),fill=color)
    elif k in ('tradeoff','routes'):
        phase=(seconds*.35)%1
        side=int(seconds/2.8)%2
        sx=450 if k=='tradeoff' else 400;ex=292 if k=='tradeoff' else 290
        if side:
            sx=W-sx;ex=W-ex
        dot(d,sx+(ex-sx)*phase,580+(125 if k=='tradeoff' else 130)*phase,GO if side else PY,12)
    elif k=='async':
        i=int(seconds*1.1)%3
        x=76+i*328
        d.rounded_rectangle((x,805,x+272,1010),radius=24,outline=PY,width=3)
        progress=(seconds*1.1)%1
        dot(d,385+progress*550,600,PY,15)
        text(d,(540,715),f'Сейчас выполняется шаг {chr(65+i)}',30,PY,anchor='mt')
    elif k=='goroutines':
        for i in range(3):
            phase=(seconds*.45+i*.32)%1
            x=425+phase*500;y=735+i*130
            dot(d,x,y,GO,15)
            text(d,(x,y-50),f'G{(int(seconds*.45)+i)%4+1}',23,GO,mono=True,anchor='mt')
    elif k=='cpu':
        for row in range(3):
            active=[int(seconds*.8)%3] if row==0 else [0,1,2]
            for j in active:
                x=740+j*75;y=475+row*205
                d.rounded_rectangle((x,y+54,x+55,y+114),radius=8,fill=PY if row!=1 else GO)
        text(d,(76,1115),'Схема модели, не замер производительности',25,MUTED)
    elif k=='checklist':
        count=min(5,int(seconds/.95))
        for i in range(count):
            y=470+i*125
            d.line((113,y+48,121,y+58,139,y+37),fill=GO,width=4)
    elif k=='survey':
        factor=ease(seconds/3.5)
        for y,value,color in [(585,58.0,PY),(835,16.5,GO)]:
            length=928*value/100*factor
            if length>1:
                d.rounded_rectangle((76,y+92,76+length,y+146),radius=12,fill=color)
    elif k=='outlook':
        y=480 if int(seconds/2)%2==0 else 735
        d.rounded_rectangle((76,y,1004,y+205),radius=24,outline=PY if y==480 else GO,width=4)
    elif k=='skills':
        count=min(5,int(seconds/.9))
        for i in range(count):
            y=475+i*120
            d.rectangle((76,y+18,83,y+77),fill=GO)
            d.line((919,y+46,930,y+58,952,y+32),fill=GO,width=5)
    return image


def render_clip(clip,index,fps,seconds):
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/(clip['id']+'.mp4')
    bases=[static_scene(clip,scene,index,i) for i,scene in enumerate(clip['scenes'])]
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    command=[ffmpeg,'-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo',
             '-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(fps),'-i','-', '-an',
             '-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',
             '-movflags','+faststart','-metadata','title='+clip['title'],str(target)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for frame in range(round(fps*seconds)):
            t=frame/fps
            scene_index=min(2,int(t//8))
            image=animated_layer(bases[scene_index].copy(),clip['scenes'][scene_index],t%8)
            d=ImageDraw.Draw(image)
            d.rectangle((76,1283,1004,1287),fill=LINE)
            d.rectangle((76,1283,76+928*(t/seconds),1287),fill=GO)
            fade=min(ease(t/.35),ease((seconds-t)/.35))
            if fade<1:
                image=Image.blend(Image.new('RGB',(W,H),BG),image,fade)
            process.stdin.write(image.tobytes())
            if frame % (fps*8)==0:
                print(f"{clip['id']}: {int(t):02d}/{seconds}s",flush=True)
        process.stdin.close()
        errors=process.stderr.read().decode('utf-8',errors='replace')
        if process.wait()!=0:
            raise RuntimeError(errors)
    except BaseException:
        process.kill()
        raise
    if target.stat().st_size>=49*1024*1024:
        raise ValueError('Анимация превышает безопасный лимит загрузки Telegram')
    for i,second in enumerate([4,12,20]):
        still=animated_layer(bases[i].copy(),clip['scenes'][i],second%8)
        still.save(OUT/(clip['id']+f'-scene-{i+1}.png'))
    print(f"Saved {target.name}: {target.stat().st_size:,} bytes",flush=True)
    return target


def contact_sheet(data):
    thumbs=[]
    for clip in data['clips']:
        for i in range(3):
            image=Image.open(OUT/(clip['id']+f'-scene-{i+1}.png')).convert('RGB')
            image.thumbnail((324,405))
            thumbs.append(image)
    sheet=Image.new('RGB',(3*324,5*405),BG)
    for i,thumb in enumerate(thumbs):
        sheet.paste(thumb,((i%3)*324,(i//3)*405))
    sheet.save(OUT/'contact-sheet.jpg',quality=94)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser()
    parser.add_argument('--clip',type=int)
    parser.add_argument('--stills-only',action='store_true')
    args=parser.parse_args()
    data=json.loads((ROOT/'storyboard.json').read_text(encoding='utf-8'))
    OUT.mkdir(parents=True,exist_ok=True)
    for index,clip in enumerate(data['clips']):
        if args.clip and index+1!=args.clip:
            continue
        if args.stills_only:
            for si,scene in enumerate(clip['scenes']):
                animated_layer(static_scene(clip,scene,index,si),scene,4).save(OUT/(clip['id']+f'-scene-{si+1}.png'))
        else:
            render_clip(clip,index,data['fps'],data['seconds_per_clip'])
    if not args.clip:
        contact_sheet(data)
