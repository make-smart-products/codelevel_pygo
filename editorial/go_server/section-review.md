# Раздел 1. Разработка и работа серверов

19 материалов в учебном порядке. Команды и примеры проверены на проекте editorial/go_server.

## 01. Что такое сервер

[Иллюстрация](images/01-request-explained.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 01/19
Что такое сервер</b>

Сервером называют и машину, и программу, которая принимает запросы. В практикуме мы пишем HTTP-программу на Go и запускаем её процесс на компьютере. Пока процесс работает, клиенты могут отправлять ему запросы.

Браузер или <code>curl</code> играет роль клиента. <code>http.Server</code> читает запрос, <code>ServeMux</code> выбирает обработчик, а обработчик формирует статус, заголовки и JSON. Стрелка обратно на схеме — ответ клиенту.

<b>Проверь понимание.</b> Что произойдёт с новым запросом после остановки процесса? <a href="https://pkg.go.dev/net/http">Устройство net/http</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 02. Адрес, порт и путь

[Иллюстрация](images/16-address-port.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 02/19
Адрес, порт и путь</b>

<code>http://127.0.0.1:8080/healthz</code> читается по частям. <code>http</code> задаёт протокол, <code>127.0.0.1</code> — адрес узла через loopback, <code>8080</code> — порт приложения, <code>/healthz</code> — путь, который проверяет маршрутизатор.

Клиент соединяется с адресом и портом, затем отправляет HTTP-метод и путь. Имя домена обычно сначала разрешается через DNS в IP-адрес. В нашем числовом URL этот шаг не нужен.

<b>Практика.</b> Замени порт на <code>8081</code>, сохранив адрес. Объясни, почему запрос не попадёт в сервер, слушающий <code>8080</code>.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 03. Подготовка и запуск проекта

[Иллюстрация](images/17-setup-launch.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 03/19
Подготовка и запуск проекта</b>

Установи актуальный стабильный <a href="https://go.dev/dl/">Go</a> и Git. Проект использует маршруты Go 1.22+. В терминале выполни
<pre>go version
git clone https://github.com/make-smart-products/codelevel_pygo.git
cd codelevel_pygo/editorial/go_server
go run .</pre>
Первая команда должна вывести версию Go. Последняя запустит сервер и займёт терминал. Во втором терминале выполни <code>curl -i http://127.0.0.1:8080/healthz</code>. В PowerShell используй <code>curl.exe</code>. Ожидай <code>200 OK</code> и <code>{"status":"ok"}</code>. Остановить сервер можно через <code>Ctrl+C</code>.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 04. Первый обработчик

[Иллюстрация](images/03-first-handler.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 04/19 · Собери маршрут с нуля</b>

<pre>package main

import (
    "fmt"
    "log"
    "net/http"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("GET /healthz",
        func(w http.ResponseWriter, r *http.Request) {
            w.Header().Set("Content-Type", "application/json")
            fmt.Fprintln(w, `{"status":"ok"}`)
        })
    log.Fatal(http.ListenAndServe("127.0.0.1:8080", mux))
}</pre>
Сохрани как <code>main.go</code> в отдельной папке. Останови сервер из проекта и выполни <code>go run main.go</code>. <code>ServeMux</code> подберёт обработчик по методу и пути. Для <code>/missing</code> ожидай <code>404</code>. Синтаксис работает с Go 1.22. <a href="https://go.dev/blog/routing-enhancements">Маршрутизация в Go</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 05. Чтение HTTP-ответа

[Иллюстрация](images/05-http-response.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 05/19 · Как читать HTTP-ответ</b>

У <code>curl -i</code> сначала идёт строка со статусом, затем заголовки, пустая строка и тело. Найди <code>Content-Type: application/json</code> и JSON с полем <code>status</code>.

<b>Задание.</b> Выполни <code>curl -i -X POST http://127.0.0.1:8080/healthz</code>. Сравни с GET. Для известного пути и неподдерживаемого метода ожидай <code>405</code> и заголовок <code>Allow</code>.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 06. Викторина о net/http

[Иллюстрация](images/02-toolbox.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 06/19</b>
Узнай пакет по его роли в сервере.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Какой пакет Go принимает HTTP-запросы и даёт тип http.Server?**

- encoding/json
- net/http
- net/url
- os/signal

<details><summary>Правильный ответ и пояснение</summary>

net/http

net/http содержит сервер, маршрутизатор ServeMux и интерфейсы для обработки запроса.

</details>

## 07. Викторина о loopback

[Иллюстрация](images/04-loopback.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 07/19</b>
Проверь, что означает адрес из примера.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Сервер слушает 127.0.0.1:8080. Кто может подключиться к нему напрямую?**

- Любой компьютер в интернете
- Все устройства в домашней сети
- Клиенты на той же машине через loopback
- Только браузер

<details><summary>Правильный ответ и пояснение</summary>

Клиенты на той же машине через loopback

127.0.0.1 — адрес обратной петли. Для связи по локальной сети серверу нужен другой адрес прослушивания.

</details>

## 08. Маршрут с параметром

[Иллюстрация](images/02-routing-explained.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 08/19 · Параметр пути</b>

<pre>mux.HandleFunc("GET /api/hello/{name}", hello)
name := r.PathValue("name")</pre>
Первая строка регистрирует маршрут. В обработчике <code>PathValue</code> берёт значение именованного сегмента из запроса. На схеме метод и путь проходят проверку, а <code>Ada</code> попадает в параметр. Перед этим шагом вернись к полному проекту и запусти <code>go run .</code>.

<b>Проверь.</b> Запроси <code>http://127.0.0.1:8080/api/hello/Ada</code>. Получи <code>{"message":"Hello, Ada!"}</code>. Теперь замени имя на <code>Grace</code>.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 09. Викторина о параметре пути

[Иллюстрация](images/07-path-quiz.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 09/19</b>
Выбери, откуда обработчик читает параметр.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Как получить Grace из GET /api/hello/Grace для шаблона GET /api/hello/{name}?**

- r.URL.Query().Get("name")
- r.Header.Get("name")
- r.Method
- r.PathValue("name")

<details><summary>Правильный ответ и пояснение</summary>

r.PathValue("name")

PathValue возвращает значение именованной части пути. Query читает параметры после знака вопроса.

</details>

## 10. JSON и проверка ввода

[Иллюстрация](images/08-json-validation.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 10/19 · JSON и проверка ввода</b>

В примере имя занимает от 1 до 40 символов. Допустимы буквы и одиночные дефисы между ними. Для <code>/api/hello/Ada123</code> сервер возвращает <code>400</code> и JSON с ошибкой.

<b>Почему это важно.</b> Сначала проверяем ввод и выбираем статус. Затем задаём <code>Content-Type</code>, отправляем статус через <code>WriteHeader</code> и кодируем ответ через <code>json.NewEncoder(w).Encode(value)</code>. Кодировщик сам экранирует строки JSON.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 11. Викторина о статусе ответа

[Иллюстрация](images/09-status-quiz.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 11/19</b>
Отдели выбор маршрута от проверки данных в обработчике.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Какой статус вернёт пример для GET /api/hello/Ada123?**

- 400 Bad Request
- 200 OK
- 404 Not Found
- 405 Method Not Allowed

<details><summary>Правильный ответ и пояснение</summary>

400 Bad Request

Метод и путь подходят шаблону. Имя не проходит проверку, поэтому обработчик возвращает 400.

</details>

## 12. Одновременные запросы

[Иллюстрация](images/10-concurrency.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 12/19 · Запросы идут одновременно</b>

<code>net/http</code> может выполнять несколько обработчиков одновременно. Имя из <code>r.PathValue</code> и переменные внутри обработчика относятся к одному вызову. Общая <code>map</code>, в которую пишут обработчики, требует синхронизации.

<b>Практика.</b> Найди в примере, где формируется приветствие. Объясни, почему два одновременных запроса с разными именами получают разные ответы.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 13. Таймауты

[Иллюстрация](images/11-timeouts.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 13/19 · Таймауты соединения</b>

У <code>http.Server</code> можно отдельно задать время чтения заголовков (<code>ReadHeaderTimeout</code>), чтения запроса целиком (<code>ReadTimeout</code>), записи ответа (<code>WriteTimeout</code>) и ожидания нового запроса по открытому соединению (<code>IdleTimeout</code>).

<b>Практика.</b> Найди эти четыре поля в проекте. Для потокового API пересмотри бюджет записи ответа. <a href="https://pkg.go.dev/net/http#Server">Поля http.Server</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 14. Викторина о чтении заголовков

[Иллюстрация](images/12-slow-header-quiz.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 14/19</b>
Соотнеси настройку с этапом HTTP-соединения.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Клиент слишком медленно присылает HTTP-заголовки. Какой таймаут задаёт предел для этого этапа?**

- IdleTimeout
- WriteTimeout
- ReadHeaderTimeout
- Timeout контекста Shutdown

<details><summary>Правильный ответ и пояснение</summary>

ReadHeaderTimeout

ReadHeaderTimeout ограничивает время чтения заголовков. IdleTimeout относится к паузе между запросами.

</details>

## 15. Мягкое завершение

[Иллюстрация](images/13-graceful-shutdown.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 15/19 · Мягкое завершение</b>

При <code>Ctrl+C</code> пример вызывает <code>server.Shutdown(ctx)</code>. Сервер прекращает принимать новые соединения, закрывает простаивающие и даёт активным запросам завершиться. Контекст ограничивает ожидание пятью секундами. На схеме показана последовательность остановки.

<b>Проверь.</b> Останови сервер и повтори запрос. Затем запусти его снова на том же адресе. <a href="https://pkg.go.dev/net/http#Server.Shutdown">Документация Shutdown</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 16. Викторина об остановке

[Иллюстрация](images/14-server-error-quiz.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 16/19</b>
Разбери, как цикл запуска отличает остановку от ошибки прослушивания порта.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

**Какую ошибку ListenAndServe возвращает при штатном вызове Shutdown?**

- context.DeadlineExceeded
- http.ErrServerClosed
- io.EOF
- nil

<details><summary>Правильный ответ и пояснение</summary>

http.ErrServerClosed

http.ErrServerClosed сигнализирует о штатном закрытии сервера. Другие ошибки запуска стоит обработать отдельно.

</details>

## 17. Тестирование обработчиков

[Иллюстрация](images/15-handler-tests.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 17/19 · Проверяем сервер тестами</b>

<code>httptest.NewRequest</code> создаёт запрос, <code>httptest.NewRecorder</code> записывает ответ. Передай их в маршрутизатор и проверь статус, заголовки и JSON без запуска слушающего порта.

<b>Практическое задание.</b> В <a href="https://github.com/make-smart-products/codelevel_pygo/tree/main/editorial/go_server">проекте</a> выполни <code>go test ./...</code>. Затем добавь маршрут <code>GET /api/version</code> и тест на его JSON-ответ. <a href="https://pkg.go.dev/net/http/httptest">Пакет httptest</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 18. Сборка и запуск файла

[Иллюстрация](images/18-build-binary.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 18/19
Собрать файл и запустить его</b>

<code>go run .</code> собирает и сразу запускает программу. <code>go build</code> сохраняет исполняемый файл для последующих запусков. В папке проекта сначала останови старый процесс и выполни
<pre>go test ./...
go build -o server .</pre>
На Linux и macOS запусти <code>./server</code>. На Windows в PowerShell удобно собрать <code>go build -o server.exe .</code> и запустить <code>.\server.exe</code>. Проверь <code>/healthz</code> из второго терминала.

Файл собирается под выбранные ОС и архитектуру. У нашего примера зависимости входят в стандартную библиотеку. Для переноса собери файл под целевую платформу.

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>

## 19. Основы размещения сервера

[Иллюстрация](images/19-hosting.png)

<b>🐹 Раздел 1 · Разработка и работа серверов · 19/19
От локального запуска к размещению</b>

Для доступа пользователей нужны работающий узел и запущенный процесс. В схеме прокси и Go находятся на одной машине. Домен указывает на публичный адрес, прокси принимает HTTPS на <code>443</code> и передаёт запрос Go на <code>127.0.0.1:8080</code>. Внешние подключения разрешает сетевой экран.

TLS требует действительного сертификата. Менеджер процессов запускает приложение после перезагрузки и собирает журнал. После размещения проверь домен, HTTPS, <code>/healthz</code> и поведение при остановке.

Основные свойства Go-сервиса из раздела — маршруты, JSON, проверка ввода, конкурентные обработчики, таймауты, мягкая остановка и тесты. <a href="https://github.com/make-smart-products/codelevel_pygo/tree/main/editorial/go_server">Код и руководство</a>

Go Gopher · по мотивам персонажа Рене Френч · <a href="https://go.dev/blog/gopher">CC BY 4.0</a>
