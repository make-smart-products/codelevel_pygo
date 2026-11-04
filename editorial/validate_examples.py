"""Исполняет только явно самостоятельные Python и Go примеры курса."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess

from generate_course import ROOT, topics


def validate():
    lessons=topics()
    counts={'python':0,'go':0,'json':0}
    for lesson in lessons:
        if lesson['kind']=='python':
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                exec(lesson['code'],{})
            if output.getvalue().strip()!=lesson['outcome'].strip():
                raise ValueError('Неверный Python результат: '+lesson['title'])
            counts['python']+=1
        elif lesson['kind']=='json':
            json.loads(lesson['code'])
            counts['json']+=1
    go=[lesson for lesson in lessons if lesson['kind']=='go']
    temp=ROOT.parent/'.local'/'course-go'
    temp.mkdir(parents=True,exist_ok=True)
    code='package main\nimport "fmt"\nfunc main(){\n'+'\n'.join('{\n'+lesson['code']+'\nfmt.Println("===")\n}' for lesson in go)+'\n}\n'
    source=temp/'examples.go'
    source.write_text(code,encoding='utf-8')
    env={**os.environ,'GOCACHE':str(temp/'cache'),'GOPATH':str(temp/'path'),'GOTELEMETRY':'off'}
    result=subprocess.run(['go','run',str(source)],capture_output=True,text=True,env=env,timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    outputs=result.stdout.strip().split('===')[:-1]
    if len(outputs)!=len(go):
        raise ValueError('Неверное число Go-результатов')
    for lesson,output in zip(go,outputs):
        if output.strip()!=lesson['outcome'].strip():
            raise ValueError('Неверный Go результат: '+lesson['title'])
    counts['go']=len(go)
    report={'executed_examples':counts,'other_examples':'contextual fragments and diagrams; not claimed standalone'}
    (ROOT/'pack'/'examples-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    print(json.dumps(validate(),ensure_ascii=False))
