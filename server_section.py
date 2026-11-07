"""Раздел 1. Разработка и работа серверов."""

from go_server_content import EXAMPLE, GOPHER, GO_HTTP_EVENTS

SECTION_TITLE = 'Разработка и работа серверов'
LESSON_COUNT = 19
IMAGE_ROOT = 'editorial/go_server/images'


def _existing(number, original):
    event = dict(GO_HTTP_EVENTS[original - 1])
    event['id'] = f'servers-section-1-{number:02}'
    field = 'caption' if event['kind'] == 'photo' else 'description'
    event[field] = event[field].replace(
        f'🐹 Go-сервер · {original:02}/15',
        f'🐹 Раздел 1 · {SECTION_TITLE} · {number:02}/{LESSON_COUNT}', 1).replace(
            'Финальное задание.', 'Практическое задание.', 1)
    return event


def _photo(number, image, title, body):
    return {
        'id': f'servers-section-1-{number:02}',
        'kind': 'photo',
        'image_path': f'{IMAGE_ROOT}/{image}.png',
        'caption': (
            f'<b>🐹 Раздел 1 · {SECTION_TITLE} · {number:02}/{LESSON_COUNT}\n{title}</b>'
            f'\n\n{body}\n\n{GOPHER}'
        ),
    }


SECTION_EVENTS = (
    _photo(1, '01-request-explained', 'Что такое сервер',
        'Сервером называют и машину, и программу, которая принимает запросы. В практикуме мы пишем '
        'HTTP-программу на Go и запускаем её процесс на компьютере. Пока процесс работает, клиенты могут отправлять ему запросы.\n\n'
        'Браузер или <code>curl</code> играет роль клиента. <code>http.Server</code> читает запрос, '
        '<code>ServeMux</code> выбирает обработчик, а обработчик формирует статус, заголовки и JSON. '
        'Стрелка обратно на схеме — ответ клиенту.\n\n'
        '<b>Проверь понимание.</b> Что произойдёт с новым запросом после остановки процесса? '
        '<a href="https://pkg.go.dev/net/http">Устройство net/http</a>'),
    _photo(2, '16-address-port', 'Адрес, порт и путь',
        '<code>http://127.0.0.1:8080/healthz</code> читается по частям. <code>http</code> задаёт протокол, '
        '<code>127.0.0.1</code> — адрес узла через loopback, <code>8080</code> — порт приложения, '
        '<code>/healthz</code> — путь, который проверяет маршрутизатор.\n\n'
        'Клиент соединяется с адресом и портом, затем отправляет HTTP-метод и путь. '
        'Имя домена обычно сначала разрешается через DNS в IP-адрес. В нашем числовом URL этот шаг не нужен.\n\n'
        '<b>Практика.</b> Замени порт на <code>8081</code>, сохранив адрес. Объясни, почему запрос '
        'не попадёт в сервер, слушающий <code>8080</code>.'),
    _photo(3, '17-setup-launch', 'Подготовка и запуск проекта',
        'Установи актуальный стабильный <a href="https://go.dev/dl/">Go</a> и Git. '
        'Проект использует маршруты Go 1.22+. В терминале выполни\n'
        '<pre>go version\ngit clone https://github.com/make-smart-products/codelevel_pygo.git\n'
        'cd codelevel_pygo/editorial/go_server\ngo run .</pre>\n'
        'Первая команда должна вывести версию Go. Последняя запустит сервер и займёт терминал. '
        'Во втором терминале выполни <code>curl -i http://127.0.0.1:8080/healthz</code>. '
        'В PowerShell используй <code>curl.exe</code>. Ожидай <code>200 OK</code> и <code>{"status":"ok"}</code>. '
        'Остановить сервер можно через <code>Ctrl+C</code>.'),
    _existing(4, 3),
    _existing(5, 5),
    _existing(6, 2),
    _existing(7, 4),
    _existing(8, 6),
    _existing(9, 7),
    _existing(10, 8),
    _existing(11, 9),
    _existing(12, 10),
    _existing(13, 11),
    _existing(14, 12),
    _existing(15, 13),
    _existing(16, 14),
    _existing(17, 15),
    _photo(18, '18-build-binary', 'Собрать файл и запустить его',
        '<code>go run .</code> собирает и сразу запускает программу. <code>go build</code> сохраняет исполняемый файл '
        'для последующих запусков. В папке проекта сначала останови старый процесс и выполни\n'
        '<pre>go test ./...\ngo build -o server .</pre>\n'
        'На Linux и macOS запусти <code>./server</code>. На Windows в PowerShell удобно собрать '
        '<code>go build -o server.exe .</code> и запустить <code>.\\server.exe</code>. '
        'Проверь <code>/healthz</code> из второго терминала.\n\n'
        'Файл собирается под выбранные ОС и архитектуру. У нашего примера зависимости входят в стандартную библиотеку. '
        'Для переноса собери файл под целевую платформу.'),
    _photo(19, '19-hosting', 'От локального запуска к размещению',
        'Для доступа пользователей нужны работающий узел и запущенный процесс. В схеме прокси и Go находятся на одной машине. '
        'Домен указывает на публичный адрес, прокси принимает HTTPS на <code>443</code> и передаёт запрос Go на '
        '<code>127.0.0.1:8080</code>. Внешние подключения разрешает сетевой экран.\n\n'
        'TLS требует действительного сертификата. Менеджер процессов запускает приложение после перезагрузки '
        'и собирает журнал. После размещения проверь домен, HTTPS, <code>/healthz</code> и поведение при остановке.\n\n'
        'Основные свойства Go-сервиса из раздела — маршруты, JSON, проверка ввода, конкурентные обработчики, '
        'таймауты, мягкая остановка и тесты. '
        f'<a href="{EXAMPLE}">Код и руководство</a>'),
)


LESSON_TITLES = (
    'Что такое сервер', 'Адрес, порт и путь', 'Подготовка и запуск проекта',
    'Первый обработчик', 'Чтение HTTP-ответа', 'Викторина о net/http',
    'Викторина о loopback', 'Маршрут с параметром', 'Викторина о параметре пути',
    'JSON и проверка ввода', 'Викторина о статусе ответа', 'Одновременные запросы',
    'Таймауты', 'Викторина о чтении заголовков', 'Мягкое завершение',
    'Викторина об остановке', 'Тестирование обработчиков', 'Сборка и запуск файла',
    'Основы размещения сервера',
)


def section_index(message_ids):
    links = [
        f'{number:02}. <a href="https://t.me/codelevel_pygo/{message_ids[event["id"]]}">{title}</a>'
        for number, (event, title) in enumerate(zip(SECTION_EVENTS, LESSON_TITLES), 1)
    ]
    return (
        f'<b>Раздел 1. {SECTION_TITLE}</b>\n\n'
        'Практикум на Go от устройства HTTP-запроса до запуска и проверки своего сервера. '
        'Проходи уроки по порядку, выполняй команды и отвечай на викторины.\n\n'
        + '\n'.join(links)
        + f'\n\n<a href="{EXAMPLE}">Исходный код и команды запуска</a>\n'
        '#Серверы #Go #Раздел1 #CodeLevel'
    )
