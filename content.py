"""Проверяемые учебные задачи: чередование Python и Go, ответ под спойлером."""

from html import escape


def exercise(index):
    if index < 0:
        raise ValueError("Индекс задачи должен быть неотрицательным.")
    language = "Python" if index % 2 == 0 else "Go"
    topic = (index // 2) % 8
    a = index // 16 + 7
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
