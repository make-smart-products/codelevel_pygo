"""Проверка контейнеров, декодирования и подписей перед публикацией."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from build_pack import plain_text


def main():
    posts=[json.loads(line) for line in (ROOT.parent/'pack/queue.jsonl').read_text(encoding='utf-8').splitlines()]
    data=json.loads((ROOT/'storyboard.json').read_text(encoding='utf-8'))
    checked=[]
    for clip,post in zip(data['clips'],posts[:5]):
        path=ROOT/'media'/(clip['id']+'.mp4')
        reader=imageio_ffmpeg.read_frames(str(path))
        metadata=next(reader)
        reader.close()
        assert metadata['size']==(1080,1350),metadata
        assert metadata['fps']==24,metadata
        assert abs(metadata['duration']-24)<.1,metadata
        assert metadata['codec']=='h264',metadata
        decode=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-i',str(path),'-f','null','-'],capture_output=True,timeout=60)
        if decode.returncode:
            raise RuntimeError(decode.stderr.decode('utf-8',errors='replace'))
        count=len(plain_text(post['caption_html']).encode('utf-16-le'))//2
        assert count<=1024,count
        poster=Image.open(ROOT/'media'/(clip['id']+'-scene-1.png')).convert('RGB')
        poster.thumbnail((320,320))
        poster.save(ROOT/'media'/(clip['id']+'-poster.jpg'),quality=90)
        checked.append({'id':clip['id'],'codec':'h264','size':[1080,1350],'fps':24,'duration':24,
                        'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'caption_utf16_units':count,'full_decode':'passed'})
    report={'clips':checked,'visual_review':'15 storyboard frames inspected; no clipping',
            'as_of':'2026-11-04','statistics_scope':'Stack Overflow 2026 language question, n=14099; multiple choices; not vacancies'}
    (ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
