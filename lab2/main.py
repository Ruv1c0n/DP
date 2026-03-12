#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Программа для решения задачи коммивояжёра с фиксированными начальным и конечным
городами с использованием динамического программирования и битовых масок.

Алгоритм находит минимальную стоимость маршрута, который:
    - начинается в заданном городе,
    - проходит через каждый город ровно один раз,
    - заканчивается в указанном конечном городе.

Для хранения состояний используется таблица динамического программирования:
    dp[mask][v] — минимальная стоимость попасть в город v,
    посетив набор городов mask.

mask — битовая маска посещённых городов.

Сложность алгоритма:
    O(n^2 * 2^n)

Главное меню:
    1 - Решение задачи (с выбором способа ввода)
    2 - Запуск модульных тестов
    3 - Стресс-тестирование
    4 - Справка (help)
    5 - Выход

Вариант 4: Гамильтонов путь с фиксированными начальным и конечным городами

ВАЖНО: Вес 0 в матрице (кроме диагональных элементов) означает отсутствие пути!
"""

import tests
import unittest
import sys
from typing import Optional, Tuple, List, Union, Dict, Any
from pathlib import Path
from io import StringIO
import contextlib
import random
import math
import time

# библиотеки красивого вывода
from rich import print
from rich.tree import Tree
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.columns import Columns
from rich import box

# =========================================================
# ПРОВЕРКА НАЛИЧИЯ БИБЛИОТЕК
# =========================================================

# Пытаемся импортировать библиотеки для визуализации графов
# Если они не установлены, программа будет работать без визуализации
try:
    import networkx as nx
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, Circle
    import matplotlib.patches as mpatches
    VISUALIZATION_AVAILABLE = True  # Флаг доступности визуализации
except ImportError:
    VISUALIZATION_AVAILABLE = False
    # Определяем заглушки для случаев, когда библиотеки не доступны
    nx = None
    plt = None
    mpatches = None

# Проверка наличия Tkinter для GUI ввода матрицы
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    GUI_AVAILABLE = True  # Флаг доступности GUI
except ImportError:
    GUI_AVAILABLE = False
    tk = None
    ttk = None
    messagebox = None

# Создаем консоль для красивого вывода
console = Console()

# Константы
INF = 10 ** 12  # "Бесконечность" для обозначения отсутствия пути
NO_PATH = 0  # Явное обозначение отсутствия пути (кроме диагонали)


# =========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВВОДА
# =========================================================

def safe_input(prompt: str) -> str:
    """
    Безопасный ввод с обработкой ошибок.

    Функция оборачивает стандартный input() в try-except для корректной
    обработки ситуации, когда пользователь отправляет EOF (Ctrl+D/Ctrl+Z)
    или прерывает программу (Ctrl+C).

    Parameters
    ----------
    prompt : str
        Приглашение для ввода

    Returns
    -------
    str
        Введенная пользователем строка с удаленными пробелами в начале и конце
    """
    try:
        return input(prompt).strip()
    except EOFError:
        # Обработка Ctrl+D (конец файла)
        print("[red]Обнаружен конец файла. Завершение программы...[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        # Обработка Ctrl+C (прерывание программы)
        print("\n[yellow]Программа прервана пользователем[/yellow]")
        sys.exit(0)
    except Exception as e:
        # Обработка прочих ошибок ввода
        print(f"[red]Ошибка ввода: {e}[/red]")
        return ""


def safe_int(prompt: str,
             minimum: Optional[int] = None,
             maximum: Optional[int] = None,
             test_mode: bool = False) -> int:
    """
    Безопасный ввод целого числа с проверкой диапазона значений.
    
    Parameters
    ----------
    prompt : str
        Приглашение для ввода
    minimum : Optional[int]
        Минимальное допустимое значение
    maximum : Optional[int]
        Максимальное допустимое значение
    test_mode : bool
        Режим тестирования - если True и входные данные закончились,
        выбрасывает исключение вместо бесконечного цикла
    
    Returns
    -------
    int
        Введенное число
    
    Raises
    ------
    EOFError
        В режиме тестирования при исчерпании входных данных
    ValueError
        При некорректном вводе в режиме тестирования
    RuntimeError
        При превышении количества попыток ввода
    """
    attempts = 0
    max_attempts = 100  # Защита от бесконечного цикла в любом режиме

    while attempts < max_attempts:
        attempts += 1
        value = safe_input(prompt)

        # Проверка на пустой ввод
        if value == "":
            if test_mode:
                raise EOFError(
                    "Исчерпаны входные данные в режиме тестирования")
            print("[red]Ошибка: ввод не может быть пустым[/red]")
            continue

        try:
            number = int(value)

            # Проверка минимального значения
            if minimum is not None and number < minimum:
                print(f"[red]Число должно быть ≥ {minimum}[/red]")
                if test_mode and attempts >= max_attempts // 2:
                    raise ValueError(
                        f"Число {number} меньше минимального {minimum}")
                continue

            # Проверка максимального значения
            if maximum is not None and number > maximum:
                print(f"[red]Число должно быть ≤ {maximum}[/red]")
                if test_mode and attempts >= max_attempts // 2:
                    raise ValueError(
                        f"Число {number} больше максимального {maximum}")
                continue

            return number

        except ValueError:
            print("[red]Ошибка: введите целое число[/red]")
            if test_mode and attempts >= max_attempts // 2:
                raise ValueError(f"Некорректный ввод: {value}")

    # Если превышено количество попыток
    raise RuntimeError(
        f"Превышено максимальное количество попыток ввода ({max_attempts})")


# =========================================================
# ВВОД МАТРИЦЫ
# =========================================================

def read_matrix(n: int, test_mode: bool = False) -> List[List[int]]:
    """
    Ввод матрицы расстояний в консольном режиме.
    
    Пользователь вводит веса для каждой пары городов.
    Для обозначения отсутствия пути можно ввести 'x'.
    
    Parameters
    ----------
    n : int
        Размер матрицы (количество городов)
    test_mode : bool
        Режим тестирования
    
    Returns
    -------
    List[List[int]]
        Матрица расстояний размером n x n
    """
    # Создаем пустую матрицу n x n
    matrix = [[0] * n for _ in range(n)]

    print()
    print("[bold cyan]Введите матрицу весов[/bold cyan]")
    print("[dim]Введите 'x' если ребра нет[/dim]\n")

    # Цикл по строкам и столбцам
    for i in range(n):
        for j in range(n):
            if i == j:
                # Диагональные элементы всегда 0
                matrix[i][j] = 0
                continue

            # Ввод значения для элемента [i][j]
            while True:
                try:
                    value = safe_input(f"Вес {i+1} → {j+1}: ")

                    if test_mode and value == "":
                        raise EOFError(
                            "Исчерпаны входные данные в режиме тестирования")

                    if value.lower() == "x":
                        # 'x' означает отсутствие пути
                        matrix[i][j] = INF
                        break

                    # Преобразуем в число
                    matrix[i][j] = int(value)
                    break

                except ValueError:
                    print("[red]Введите целое число или 0[/red]")
                    if test_mode:
                        raise ValueError(
                            f"Некорректный ввод для элемента [{i}][{j}]: {value}")
                except EOFError as e:
                    if test_mode:
                        raise e
                    print("[red]Ошибка ввода[/red]")

    return matrix


# =========================================================
# ПРОВЕРКА МАТРИЦЫ
# =========================================================

def validate_matrix(matrix: List[List[int]]) -> bool:
    """
    Проверка корректности матрицы расстояний.
    
    Выполняет следующие проверки:
    1. Матрица должна быть квадратной
    2. Диагональные элементы должны быть равны 0
    
    Parameters
    ----------
    matrix : List[List[int]]
        Матрица для проверки
    
    Returns
    -------
    bool
        True если матрица корректна
    
    Raises
    ------
    ValueError
        Если матрица не является квадратной
    """
    n = len(matrix)

    # Проверка на квадратность матрицы
    for i, row in enumerate(matrix):
        if len(row) != n:
            raise ValueError(
                f"Матрица должна быть квадратной. Строка {i} имеет длину {len(row)}")

    # Проверка диагональных элементов
    for i in range(n):
        if matrix[i][i] != 0:
            print(
                f"[yellow]Предупреждение: элемент [{i}][{i}] должен быть 0, исправлено[/yellow]")
            matrix[i][i] = 0

    return True


# =========================================================
# ГЕНЕРАЦИЯ ГРАФА
# =========================================================

def generate_graph(n: int,
                   max_weight: int = 50,
                   allow_zero: bool = False) -> List[List[int]]:
    """
    Генерация случайного графа.
    
    Создает матрицу расстояний со случайными весами.
    Можно задать вероятность отсутствия ребер.
    
    Parameters
    ----------
    n : int
        Размер матрицы (количество городов)
    max_weight : int
        Максимальный вес ребра
    allow_zero : bool
        Разрешить ли нулевые веса (которые будут интерпретироваться как отсутствие пути)
    
    Returns
    -------
    List[List[int]]
        Сгенерированная матрица расстояний
    """
    # Создаем пустую матрицу
    matrix = [[0] * n for _ in range(n)]

    # Заполняем матрицу случайными значениями
    for i in range(n):
        for j in range(n):
            if i == j:
                continue

            # С вероятностью 10% генерируем отсутствие пути (если разрешено)
            if allow_zero and random.random() < 0.1:  # 10% вероятность отсутствия пути
                matrix[i][j] = INF
            else:
                # Случайный вес от 1 до max_weight
                matrix[i][j] = random.randint(1, max_weight)

    return matrix


# =========================================================
# ВЫВОД МАТРИЦЫ
# =========================================================

def print_matrix(matrix: List[List[int]]) -> None:
    """
    Красивый вывод матрицы расстояний с использованием rich.
    
    Отображает матрицу в виде таблицы с цветовым кодированием:
    - Красный ∞ для отсутствующих путей
    - Желтый 0 для нулевых весов (кроме диагонали)
    
    Parameters
    ----------
    matrix : List[List[int]]
        Матрица для вывода
    """
    # Создаем таблицу с заголовком
    table = Table(title="Матрица расстояний", box=box.ROUNDED)

    n = len(matrix)

    # Добавляем пустой столбец для номеров строк
    table.add_column("", style="cyan")

    # Добавляем столбцы для городов
    for i in range(n):
        table.add_column(str(i + 1), justify="center", style="green")

    # Заполняем строки таблицы
    for i in range(n):
        row = [str(i + 1)]  # Номер строки

        for j in range(n):
            value = matrix[i][j]

            # Применяем цветовое кодирование
            if value >= INF:
                row.append("[red]∞[/red]")  # Красный для бесконечности
            elif value == 0 and i != j:
                row.append("[yellow]0[/yellow]")  # Желтый для нулевых весов
            else:
                row.append(str(value))  # Обычный текст для остальных

        table.add_row(*row)

    # Выводим таблицу
    console.print(table)


# =========================================================
# АЛГОРИТМ TSP (ДИНАМИЧЕСКОЕ ПРОГРАММИРОВАНИЕ + БИТОВЫЕ МАСКИ)
# =========================================================

def tsp(matrix: List[List[int]],
        start: int,
        end: int,
        visualize: bool = False) -> Tuple[int, List[int]]:
    """
    Решение задачи коммивояжёра методом динамического программирования.

    АЛГОРИТМ:
    1. Создаем таблицу dp[mask][v], где mask - битовая маска посещенных городов,
       v - текущий город. dp[mask][v] хранит минимальную стоимость пути,
       который начинается в start, проходит через все города из mask и
       заканчивается в v.
    
    2. Начальное состояние: dp[1<<start][start] = 0
    
    3. Для каждой маски и каждого города u в маске, пытаемся перейти в город v,
       который еще не посещен, добавляя вес ребра u->v.
    
    4. Ответ: dp[(1<<n)-1][end] - минимальная стоимость пути, посетившего все
       города и заканчивающегося в end.
    
    5. Восстанавливаем путь с помощью таблицы parent.

    Сложность алгоритма: O(n^2 * 2^n)
    
    Parameters
    ----------
    matrix : List[List[int]]
        Матрица расстояний
    start : int
        Начальный город (индекс с 0)
    end : int
        Конечный город (индекс с 0)
    visualize : bool
        Флаг для включения визуализации (не используется в этой версии)
    
    Returns
    -------
    Tuple[int, List[int]]
        (стоимость маршрута, список городов в порядке посещения)
        Если маршрут не существует, возвращает (-1, [])
    
    Notes
    -----
    Вес 0 при i != j интерпретируется как отсутствие пути!
    """
    # Проверка матрицы на корректность
    try:
        validate_matrix(matrix)
    except ValueError as e:
        print(f"[red]Ошибка в матрице: {e}[/red]")
        return -1, []

    n = len(matrix)

    # Проверка корректности индексов начального и конечного городов
    if start < 0 or start >= n:
        print(f"[red]Начальный город должен быть от 1 до {n}[/red]")
        return -1, []
    if end < 0 or end >= n:
        print(f"[red]Конечный город должен быть от 1 до {n}[/red]")
        return -1, []

    # Количество возможных масок = 2^n
    size = 1 << n

    # dp[mask][v] - минимальная стоимость пути, заканчивающегося в v,
    # посетившего города из mask
    dp = [[INF] * n for _ in range(size)]

    # parent[mask][v] - предыдущий город в оптимальном пути,
    # заканчивающемся в v с маской mask (используется для восстановления пути)
    parent = [[-1] * n for _ in range(size)]

    # Начальное состояние: посещен только стартовый город
    dp[1 << start][start] = 0

    # Основной цикл динамического программирования
    # Перебираем все возможные маски посещенных городов
    for mask in range(size):
        for u in range(n):
            # Пропускаем, если город u не в маске
            if not (mask & (1 << u)):
                continue

            # Пытаемся перейти в город v
            for v in range(n):
                # Пропускаем, если это ребро отсутствует (вес 0 при u != v)
                if u != v and matrix[u][v] == 0:
                    continue

                # Пропускаем, если город v уже посещен
                if mask & (1 << v):
                    continue

                weight = matrix[u][v]

                # Пропускаем, если путь отсутствует (бесконечность)
                if weight >= INF:
                    continue

                # Новая маска с добавленным городом v
                new_mask = mask | (1 << v)
                # Новая стоимость пути
                new_cost = dp[mask][u] + weight

                # Если нашли более дешевый путь, обновляем значения
                if new_cost < dp[new_mask][v]:
                    dp[new_mask][v] = new_cost
                    parent[new_mask][v] = u

    # Полная маска (все города посещены)
    full_mask = (1 << n) - 1
    cost = dp[full_mask][end]

    # Если стоимость бесконечна, маршрут не существует
    if cost >= INF:
        return -1, []

    # ВОССТАНОВЛЕНИЕ ПУТИ
    # Идем от конечного города назад к начальному, используя parent
    path = []
    mask = full_mask
    v = end

    while v != -1:
        path.append(v + 1)  # +1 для вывода пользователю (1-индексация)
        p = parent[mask][v]
        mask ^= (1 << v)  # Убираем текущий город из маски
        v = p

    # Разворачиваем путь, так как шли от конца к началу
    path.reverse()

    return cost, path


# =========================================================
# ВЫВОД РЕШЕНИЯ
# =========================================================

def print_solution(cost: int,
                   path: List[int]) -> None:
    """
    Вывод найденного маршрута в красивом формате.
    
    Parameters
    ----------
    cost : int
        Стоимость найденного маршрута
    path : List[int]
        Список городов в порядке посещения
    """
    if cost == -1 or not path:
        # Маршрут не найден
        console.print(
            Panel(
                "[red]Маршрут не существует[/red]",
                title="Результат",
                border_style="red"
            )
        )
        return

    # Создаем таблицу с результатами
    table = Table(title="Оптимальный маршрут", box=box.ROUNDED)
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="green")

    table.add_row("Минимальная стоимость", str(cost))
    table.add_row("Маршрут", " → ".join(map(str, path)))

    console.print(table)


# =========================================================
# ТЕСТЫ
# =========================================================

def run_unit_tests() -> None:
    """
    Запуск автотестов из файла tests.py с упрощенным выводом.
    """
    # Загружаем тесты из модуля tests
    suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
    console.print("\n[bold cyan]Запуск автотестов...[/bold cyan]\n")

    # Создаем свой обработчик результатов для кастомного вывода
    class CustomTestResult(unittest.TextTestResult):
        """Кастомный класс для форматирования вывода тестов."""

        def getDescription(self, test):
            """
            Возвращает только docstring теста без имени класса и метода.
            """
            doc_first_line = test.shortDescription()
            if doc_first_line:
                return doc_first_line
            else:
                # Если нет docstring, возвращаем имя метода
                return str(test).split()[0]

    # Создаем свой runner с кастомным result class
    class CustomTestRunner(unittest.TextTestRunner):
        """Кастомный runner для использования нашего форматирования."""

        def _makeResult(self):
            return CustomTestResult(self.stream, self.descriptions, self.verbosity)

    # Запускаем тесты с кастомным runner'ом
    runner = CustomTestRunner(verbosity=2)
    runner.run(suite)


def stress_test() -> None:
    """
    Стресс-тестирование алгоритма.
    
    Генерирует большое количество случайных графов и запускает на них алгоритм.
    Используется для проверки производительности и стабильности.
    """
    iterations = safe_int("Количество тестов: ", 1, 100000)
    console.print("\n[bold cyan]Запуск стресс-теста[/bold cyan]\n")

    # Используем прогресс-бар для отображения процесса
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task("Тестирование...", total=iterations)

        for _ in range(iterations):
            # Генерируем случайный граф
            n = random.randint(3, 8)
            dist = generate_graph(n, max_weight=50, allow_zero=True)
            start = random.randint(0, n-1)
            end = random.randint(0, n-1)

            # Запускаем алгоритм
            tsp(dist, start, end)

            # Обновляем прогресс
            progress.update(task, advance=1)

    console.print("\n[green]Стресс-тест завершён[/green]\n")


# =========================================================
# РЕШЕНИЕ ЗАДАЧИ
# =========================================================

def solve_problem() -> None:
    """
    Основной сценарий решения задачи.
    
    Последовательность действий:
    1. Ввод количества городов
    2. Выбор способа ввода данных (консоль, случайный, GUI)
    3. Ввод/генерация матрицы расстояний
    4. Ввод начального и конечного городов
    5. Запуск алгоритма TSP
    6. Вывод результата
    7. Опционально - анимация маршрута
    """
    # Показываем меню выбора режима ввода СНАЧАЛА
    print("\n[bold cyan]Выберите способ ввода данных:[/bold cyan]")
    print("1 — ввести матрицу вручную (консоль)")
    print("2 — случайный граф")
    print("3 — ввести матрицу вручную (GUI)")

    mode = safe_int("Выбор: ", 1, 3)

    matrix = None
    n = None

    if mode == 2:
        # Случайный граф - нужно знать размер
        n = safe_int("Введите количество городов: ", 2, 15)
        matrix = generate_graph(n, allow_zero=True)
        console.print("[green]Сгенерирован случайный граф[/green]")
    elif mode == 3:
        # GUI ввод - размер задается в самом GUI
        if not GUI_AVAILABLE:
            console.print(
                "[red]GUI режим недоступен: не установлен Tkinter[/red]")
            return

        console.print(
            "\n[bold cyan]Запуск графического интерфейса...[/bold cyan]")
        matrix = gui_input_mode()  # Без параметра, начальный размер 4
        if matrix is None:
            # Если пользователь отменил ввод, возвращаемся в меню
            return
        n = len(matrix)  # Получаем размер из полученной матрицы
        console.print("[green]Матрица успешно введена через GUI[/green]")
    else:
        # Консольный ввод - сначала размер, потом матрица
        n = safe_int("Введите количество городов: ", 2, 15)
        matrix = read_matrix(n)

    # Проверяем, что матрица получена
    if matrix is None:
        console.print("[red]Ошибка получения матрицы[/red]")
        return

    # Выводим матрицу
    print_matrix(matrix)

    # Ввод начального и конечного городов
    start = safe_int("Начальный город: ", 1, n) - 1
    end = safe_int("Конечный город: ", 1, n) - 1

    # Запрос визуализации
    show_animation = False
    if VISUALIZATION_AVAILABLE:
        show_animation = safe_int(
            "\nПоказать анимацию маршрута?\n1 — да\n0 — нет\nВыбор: ",
            0,
            1
        ) == 1
    else:
        console.print(
            "\n[dim]Анимация недоступна (установите networkx и matplotlib для визуализации)[/dim]")

    # Решение задачи
    start_time = time.time()
    cost, path = tsp(matrix, start, end)
    end_time = time.time()

    # Вывод результата
    print_solution(cost, path)

    # Анимация если нужно
    if show_animation and cost != -1 and path and VISUALIZATION_AVAILABLE:
        animate_path(matrix, path, start, end)

    console.print(
        f"\n[dim]Время работы: {end_time - start_time:.6f} сек[/dim]")


# =========================================================
# ГЛАВНОЕ МЕНЮ
# =========================================================

def main_menu() -> None:
    """
    Главное меню программы.
    
    Отображает доступные опции и обрабатывает выбор пользователя.
    Меню циклическое, выход только по выбору пункта 4.
    """
    while True:
        # Формируем информацию о доступных режимах с цветовым кодированием
        status_text = "[bold cyan]Лабораторная работа №2[/bold cyan]\n"
        status_text += "Задача коммивояжёра\n\n"

        status_text += "[bold]Доступные режимы:[/bold]\n"
        status_text += "1 — Решить задачу\n"

        # Отображаем статус GUI ввода
        if GUI_AVAILABLE:
            status_text += "   └─ Ввод: консоль / случайный / [green]GUI[/green]\n"
        else:
            status_text += "   └─ Ввод: консоль / случайный ([yellow]GUI недоступен[/yellow])\n"

        # Отображаем статус визуализации
        if VISUALIZATION_AVAILABLE:
            status_text += "   └─ Визуализация: [green]доступна[/green]\n"
        else:
            status_text += "   └─ Визуализация: [yellow]недоступна[/yellow] (pip install networkx matplotlib)\n"

        status_text += "\n2 — Запустить тесты\n"
        status_text += "3 — Стресс тест\n"
        status_text += "4 — Справка (help)\n"
        status_text += "5 — Выход\n"

        # Добавляем информацию по установке недостающих библиотек
        if not GUI_AVAILABLE or not VISUALIZATION_AVAILABLE:
            status_text += "\n[dim]Для полной функциональности установите:\n"
            if not GUI_AVAILABLE:
                status_text += "  • Tkinter (обычно встроен в Python)\n"
            if not VISUALIZATION_AVAILABLE:
                status_text += "  • networkx и matplotlib (pip install networkx matplotlib)\n"
            status_text += "[/dim]"

        # Отображаем меню в красивом обрамлении
        console.print(Panel(status_text, border_style="cyan"))

        # Получаем выбор пользователя (теперь максимум 5)
        choice = safe_int("Выберите пункт: ", 1, 5)

        # Обрабатываем выбор
        if choice == 1:
            solve_problem()
        elif choice == 2:
            run_unit_tests()
        elif choice == 3:
            stress_test()
        elif choice == 4:
            show_help()
        else:
            print("[yellow]Выход из программы[/yellow]")
            break

# =========================================================
# ВИЗУАЛИЗАЦИЯ ГРАФА
# =========================================================


if VISUALIZATION_AVAILABLE:
    def animate_path(matrix: List[List[int]],
                     path: List[int],
                     start: int,
                     end: int) -> None:
        """
        Анимация построения оптимального маршрута на графе.
        
        Функция создает граф на основе матрицы расстояний и поэтапно
        показывает построение маршрута с задержкой 2 секунды на каждый шаг.
        
        Parameters
        ----------
        matrix : List[List[int]]
            Матрица расстояний
        path : List[int]
            Найденный оптимальный маршрут (1-индексация)
        start : int
            Начальный город (0-индексация)
        end : int
            Конечный город (0-индексация)
        """
        if not path:
            console.print(
                "[yellow]Маршрут не найден, анимация невозможна[/yellow]")
            return

        n = len(matrix)

        # ===== СОЗДАНИЕ ГРАФА =====
        # Используем неориентированный граф (можно изменить на DiGraph для ориентированного)
        G = nx.Graph()

        # Добавляем вершины (используем 0-индексацию для внутреннего представления)
        for i in range(n):
            G.add_node(i)

        # Добавляем ребра с весами (только верхний треугольник для неориентированного графа)
        for i in range(n):
            for j in range(i+1, n):
                if matrix[i][j] < INF and matrix[i][j] != 0:
                    G.add_edge(i, j, weight=matrix[i][j])

        # ===== ПОЗИЦИОНИРОВАНИЕ ВЕРШИН =====
        # Используем фиксированное seed для воспроизводимости
        # spring_layout располагает вершины так, чтобы ребра были примерно одинаковой длины
        pos = nx.spring_layout(G, seed=42, k=2, iterations=50)

        # Словарь для отображения меток (1-индексация для пользователя)
        labels = {i: str(i+1) for i in range(n)}

        # ===== НАСТРОЙКА АНИМАЦИИ =====
        # Включаем интерактивный режим matplotlib
        plt.ion()
        fig, ax = plt.subplots(figsize=(12, 8))

        console.print("\n[bold cyan]Анимация построения маршрута:[/bold cyan]")
        console.print("[dim]Каждый шаг отображается 2 секунды[/dim]\n")

        # Преобразуем path в 0-индексацию для внутреннего использования
        path_0 = [p - 1 for p in path]

        # ===== ПОШАГОВОЕ ОТОБРАЖЕНИЕ =====
        for step in range(len(path_0)-1):
            ax.clear()

            # Рисуем базовый граф (все вершины и ребра серым)
            nx.draw(G, pos,
                    labels=labels,
                    node_color="lightblue",
                    node_size=2000,
                    font_size=12,
                    font_weight='bold',
                    edge_color='gray',
                    width=1,
                    ax=ax)

            # Добавляем подписи весов ребер
            weights = nx.get_edge_attributes(G, 'weight')
            weights_labels = {(u, v): str(w) for (u, v), w in weights.items()}
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=weights_labels, font_size=10, ax=ax)

            # Выделяем уже пройденные ребра красным
            edges = []
            for i in range(step + 1):
                edges.append((path_0[i], path_0[i+1]))

            if edges:
                nx.draw_networkx_edges(
                    G,
                    pos,
                    edgelist=edges,
                    edge_color="red",
                    width=3,
                    ax=ax
                )

            # ===== ПОДСВЕТКА ГОРОДОВ =====
            # Разные цвета для разных типов городов:
            # - текущий город: зеленый
            # - следующий город: коралловый
            # - уже посещенные: голубой
            # - остальные: светло-синий
            current_city = path_0[step]
            next_city = path_0[step + 1]

            node_colors = []
            for node in G.nodes():
                if node == current_city:
                    node_colors.append('lightgreen')
                elif node == next_city:
                    node_colors.append('lightcoral')
                elif node in path_0[:step+1]:
                    node_colors.append('lightskyblue')
                else:
                    node_colors.append('lightblue')

            # Перерисовываем вершины с новыми цветами
            nx.draw_networkx_nodes(G, pos,
                                   node_color=node_colors,
                                   node_size=2000,
                                   edgecolors='black',
                                   linewidths=2,
                                   ax=ax)

            # Перерисовываем метки (чтобы они были поверх вершин)
            nx.draw_networkx_labels(
                G, pos, labels=labels, font_size=12, font_weight='bold', ax=ax)

            # ===== ЗАГОЛОВОК С ИНФОРМАЦИЕЙ =====
            # Вычисляем накопленную стоимость
            total_cost = 0
            for i in range(step + 1):
                total_cost += matrix[path_0[i]][path_0[i+1]]

            ax.set_title(f"Шаг {step + 1}: {path_0[step] + 1} → {path_0[step+1] + 1} "
                         f"(вес: {matrix[path_0[step]][path_0[step+1]]}, накоплено: {total_cost})",
                         fontsize=14, fontweight='bold')

            plt.tight_layout()
            plt.pause(2)  # Задержка 2 секунды

        # ===== ФИНАЛЬНЫЙ КАДР =====
        # Показываем полный маршрут
        ax.clear()

        # Базовый граф
        nx.draw(G, pos,
                labels=labels,
                node_color="lightblue",
                node_size=2000,
                font_size=12,
                font_weight='bold',
                edge_color='gray',
                width=1,
                ax=ax)

        # Подписи весов
        weights = nx.get_edge_attributes(G, 'weight')
        weights_labels = {(u, v): str(w) for (u, v), w in weights.items()}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=weights_labels, font_size=10, ax=ax)

        # Все ребра маршрута красным
        all_edges = [(path_0[i], path_0[i+1]) for i in range(len(path_0)-1)]
        if all_edges:
            nx.draw_networkx_edges(G, pos, edgelist=all_edges,
                                   edge_color="red", width=3, ax=ax)

        # Подсвечиваем все города в маршруте
        node_colors = []
        for node in G.nodes():
            if node == path_0[0]:
                node_colors.append('lightgreen')  # Начальный
            elif node == path_0[-1]:
                node_colors.append('lightcoral')  # Конечный
            elif node in path_0:
                node_colors.append('lightskyblue')  # Промежуточные
            else:
                node_colors.append('lightblue')  # Остальные

        nx.draw_networkx_nodes(G, pos,
                               node_color=node_colors,
                               node_size=2000,
                               edgecolors='black',
                               linewidths=2,
                               ax=ax)

        nx.draw_networkx_labels(G, pos, labels=labels,
                                font_size=12, font_weight='bold', ax=ax)

        # Общая стоимость маршрута
        total_cost = 0
        for i in range(len(path_0)-1):
            total_cost += matrix[path_0[i]][path_0[i+1]]

        ax.set_title(f"Оптимальный маршрут (стоимость: {total_cost})",
                     fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.pause(2)

        # Выключаем интерактивный режим и показываем финальный график
        plt.ioff()
        plt.show()

        # Показываем таблицу с деталями маршрута
        show_path_details(matrix, path)

    def show_path_details(matrix: List[List[int]], path: List[int]) -> None:
        """
        Показывает детальную таблицу маршрута с весами на каждом шаге.
        
        Parameters
        ----------
        matrix : List[List[int]]
            Матрица расстояний
        path : List[int]
            Найденный маршрут (1-индексация)
        """
        # Создаем таблицу с колонками
        table = Table(title="Детали маршрута", box=box.ROUNDED)
        table.add_column("Шаг", style="cyan", justify="center")
        table.add_column("Откуда", style="green", justify="center")
        table.add_column("Куда", style="green", justify="center")
        table.add_column("Вес", style="yellow", justify="center")
        table.add_column("Накопленная стоимость",
                         style="magenta", justify="center")

        # Заполняем таблицу
        total_cost = 0
        path_0 = [p - 1 for p in path]  # Переводим в 0-индексацию

        for i in range(len(path_0) - 1):
            current = path_0[i]
            next_city = path_0[i + 1]
            weight = matrix[current][next_city]
            total_cost += weight

            table.add_row(
                str(i + 1),
                str(current + 1),  # Обратно в 1-индексацию для отображения
                str(next_city + 1),
                str(weight),
                str(total_cost)
            )

        console.print("\n")
        console.print(table)
else:
    # Заглушки для случаев, когда визуализация недоступна
    def animate_path(matrix: List[List[int]],
                     path: List[int],
                     start: int,
                     end: int) -> None:
        """Заглушка для анимации, когда библиотеки не установлены."""
        console.print(
            "[yellow]Анимация недоступна: не установлены библиотеки networkx и/или matplotlib[/yellow]")

    def show_path_details(matrix: List[List[int]], path: List[int]) -> None:
        """Заглушка для деталей маршрута."""
        pass


# =========================================================
# GUI ВВОД МАТРИЦЫ
# =========================================================

if GUI_AVAILABLE:
    def gui_matrix_input(initial_size: int = 4) -> List[List[int]]:
        """
        Ввод матрицы расстояний через графический интерфейс на Tkinter.
        
        Parameters
        ----------
        initial_size : int
            Начальный размер матрицы (из консольного ввода)
        
        Returns
        -------
        List[List[int]]
            Введенная матрица расстояний
        """
        # Создаем главное окно
        root = tk.Tk()
        root.title("Ввод матрицы расстояний")
        root.geometry("800x600")
        root.resizable(True, True)

        # Переменные для хранения состояния
        # Используем переданное значение
        size_var = tk.IntVar(value=initial_size)
        entries = []  # Список полей ввода
        matrix = []   # Результирующая матрица

        # ===== СОЗДАНИЕ ФРЕЙМОВ =====
        # Верхний фрейм для элементов управления
        top_frame = ttk.Frame(root, padding="10")
        top_frame.pack(fill=tk.X)

        # Фрейм для кнопок управления
        control_frame = ttk.Frame(top_frame)
        control_frame.pack()

        # Фрейм для матрицы с прокруткой
        matrix_frame = ttk.Frame(root, padding="10")
        matrix_frame.pack(fill=tk.BOTH, expand=True)

        # ===== СОЗДАНИЕ ОБЛАСТИ С ПРОКРУТКОЙ =====
        # Canvas для прокрутки
        canvas = tk.Canvas(matrix_frame)

        # Полосы прокрутки
        scrollbar_y = ttk.Scrollbar(
            matrix_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(
            matrix_frame, orient="horizontal", command=canvas.xview)

        # Фрейм внутри canvas, который будет прокручиваться
        scrollable_frame = ttk.Frame(canvas)

        # При изменении размера scrollable_frame обновляем область прокрутки canvas
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Создаем окно в canvas для scrollable_frame
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        # Настраиваем прокрутку
        canvas.configure(yscrollcommand=scrollbar_y.set,
                         xscrollcommand=scrollbar_x.set)

        # ===== ФУНКЦИЯ СОЗДАНИЯ МАТРИЦЫ =====
        def build_matrix():
            """
            Создает поля ввода для матрицы текущего размера.
            Удаляет предыдущие поля и создает новые.
            """
            nonlocal entries

            # Очищаем предыдущие виджеты
            for widget in scrollable_frame.winfo_children():
                widget.destroy()

            n = size_var.get()
            entries = [[None] * n for _ in range(n)]

            # Заголовки столбцов
            ttk.Label(scrollable_frame, text="", font=("Arial", 10, "bold")).grid(
                row=0, column=0, padx=5, pady=5)

            for j in range(n):
                ttk.Label(scrollable_frame, text=f"Город {j+1}", font=(
                    "Arial", 10, "bold")).grid(row=0, column=j+1, padx=5, pady=5)

            # Создаем поля ввода для каждой ячейки
            for i in range(n):
                # Заголовок строки
                ttk.Label(scrollable_frame, text=f"Город {i+1}", font=(
                    "Arial", 10, "bold")).grid(row=i+1, column=0, padx=5, pady=5)

                for j in range(n):
                    # Создаем поле ввода
                    e = ttk.Entry(scrollable_frame, width=8, justify="center")
                    e.grid(row=i+1, column=j+1, padx=2, pady=2)

                    # Диагональные элементы блокируем и ставим 0
                    if i == j:
                        e.insert(0, "0")
                        e.configure(state="readonly")
                    else:
                        # Автозаполнение симметричных элементов
                        def make_callback(i_idx, j_idx):
                            """
                            Создает функцию обратного вызова для автоматического
                            копирования значения в симметричную ячейку.
                            """
                            def callback(event):
                                if i_idx != j_idx:
                                    value = entries[i_idx][j_idx].get()
                                    if value.isdigit() and entries[j_idx][i_idx]:
                                        entries[j_idx][i_idx].delete(0, tk.END)
                                        entries[j_idx][i_idx].insert(0, value)
                            return callback

                        e.bind("<KeyRelease>", make_callback(i, j))

                    entries[i][j] = e

            # Обновляем область прокрутки
            canvas.configure(scrollregion=canvas.bbox("all"))

        # ===== ФУНКЦИЯ СБОРА ДАННЫХ =====
        def submit_matrix():
            """
            Собирает данные из полей ввода, проверяет корректность
            и закрывает окно при успехе.
            """
            nonlocal matrix

            try:
                n = size_var.get()

                # Дополнительная проверка на максимальный размер
                if n > 15:
                    messagebox.showerror(
                        "Ошибка", f"Размер матрицы не может быть больше 15!\nТекущий размер: {n}")
                    return

                matrix = [[0] * n for _ in range(n)]

                # Собираем значения из полей ввода
                for i in range(n):
                    for j in range(n):
                        if i == j:
                            matrix[i][j] = 0
                        else:
                            value = entries[i][j].get().strip()

                            # Проверка на пустое поле
                            if value == "":
                                messagebox.showerror(
                                    "Ошибка", f"Заполните все поля!\nПустое поле в [{i+1}][{j+1}]")
                                return

                            # Проверка на число
                            try:
                                val = int(value)
                                if val < 0:
                                    messagebox.showerror(
                                        "Ошибка", "Веса не могут быть отрицательными!")
                                    return
                                matrix[i][j] = val
                            except ValueError:
                                messagebox.showerror(
                                    "Ошибка", f"Введите целое число в [{i+1}][{j+1}]")
                                return

                # Закрываем окно при успехе
                root.destroy()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при сборе данных: {e}")

        # ===== ФУНКЦИЯ СЛУЧАЙНОГО ЗАПОЛНЕНИЯ =====
        def random_fill():
            """Заполняет матрицу случайными значениями от 1 до 20."""
            n = size_var.get()
            for i in range(n):
                for j in range(n):
                    if i != j:
                        val = random.randint(1, 20)
                        entries[i][j].delete(0, tk.END)
                        entries[i][j].insert(0, str(val))

        # ===== ФУНКЦИЯ ОЧИСТКИ =====
        def clear_matrix():
            """Очищает все поля ввода (кроме диагонали)."""
            n = size_var.get()
            for i in range(n):
                for j in range(n):
                    if i != j:
                        entries[i][j].delete(0, tk.END)

        # ===== СОЗДАНИЕ ЭЛЕМЕНТОВ УПРАВЛЕНИЯ =====
        # Метка "Размер матрицы"
        ttk.Label(control_frame, text="Размер матрицы:", font=(
            "Arial", 11)).grid(row=0, column=0, padx=5)

        # Spinbox для выбора размера (ограничиваем до 15)
        size_spinbox = ttk.Spinbox(
            control_frame, from_=2, to=15, textvariable=size_var, width=5)
        size_spinbox.grid(row=0, column=1, padx=5)

        # Кнопки управления
        ttk.Button(control_frame, text="Создать",
                   command=build_matrix).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Случайно",
                   command=random_fill).grid(row=0, column=3, padx=5)
        ttk.Button(control_frame, text="Очистить",
                   command=clear_matrix).grid(row=0, column=4, padx=5)
        ttk.Button(control_frame, text="Готово", command=submit_matrix).grid(
            row=0, column=5, padx=5)

        # ===== ИНФОРМАЦИОННАЯ ПАНЕЛЬ =====
        info_frame = ttk.Frame(top_frame)
        info_frame.pack(fill=tk.X, pady=10)

        info_text = """
        Инструкция:
        • Диагональные элементы (i = j) всегда равны 0
        • Введите целые положительные числа для остальных элементов
        • Значения автоматически копируются для симметричности
        • Максимальный размер матрицы: 15
        • Используйте кнопки для управления
        """
        ttk.Label(info_frame, text=info_text, foreground="gray").pack()

        # ===== РАЗМЕЩЕНИЕ CANVAS С ПРОКРУТКОЙ =====
        canvas.pack(side="left", fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")

        # Создаем начальную матрицу
        build_matrix()

        # ===== ЦЕНТРИРОВАНИЕ ОКНА =====
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

        # Запускаем главный цикл обработки событий
        root.mainloop()

        return matrix

    def gui_input_mode(initial_size: int = 4) -> List[List[int]]:
        """
        Запуск GUI ввода матрицы с обработкой возможных ошибок.
        
        Parameters
        ----------
        initial_size : int
            Начальный размер матрицы
            
        Returns
        -------
        List[List[int]] or None
            Введенная матрица или None при отмене/ошибке
        """
        try:
            matrix = gui_matrix_input(initial_size)
            if matrix:
                return matrix
            else:
                console.print(
                    "[yellow]Ввод матрицы отменен, возврат в меню[/yellow]")
                return None
        except Exception as e:
            console.print(f"[red]Ошибка при работе GUI: {e}[/red]")
            return None
else:
    # Заглушка для GUI, когда Tkinter недоступен
    def gui_input_mode(initial_size: int = 4) -> List[List[int]]:
        """Заглушка для GUI ввода."""
        console.print(
            "[yellow]GUI режим недоступен: не установлен Tkinter[/yellow]")
        return None

# =========================================================
# HELP / СПРАВКА
# =========================================================


def show_help() -> None:
    """
    Отображение справочной информации о программе.
    """
    console.print("\n[bold cyan]========== СПРАВКА ==========[/bold cyan]\n")

    # Основная информация о задаче
    help_text = """
[bold yellow]О программе:[/bold yellow]
Программа решает задачу коммивояжёра (TSP) с фиксированными начальным и конечным городами.
Алгоритм находит минимальный по стоимости маршрут, проходящий через все города ровно один раз.

[bold yellow]Математическая постановка:[/bold yellow]
Дан полный ориентированный граф G = (V, E) с множеством вершин V = {1, 2, ..., n}
и весовой функцией w: E → ℝ (веса могут быть отрицательными).
Требуется найти гамильтонов путь минимального веса, начинающийся в заданной вершине start
и заканчивающийся в заданной вершине end.

[bold yellow]Алгоритм решения:[/bold yellow]
• Метод: динамическое программирование на битовых масках
• Сложность: O(n²·2ⁿ)
• Память: O(n·2ⁿ)

Состояние динамического программирования:
    dp[mask][v] — минимальная стоимость пути, который начинается в start,
                  проходит через все города из множества mask и заканчивается в v.
    mask — битовая маска посещенных городов (бит i = 1, если город i посещен)

[bold yellow]Форматы ввода данных:[/bold yellow]
"""
    console.print(help_text)

    # Таблица с режимами ввода
    table = Table(title="Режимы ввода матрицы", box=box.ROUNDED)
    table.add_column("Режим", style="cyan", justify="center")
    table.add_column("Описание", style="green")
    table.add_column("Особенности", style="yellow")

    table.add_row("1 - Консоль",
                  "Ручной ввод матрицы в терминале",
                  "Можно вводить 'x' для отсутствия пути")
    table.add_row("2 - Случайный",
                  "Генерация случайного графа",
                  "Веса от 1 до 50, 10% вероятность отсутствия пути")

    if GUI_AVAILABLE:
        table.add_row("3 - GUI",
                      "Ввод через графический интерфейс",
                      "Авто-копирование симметричных элементов, изменение размера")
    else:
        table.add_row("3 - GUI",
                      "[red]НЕДОСТУПЕН[/red]",
                      "Установите Tkinter")

    console.print(table)

    # Информация о визуализации
    viz_text = f"""
[bold yellow]Визуализация:[/bold yellow]
{'✅ Доступна' if VISUALIZATION_AVAILABLE else '❌ Недоступна'}
"""
    if VISUALIZATION_AVAILABLE:
        viz_text += """
При включении визуализации:
• Граф отображается с помощью networkx и matplotlib
• Каждый шаг маршрута показывается с задержкой 2 секунды
• Цветовая схема:
  - 🟢 Зеленый: начальный город
  - 🔴 Коралловый: конечный город
  - 🔵 Голубой: промежуточные города
  - 🔴 Красный: текущий шаг маршрута
  - ⚪ Серый: остальные города
• В конце показывается таблица с деталями маршрута
"""
    else:
        viz_text += "\nДля визуализации установите: pip install networkx matplotlib\n"

    console.print(Panel(viz_text, title="Визуализация", border_style="green"))

    # Информация о формате данных
    format_text = """
[bold yellow]Формат матрицы расстояний:[/bold yellow]
• Размерность: n × n, где n — количество городов
• Элемент [i][j] — стоимость перехода из города i в город j
• Диагональные элементы всегда равны 0
• Значение 0 при i ≠ j интерпретируется как ОТСУТСТВИЕ ПУТИ
• Для отсутствия пути также можно использовать символ 'x'
• Допускаются отрицательные веса

Пример матрицы для 4 городов:
    1   2   3   4
1   0   5   3   x
2   5   0   2   4
3   3   2   0   1
4   x   4   1   0

[bold yellow]Ограничения:[/bold yellow]
• Количество городов: от 2 до 15 (из-за сложности алгоритма O(n²·2ⁿ))
• При n > 15 время выполнения может быть очень большим
"""
    console.print(
        Panel(format_text, title="Формат данных", border_style="blue"))

    # Информация о тестировании
    test_text = """
[bold yellow]Режимы тестирования:[/bold yellow]
• [cyan]Тесты[/cyan] - запуск модульных тестов из файла tests.py
• [cyan]Стресс-тест[/cyan] - проверка на большом количестве случайных графов
  (позволяет оценить стабильность и производительность алгоритма)

[bold yellow]Коды возврата:[/bold yellow]
• cost = -1, path = [] — маршрут не существует
• иначе — (стоимость, список городов в порядке посещения)
"""
    console.print(
        Panel(test_text, title="Тестирование", border_style="magenta"))

    # Версия и авторство
    console.print(
        "\n[dim]Версия: 2.0 | Лабораторная работа №2 | Вариант 4[/dim]")
    console.print(
        "[dim]Задача коммивояжёра с фиксированными начальным и конечным городами[/dim]\n")

    # Пауза для просмотра
    input("\n[dim]Нажмите Enter для возврата в меню...[/dim]")

# =========================================================
# ТОЧКА ВХОДА
# =========================================================


if __name__ == "__main__":
    # Выводим информацию о доступных компонентах при запуске
    console.print("[bold]Проверка доступных компонентов:[/bold]")

    if VISUALIZATION_AVAILABLE:
        console.print(
            "  ✅ Визуализация (networkx/matplotlib) - [green]доступна[/green]")
    else:
        console.print(
            "  ❌ Визуализация - [yellow]недоступна[/yellow] (pip install networkx matplotlib)")

    if GUI_AVAILABLE:
        console.print("  ✅ GUI ввод (Tkinter) - [green]доступен[/green]")
    else:
        console.print(
            "  ❌ GUI ввод - [yellow]недоступен[/yellow] (Tkinter обычно встроен в Python)")

    print()

    # Запускаем главное меню
    main_menu()
