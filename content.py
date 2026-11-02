"""Проверяемые учебные задачи: чередование Python и Go, ответ под спойлером."""

from html import escape


def exercise(index):
    if index < 0:
        raise ValueError("Индекс задачи должен быть неотрицательным.")
    language = "Python" if index % 2 == 0 else "Go"
    topic = (index // 2) % 16
    a = index // 32 + 7
    b = a + 3
    if language == "Python":
        examples = [
            ("Целочисленное деление", f"print({a} // 3, {a} % 3)", f"{a // 3} {a % 3}", "Для положительных чисел // даёт целую часть частного, % — остаток."),
            ("Срез списка", f"values = [{a}, {b}, {b+2}, {b+4}]\nprint(values[1:3])", str([b, b+2]), "Начало среза включается, конец не включается. Индексы начинаются с нуля."),
            ("Общий список", f"first = [{a}, {b}]\nsecond = first\nsecond.append({b+1})\nprint(first)", str([a,b,b+1]), "Присваивание не копирует список: обе переменные ссылаются на один объект."),
            ("Копия списка", f"first = [{a}, {b}]\nsecond = first.copy()\nsecond[0] = {b+1}\nprint(first[0], second[0])", f"{a} {b+1}", "copy() создаёт отдельный список. Для вложенных объектов копия остаётся поверхностной."),
            ("Генератор списка", f"print([x * 2 for x in range({a}, {a+3})])", str([a*2,(a+1)*2,(a+2)*2]), "range не включает правую границу, выражение x * 2 применяется к каждому элементу."),
            ("Значение по умолчанию", f"scores = {{'Python': {a}}}\nprint(scores.get('Go', {b}))", str(b), "get возвращает значение по умолчанию, когда ключ отсутствует, и не добавляет его в словарь."),
            ("Распаковка", f"left, right = {a}, {b}\nleft, right = right, left\nprint(left, right)", f"{b} {a}", "Правая часть вычисляется до присваивания. Так можно обменять значения двух переменных."),
            ("Сумма диапазона", f"print(sum(range({a}, {a+4})))", str(4*a+6), "В диапазоне четыре числа: a, a+1, a+2 и a+3. sum складывает их."),
            ("Аргументы функции", f"def multiply(value, factor=2):\n    return value * factor\n\nprint(multiply({a}), multiply({a}, 3))", f"{2*a} {3*a}", "Если factor не передан, используется значение 2. Во втором вызове передаётся 3."),
            ("Фильтрация списка", f"values = [{a}, {a+1}, {a+2}, {a+3}]\nprint([x for x in values if x % 2 == 0])", str([x for x in range(a,a+4) if x%2==0]), "Условие x % 2 == 0 оставляет только чётные числа, сохраняя их порядок."),
            ("Индексы через enumerate", f"values = [{a}, {b}]\nprint(sum(i * value for i, value in enumerate(values, start=1)))", str(a+2*b), "start=1 задаёт индексы 1 и 2. Суммируются произведения индекса на значение."),
            ("Уникальные элементы", f"values = [{a}, {a}, {b}, {b}, {a+1}]\nprint(len(set(values)))", "3", "set удаляет повторы. В исходном списке три различных числа."),
            ("Сортировка без изменения исходника", f"values = [{b}, {a}, {a+1}]\nordered = sorted(values)\nprint(values[0], ordered[0])", f"{b} {a}", "sorted возвращает новый отсортированный список. Исходный список не меняется."),
            ("Генератор словаря", f"squares = {{x: x * x for x in range({a}, {a+3})}}\nprint(squares[{a+1}])", str((a+1)**2), "Для каждого x создаётся пара ключ x — значение x * x. Затем читается значение по ключу."),
            ("Проверка всех и хотя бы одного", f"values = [0, {a}, {b}]\nprint(any(values), all(values))", "True False", "any проверяет наличие хотя бы одного истинного значения. all требует, чтобы истинными были все; 0 считается ложным."),
            ("Объединение последовательностей", f"names = ['Python', 'Go']\nscores = [{a}, {b}]\nprint(dict(zip(names, scores))['Go'])", str(b), "zip объединяет элементы по позициям. dict превращает пары в словарь."),
        ]
    else:
        examples = [
            ("Целочисленное деление", f"fmt.Println({a}/3, {a}%3)", f"{a//3} {a%3}", "Для этих положительных целых / даёт целое частное, % — остаток."),
            ("Срез", f"values := []int{{{a}, {b}, {b+2}, {b+4}}}\nfmt.Println(values[1:3])", f"[{b} {b+2}]", "Индекс начала включён, индекс конца исключён. Индексация начинается с нуля."),
            ("Общий массив срезов", f"first := []int{{{a}, {b}}}\nsecond := first\nsecond[0] = {b+1}\nfmt.Println(first[0])", str(b+1), "Копируется заголовок среза. Оба среза продолжают использовать один базовый массив."),
            ("Копия среза", f"first := []int{{{a}, {b}}}\nsecond := append([]int(nil), first...)\nsecond[0] = {b+1}\nfmt.Println(first[0], second[0])", f"{a} {b+1}", "append в nil-срез создаёт отдельное хранилище для элементов. В этом примере элементы — целые числа."),
            ("Цикл for", f"total := 0\nfor i := {a}; i < {a+3}; i++ {{\n    total += i\n}}\nfmt.Println(total)", str(3*a+3), "Цикл выполнится для трёх значений: a, a+1 и a+2."),
            ("Отсутствующий ключ map", f"scores := map[string]int{{\"Python\": {a}}}\nvalue, ok := scores[\"Go\"]\nfmt.Println(value, ok)", "0 false", "Для отсутствующего ключа возвращается нулевое значение типа. Флаг ok показывает наличие ключа."),
            ("Обмен значений", f"left, right := {a}, {b}\nleft, right = right, left\nfmt.Println(left, right)", f"{b} {a}", "Множественное присваивание позволяет обменять значения без временной переменной."),
            ("Индекс и значение в range", f"values := []int{{{a}, {b}}}\nfor i, value := range values {{\n    fmt.Println(i, value)\n}}", f"0 {a}\n1 {b}", "Для среза range возвращает сначала индекс, затем значение элемента."),
            ("Функция как значение", f"double := func(value int) int {{\n    return value * 2\n}}\nfmt.Println(double({a}))", str(2*a), "Функцию можно сохранить в переменную и вызвать через неё. Результат имеет тип int."),
            ("Копирование массива", f"first := [2]int{{{a}, {b}}}\nsecond := first\nsecond[0] = {a+1}\nfmt.Println(first[0], second[0])", f"{a} {a+1}", "Массив — значение. При присваивании копируются его элементы; это отличается от присваивания среза."),
            ("Отложенные вызовы defer", f"show := func() {{\n    defer fmt.Println({a})\n    defer fmt.Println({b})\n    fmt.Println({a+1})\n}}\nshow()", f"{a+1}\n{b}\n{a}", "defer выполняется при выходе из функции. Несколько отложенных вызовов выполняются в обратном порядке."),
            ("Указатель на переменную", f"value := {a}\nptr := &value\n*ptr += 3\nfmt.Println(value)", str(a+3), "&value получает адрес переменной. Через *ptr изменяется сама переменная, а не отдельная копия."),
            ("Поля структуры", f"type Player struct {{\n    Score int\n}}\np := Player{{Score: {a}}}\np.Score += {b}\nfmt.Println(p.Score)", str(a+b), "Структура объединяет именованные поля. К полю обращаются через точку."),
            ("Обновление map", f"scores := map[string]int{{\"Go\": {a}}}\nscores[\"Go\"] += {b}\nfmt.Println(scores[\"Go\"])", str(a+b), "По ключу читается текущее число, затем увеличенное значение записывается обратно в map."),
            ("Выбор ветки switch", f"value := {a}\nswitch {{\ncase value % 2 == 0:\n    fmt.Println(\"even\")\ndefault:\n    fmt.Println(\"odd\")\n}}", "even" if a%2==0 else "odd", "switch без выражения выбирает первое истинное условие case. default используется, если подходящего case нет."),
            ("Возврат нескольких значений", f"split := func(value int) (int, int) {{\n    return value / 3, value % 3\n}}\nquotient, remainder := split({a})\nfmt.Println(quotient, remainder)", f"{a//3} {a%3}", "Функция Go может вернуть несколько значений. Здесь это целое частное и остаток."),
        ]
    title, code, answer, explanation = examples[topic]
    return {"language": language, "title": title, "code": code, "answer": answer, "explanation": explanation}


def render(index):
    item = exercise(index)
    return (
        f"<b>{item['language']} · задача #{index+1}</b>\n"
        f"{escape(item['title'])}\n\nЧто выведет код?\n\n"
        f"<pre>{escape(item['code'])}</pre>\n\n"
        "Сначала решите самостоятельно, затем откройте ответ.\n\n"
        f"<tg-spoiler>Ответ:\n{escape(item['answer'])}\n\n{escape(item['explanation'])}</tg-spoiler>\n\n"
        f"#{item['language']} #Практика #CodeLevel"
    )
