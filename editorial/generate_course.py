"""300 последовательных публикаций: 60 создание, 90 развитие, 150 навыки."""

import json
from pathlib import Path

from build_pack import ROOT, build, make_post

APP_URL='https://github.com/make-smart-products/codelevel_pygo/tree/main/editorial/app60'
SOURCE_OVERRIDES={
    'Проверки сценариев':['https://docs.python.org/3.12/library/unittest.html'],
    'Сроки и зоны времени':['https://docs.python.org/3.12/library/datetime.html','https://docs.python.org/3.12/library/zoneinfo.html'],
    'Контейнер и постоянные данные':['https://docs.docker.com/build/building/best-practices/'],
    'Наблюдаемость и восстановление':['https://opentelemetry.io/docs/concepts/observability-primer/'],
    'Контекстные менеджеры':['https://docs.python.org/3.12/library/sqlite3.html','https://docs.python.org/3.12/library/contextlib.html'],
    'Время и длительность':['https://docs.python.org/3.12/library/time.html#time.monotonic'],
    'Go: ошибки':['https://pkg.go.dev/errors','https://pkg.go.dev/fmt'],
    'Go: context':['https://pkg.go.dev/context'],
    'Go: гонки данных':['https://go.dev/doc/articles/race_detector'],
    'HTTP-контракты':['https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview'],
    'Совместимость схем':['https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design'],
    'SQL и индексы':['https://www.postgresql.org/docs/current/indexes.html'],
    'Транзакции и внешние эффекты':['https://www.sqlite.org/lang_transaction.html'],
    'Границы доверия':['https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html'],
    'Git и проверяемые изменения':['https://git-scm.com/docs/gittutorial'],
    'Измерение производительности':['https://docs.python.org/3.12/library/profile.html'],
    'Надёжность сервиса':['https://sre.google/sre-book/monitoring-distributed-systems/'],
    'ИИ в работе разработчика':['https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html'],
}


def topics():
    result=[]
    module=None
    for line_number,line in enumerate((ROOT/'course_topics.txt').read_text(encoding='utf-8').splitlines(),1):
        if not line.strip():
            continue
        fields=line.split('¦')
        if line.startswith('@'):
            if len(fields)!=3:
                raise ValueError(f'Неверный модуль: строка {line_number}')
            module=fields[1]
            sources=fields[2].split(';')
            continue
        if not module or len(fields)!=8:
            raise ValueError(f'Нужно 8 полей, строка {line_number}: {len(fields)}')
        title,core,code,outcome,pitfall,task,solution,kind=[value.replace('\\n','\n') for value in fields]
        result.append(dict(module=module,title=title,core=core,code=code,outcome=outcome,
                           pitfall=pitfall,task=task,solution=solution,kind=kind,
                           source_urls=SOURCE_OVERRIDES.get(title,sources)))
    if len(result)!=60:
        raise ValueError(f'Нужно 60 тем, получено {len(result)}')
    return result


def posts():
    result=[]
    labels=['Понимаем задачу','Разбираем пример','Ловим ошибку','Практикуемся','Проверяем решение']
    for topic_index,topic in enumerate(topics()):
        number=topic_index*5+1
        first_release=topic_index<12
        link=('Код первой версии: '+APP_URL) if first_release else 'Этот модуль — продолжение курса; доработка выполняется отдельно от первой версии.'
        sets=[
            [('text',topic['core']),('text','Учебная цель: '+topic['task']),
             ('text',f'Модуль {topic_index+1}: сначала разберём пример, затем ошибку, самостоятельную задачу и её решение. '+link)],
            [('text','Рассмотрим конкретный пример по теме «'+topic['title']+'». '+
              ('Фрагмент показан в контексте соответствующей функции или схемы; отдельно он не запускается.' if topic['kind'] in ('context','python-fragment','go-fragment','sql') else
               'Для Go сниппет помещается в main с импортом fmt; команды shell выполняются в указанной среде проекта.' if topic['kind'] in ('go','shell') else
               'Сопоставьте каждый шаг примера с результатом ниже.')),
             ('code',topic['code']),('text','Что это означает:\n'+topic['outcome'])],
            [('text','Типичная ошибка: '+topic['pitfall']),
             ('text','Почему это важно:\n'+topic['core']),
             ('text','Проверка при ревью: объясните, какое состояние или результат нарушится при этой ошибке. Зафиксируйте отдельный отрицательный сценарий до изменения реализации.')],
            [('text','Самостоятельная задача:\n'+topic['task']),
             ('text','Опора из разбора:\n'+topic['outcome']),
             ('text','Запишите свой ответ или выполните проверку в тестовой копии проекта. Для кода укажите вход, ожидаемый результат и один граничный случай. Не используйте рабочую базу или реальные секреты как тестовые данные. Разбор — в следующем посте.')],
            [('text','Разбор задачи:\n'+topic['task']),('answer',topic['solution']),
             ('text','Завершение модуля: сверьте решение с результатом собственного опыта. Если оно отличается, объясните причину и поправьте проверку. В следующем модуле перейдём к «'+
              (topics()[topic_index+1]['title'] if topic_index<59 else 'самостоятельному развитию своего проекта')+'».')],
        ]
        for part,sections in enumerate(sets):
            post=make_post(number+part,topic['module'],topic['title']+' · '+labels[part],
                topic['task'],sections,topic['source_urls'],topic_number=topic_index+1,
                part=part+1,topic=topic['title'],course_version='personal-bot-v1',
                prerequisite_numbers=[] if number+part==1 else [number+part-1],
                artifact_url=APP_URL if first_release else None,
                implementation_status='reference_app_available' if first_release else 'learning_exercise_to_implement')
            result.append(post)
    return result


if __name__=='__main__':
    report=build(posts(),300)
    print(json.dumps(report,ensure_ascii=False,indent=2))
