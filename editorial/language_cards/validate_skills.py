"""Проверка Go-ответов реальным выполнением; снимок будущих публикаций."""

from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
sys.path.insert(0,str(PROJECT))
from skills_content import RECIPES,code_case,make_event


def main():
    cases=[]
    for recipe in RECIPES:
        if recipe[1]=='Go':
            for a in (7,10,31,100):
                code,expected,_=code_case(recipe[0],a)
                cases.append((recipe[0],code,expected))
    folder=PROJECT/'.local/skills-go'
    folder.mkdir(parents=True,exist_ok=True)
    source=folder/'examples.go'
    source.write_text('package main\nimport "fmt"\nfunc main(){\n'+
        '\n'.join('{\n'+code+'\nfmt.Println("===")\n}' for _,code,_ in cases)+'\n}\n',encoding='utf-8')
    env={**os.environ,'GOCACHE':str(folder/'cache'),'GOPATH':str(folder/'path'),'GOTELEMETRY':'off'}
    result=subprocess.run(['go','run',str(source)],capture_output=True,text=True,env=env,timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    outputs=result.stdout.strip().split('===')[:-1]
    assert len(outputs)==len(cases)
    for (name,_,expected),actual in zip(cases,outputs):
        if actual.strip()!=expected:
            raise ValueError('Go result mismatch: '+name)
    snapshot=[make_event(index) for index in range(605)]
    with (ROOT/'prepared-605.jsonl').open('w',encoding='utf-8') as stream:
        for event in snapshot:
            stream.write(json.dumps(event,ensure_ascii=False)+'\n')
    report={'go_examples_executed':len(cases),'recipe_families':len(RECIPES),
            'prepared_preview':len(snapshot),'kinds':dict(Counter(e['kind'] for e in snapshot)),
            'generation':'deterministic authored templates; repeated concepts with new code inputs',
            'images':'five reusable topic-series covers generated with built-in image_gen',
            'not_ai_generation_on_github':True}
    (ROOT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
