"""Практикум CodeLevel по HTTP-серверу на Go."""

EXAMPLE = 'https://github.com/make-smart-products/codelevel_pygo/tree/main/editorial/go_server'
GOPHER = 'Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>'
IMAGES = 'editorial/go_server/images'


def _base(number, image, kind):
    return {
        'id': f'go-http-v1-{number:02}',
        'kind': kind,
        'image_path': f'{IMAGES}/{image}.png',
    }


def _photo(number, image, title, body):
    return {
        **_base(number, image, 'photo'),
        'caption': f'<b>🐹 Go-сервер · {number:02}/15 · {title}</b>\n\n{body}\n\n{GOPHER}',
    }


def _quiz(number, image, question, options, correct, explanation, context):
    return {
        **_base(number, image, 'quiz'),
        'question': question,
        'options': options,
        'correct': correct,
        'explanation': explanation,
        'description': f'<b>🐹 Go-сервер · {number:02}/15</b>\n{context}\n\n{GOPHER}',
    }


GO_HTTP_EVENTS = (
    _photo(1, '01-request-explained', 'Первый HTTP-сервер',
        'Начнём с маршрута <code>GET /healthz</code>. Сервер примет запрос, вызовет обработчик и вернёт JSON. '
        'На схеме проследи путь от клиента через <code>http.Server</code> и <code>ServeMux</code> к обработчику.\n\n'
        'Нужен <a href="https://go.dev/dl/">Go 1.22+</a>. '
        f'Открой <a href="{EXAMPLE}">проект серии</a>, перейди в <code>editorial/go_server</code> '
        'и запусти <code>go run .</code>. В другом терминале выполни '
        '<code>curl -i http://127.0.0.1:8080/healthz</code>. В PowerShell используй <code>curl.exe</code>. '
        'Ожидай <code>200 OK</code> и <code>{"status":"ok"}</code>.'),
    _quiz(2, '02-toolbox', 'Какой пакет Go принимает HTTP-запросы и даёт тип http.Server?',
        ('encoding/json', 'net/http', 'net/url', 'os/signal'), 1,
        'net/http содержит сервер, маршрутизатор ServeMux и интерфейсы для обработки запроса.',
        'Узнай пакет по его роли в сервере.'),
    _photo(3, '03-first-handler', 'Собери маршрут с нуля',
        '<pre>package main\n\nimport (\n    "fmt"\n    "log"\n    "net/http"\n)\n\nfunc main() {\n'
        '    mux := http.NewServeMux()\n    mux.HandleFunc("GET /healthz",\n'
        '        func(w http.ResponseWriter, r *http.Request) {\n'
        '            w.Header().Set("Content-Type", "application/json")\n'
        '            fmt.Fprintln(w, `{"status":"ok"}`)\n'
        '        })\n    log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))\n}</pre>\n'
        'Сохрани как <code>main.go</code> в отдельной папке. Останови сервер из проекта и выполни '
        '<code>go run main.go</code>. <code>ServeMux</code> подберёт обработчик по методу и пути. '
        'Для <code>/missing</code> ожидай <code>404</code>. Синтаксис работает с Go 1.22. '
        '<a href="https://go.dev/blog/routing-enhancements">Маршрутизация в Go</a>'),
    _quiz(4, '04-loopback', 'Сервер слушает 127.0.0.1:8080. Кто может подключиться к нему напрямую?',
        ('Любой компьютер в интернете', 'Все устройства в домашней сети',
         'Клиенты на той же машине через loopback', 'Только браузер'), 2,
        '127.0.0.1 — адрес обратной петли. Для связи по локальной сети серверу нужен другой адрес прослушивания.',
        'Проверь, что означает адрес из примера.'),
    _photo(5, '05-http-response', 'Как читать HTTP-ответ',
        'У <code>curl -i</code> сначала идёт строка со статусом, затем заголовки, пустая строка и тело. '
        'Найди <code>Content-Type: application/json</code> и JSON с полем <code>status</code>.\n\n'
        '<b>Задание.</b> Выполни <code>curl -i -X POST http://127.0.0.1:8080/healthz</code>. '
        'Сравни с GET. Для известного пути и неподдерживаемого метода ожидай <code>405</code> и заголовок <code>Allow</code>.'),
    _photo(6, '02-routing-explained', 'Параметр пути',
        '<pre>mux.HandleFunc("GET /api/hello/{name}", hello)\nname := r.PathValue("name")</pre>\n'
        'Первая строка регистрирует маршрут. В обработчике <code>PathValue</code> берёт значение '
        'именованного сегмента из запроса. На схеме метод и путь проходят проверку, а <code>Ada</code> попадает в параметр. '
        'Перед этим шагом вернись к полному проекту и запусти <code>go run .</code>.\n\n'
        '<b>Проверь.</b> Запроси <code>http://127.0.0.1:8080/api/hello/Ada</code>. '
        'Получи <code>{"message":"Hello, Ada!"}</code>. Теперь замени имя на <code>Grace</code>.'),
    _quiz(7, '07-path-quiz', 'Как получить Grace из GET /api/hello/Grace для шаблона GET /api/hello/{name}?',
        ('r.URL.Query().Get("name")', 'r.Header.Get("name")', 'r.Method', 'r.PathValue("name")'), 3,
        'PathValue возвращает значение именованной части пути. Query читает параметры после знака вопроса.',
        'Выбери, откуда обработчик читает параметр.'),
    _photo(8, '08-json-validation', 'JSON и проверка ввода',
        'В примере имя занимает от 1 до 40 символов. Допустимы буквы и одиночные дефисы между ними. '
        'Для <code>/api/hello/Ada123</code> сервер возвращает <code>400</code> и JSON с ошибкой.\n\n'
        '<b>Почему это важно.</b> Сначала проверяем ввод и выбираем статус. '
        'Затем задаём <code>Content-Type</code>, отправляем статус через <code>WriteHeader</code> и кодируем ответ '
        'через <code>json.NewEncoder(w).Encode(value)</code>. '
        'Кодировщик сам экранирует строки JSON.'),
    _quiz(9, '09-status-quiz', 'Какой статус вернёт пример для GET /api/hello/Ada123?',
        ('400 Bad Request', '200 OK', '404 Not Found', '405 Method Not Allowed'), 0,
        'Метод и путь подходят шаблону. Имя не проходит проверку, поэтому обработчик возвращает 400.',
        'Отдели выбор маршрута от проверки данных в обработчике.'),
    _photo(10, '10-concurrency', 'Запросы идут одновременно',
        '<code>net/http</code> может выполнять несколько обработчиков одновременно. '
        'Имя из <code>r.PathValue</code> и переменные внутри обработчика относятся к одному вызову. '
        'Общая <code>map</code>, в которую пишут обработчики, требует синхронизации.\n\n'
        '<b>Практика.</b> Найди в примере, где формируется приветствие. '
        'Объясни, почему два одновременных запроса с разными именами получают разные ответы.'),
    _photo(11, '11-timeouts', 'Таймауты соединения',
        'У <code>http.Server</code> можно отдельно задать время чтения заголовков (<code>ReadHeaderTimeout</code>), '
        'чтения запроса целиком (<code>ReadTimeout</code>), записи ответа (<code>WriteTimeout</code>) '
        'и ожидания нового запроса по открытому соединению (<code>IdleTimeout</code>).\n\n'
        '<b>Практика.</b> Найди эти четыре поля в проекте. Для потокового API пересмотри бюджет записи ответа. '
        '<a href="https://pkg.go.dev/net/http#Server">Поля http.Server</a>'),
    _quiz(12, '12-slow-header-quiz', 'Клиент слишком медленно присылает HTTP-заголовки. Какой таймаут задаёт предел для этого этапа?',
        ('IdleTimeout', 'WriteTimeout', 'ReadHeaderTimeout', 'Timeout контекста Shutdown'), 2,
        'ReadHeaderTimeout ограничивает время чтения заголовков. IdleTimeout относится к паузе между запросами.',
        'Соотнеси настройку с этапом HTTP-соединения.'),
    _photo(13, '13-graceful-shutdown', 'Мягкое завершение',
        'При <code>Ctrl+C</code> пример вызывает <code>server.Shutdown(ctx)</code>. '
        'Сервер прекращает принимать новые соединения, закрывает простаивающие и даёт активным запросам завершиться. '
        'Контекст ограничивает ожидание пятью секундами. На схеме показана последовательность остановки.\n\n'
        '<b>Проверь.</b> Останови сервер и повтори запрос. Затем запусти его снова на том же адресе. '
        '<a href="https://pkg.go.dev/net/http#Server.Shutdown">Документация Shutdown</a>'),
    _quiz(14, '14-server-error-quiz', 'Какую ошибку ListenAndServe возвращает при штатном вызове Shutdown?',
        ('context.DeadlineExceeded', 'http.ErrServerClosed', 'io.EOF', 'nil'), 1,
        'http.ErrServerClosed сигнализирует о штатном закрытии сервера. Другие ошибки запуска стоит обработать отдельно.',
        'Разбери, как цикл запуска отличает остановку от ошибки прослушивания порта.'),
    _photo(15, '15-handler-tests', 'Проверяем сервер тестами',
        '<code>httptest.NewRequest</code> создаёт запрос, <code>httptest.NewRecorder</code> записывает ответ. '
        'Передай их в маршрутизатор и проверь статус, заголовки и JSON без запуска слушающего порта.\n\n'
        f'<b>Финальное задание.</b> В <a href="{EXAMPLE}">проекте</a> выполни <code>go test ./...</code>. '
        'Затем добавь маршрут <code>GET /api/version</code> и тест на его JSON-ответ. '
        '<a href="https://pkg.go.dev/net/http/httptest">Пакет httptest</a>'),
)
