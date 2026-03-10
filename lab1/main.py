#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Программа для сегментации текста с использованием префиксного дерева (бора)
и динамического программирования. Решает задачу омонимии - находит разбиение
строки на слова из словаря с максимальной суммой весов.

Режимы работы:
    1 - Обычный ввод (интерактивный)
    2 - Стресс-тест (генерация случайных данных)
    3 - Тестирование (прогон всех тестов)

Вариант 4: Омонимия
"""

import string
import random
import re
import time
import sys
from typing import Optional, Tuple, List, Union, Dict, Any
from pathlib import Path
from io import StringIO
import contextlib

# Библиотеки для красивого вывода
from rich import print
from rich.tree import Tree
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.columns import Columns
from rich import box

# Импорт тестов
try:
    from tests import (
        TestCase, TestType, get_all_tests, get_tests_by_type,
        INTERACTIVE_TEST_SCENARIOS
    )
except ImportError:
    print("[red]Ошибка: файл tests.py не найден или содержит ошибки[/red]")
    print("[yellow]Убедитесь, что tests.py находится в той же директории[/yellow]")
    sys.exit(1)

console = Console()

# =========================
# Генератор стресс-теста
# =========================


def gen_stress_test(n: int = 10**5, m: int = 10**4, max_word_len: int = 20) -> Tuple[str, 'Trie']:
    """
    Генерирует случайные тестовые данные для проверки производительности.

    Функция создает случайную строку заданной длины и заполняет бор
    случайными словами со случайными весами. Используется для стресс-тестирования
    алгоритма на больших объемах данных.

    Parameters
    ----------
    n : int, optional
        Длина генерируемой строки, по умолчанию 10^5
    m : int, optional
        Количество слов в словаре, по умолчанию 10^4
    max_word_len : int, optional
        Максимальная длина генерируемого слова, по умолчанию 20

    Returns
    -------
    Tuple[str, Trie]
        Кортеж из сгенерированной строки и заполненного префиксного дерева

    Raises
    ------
    ValueError
        Если параметры имеют некорректные значения
    MemoryError
        Если недостаточно памяти для генерации данных

    Examples
    --------
    >>> s, trie = gen_stress_test(100, 10)
    >>> len(s)
    100
    >>> trie.word_count
    10

    Notes
    -----
    Веса генерируются случайно в диапазоне от 1 до 100.
    """
    try:
        print("\n[bold blue]Генерация стресс-теста...[/bold blue]")

        # Проверка входных параметров
        if n <= 0 or m <= 0 or max_word_len <= 0:
            raise ValueError("Параметры должны быть положительными числами")
        if n > 10**5:
            raise ValueError("Слишком большая длина строки")
        if m > 10**5:
            raise ValueError("Слишком много слов в словаре")

        # Генерация строки с прогресс-баром
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Генерация строки...", total=n)

            try:
                # Генерация строки случайных строчных букв длиной n
                chars = []
                for i in range(n):
                    chars.append(random.choice(string.ascii_lowercase))
                    if i % 1000 == 0:  # Обновляем прогресс каждые 1000 символов
                        progress.update(task, completed=i)
                s = ''.join(chars)
                progress.update(task, completed=n)
            except MemoryError:
                raise MemoryError("Недостаточно памяти для генерации строки")

        trie = Trie()

        # Заполнение словаря
        print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[yellow]Генерация словаря...", total=m)

            successful_inserts = 0
            for i in range(m):
                try:
                    length: int = random.randint(1, max_word_len)
                    word: str = ''.join(random.choices(
                        string.ascii_lowercase, k=length))
                    weight: float = random.uniform(
                        1, 100)  # случайный вес от 1 до 100
                    trie.insert(word, weight)
                    successful_inserts += 1
                except Exception as e:
                    print(
                        f"\n[yellow]Предупреждение: не удалось вставить слово {i+1}: {e}[/yellow]")
                    continue
                finally:
                    progress.update(task, advance=1)

        print(
            f"\n[green]Сгенерировано:[/green] n={n}, m={successful_inserts}/{m}, L_max={trie.max_len}")
        return s, trie

    except ValueError as e:
        print(f"[red]Ошибка в параметрах: {e}[/red]")
        raise
    except MemoryError as e:
        print(f"[red]Ошибка памяти: {e}[/red]")
        raise
    except Exception as e:
        print(f"[red]Неожиданная ошибка при генерации теста: {e}[/red]")
        raise


# =========================
# Класс узла бора
# =========================

class TrieNode:
    """
    Узел префиксного дерева (бора).

    Класс представляет один узел в префиксном дереве. Каждый узел содержит
    ссылки на дочерние узлы (по одной на каждую букву алфавита) и может
    хранить вес слова, если в этом узле заканчивается какое-либо слово.

    Attributes
    ----------
    children : List[Optional[TrieNode]]
        Массив из 26 элементов (по числу букв a-z), каждый элемент
        ссылается на следующий узел или None
    best_weight : Optional[float]
        Максимальный вес слова, заканчивающегося в этом узле,
        None если слово не заканчивается в этом узле

    Examples
    --------
    >>> node = TrieNode()
    >>> node.best_weight is None
    True
    >>> node.children[0] is None
    True

    Notes
    -----
    Использование __slots__ позволяет экономить память при создании
    большого количества узлов.
    """
    __slots__ = (
        "children", "best_weight")  # оптимизация памяти - фиксированные атрибуты

    def __init__(self) -> None:
        try:
            self.children: List[Optional['TrieNode']] = [None] * 26
            self.best_weight: Optional[float] = None
        except Exception as e:
            print(f"[red]Ошибка при инициализации узла: {e}[/red]")
            raise


# =========================
# Класс бора
# =========================

class Trie:
    """
    Префиксное дерево (бор) для хранения словаря с весами.

    Реализует структуру данных "префиксное дерево" для эффективного хранения
    и поиска слов. Особенностью реализации является хранение для каждого слова
    максимального веса среди возможных дубликатов и отслеживание максимальной
    длины слова для оптимизации поиска.

    Attributes
    ----------
    root : TrieNode
        Корневой узел дерева (не содержит символа)
    max_len : int
        Максимальная длина слова в словаре (для ограничения перебора)
    word_count : int
        Количество уникальных слов в словаре

    Methods
    -------
    insert(word, weight)
        Вставляет слово в бор с указанным весом
    search(word)
        Ищет слово в дереве и возвращает его вес
    visualize()
        Выводит красивое представление дерева в консоль

    Examples
    --------
    >>> trie = Trie()
    >>> trie.insert("hello", 5.0)
    >>> trie.insert("world", 3.0)
    >>> trie.word_count
    2
    >>> trie.max_len
    5
    """

    def __init__(self):
        """
        Инициализирует пустое префиксное дерево.

        Создает корневой узел и обнуляет счетчики.
        """
        try:
            self.root: TrieNode = TrieNode()
            self.max_len: int = 0
            self.word_count: int = 0
        except Exception as e:
            print(f"[red]Ошибка при инициализации дерева: {e}[/red]")
            raise

    def insert(self, word: str, weight: float) -> None:
        """
        Вставляет слово в бор с заданным весом.

        Реализует стандартный алгоритм вставки в префиксное дерево:
        проход по символам слова с созданием новых узлов при необходимости.
        Если слово уже существует, сохраняется максимальный вес.

        Parameters
        ----------
        word : str
            Вставляемое слово (должно содержать только строчные латинские буквы)
        weight : float
            Вес слова

        Raises
        ------
        ValueError
            Если слово содержит недопустимые символы
        TypeError
            Если передан неправильный тип данных

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert("test", 10.0)
        >>> trie.insert("test", 15.0)  # обновит вес до 15.0
        >>> trie.search("test")
        15.0

        Notes
        -----
        Символы преобразуются в индексы по формуле: index = ord(char) - ord('a')
        """
        try:
            # Проверка типов
            if not isinstance(word, str):
                raise TypeError(
                    f"Слово должно быть строкой, получен {type(word)}")
            if not isinstance(weight, (int, float)):
                raise TypeError(
                    f"Вес должен быть числом, получен {type(weight)}")

            # Проверка на допустимые символы
            if not word:
                raise ValueError("Слово не может быть пустым")
            if not word.islower() or not word.isalpha():
                raise ValueError(
                    "Слово должно содержать только строчные латинские буквы")

            node: TrieNode = self.root
            self.max_len = max(self.max_len, len(word))

            for char in word:
                try:
                    idx = ord(char) - ord('a')
                    # Проверка индекса
                    if idx < 0 or idx >= 26:
                        raise ValueError(f"Недопустимый символ: {char}")

                    if node.children[idx] is None:
                        node.children[idx] = TrieNode()
                    node = node.children[idx]
                except IndexError:
                    raise ValueError(
                        f"Ошибка доступа к индексу для символа {char}")
                except Exception as e:
                    raise RuntimeError(
                        f"Ошибка при обработке символа {char}: {e}")

            if node.best_weight is None:
                node.best_weight = weight
                self.word_count += 1
            else:
                node.best_weight = max(node.best_weight, weight)

        except (ValueError, TypeError) as e:
            print(f"[red]Ошибка при вставке слова '{word}': {e}[/red]")
            raise
        except Exception as e:
            print(
                f"[red]Неожиданная ошибка при вставке слова '{word}': {e}[/red]")
            raise

    def search(self, word: str) -> Optional[float]:
        """
        Выполняет поиск слова в дереве.

        Проходит по символам слова, перемещаясь по соответствующим узлам.
        Если слово найдено, возвращает его вес, иначе None.

        Parameters
        ----------
        word : str
            Искомое слово (только строчные латинские буквы)

        Returns
        -------
        Optional[float]
            Вес слова, если оно найдено, иначе None

        Raises
        ------
        ValueError
            Если слово содержит недопустимые символы

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert("hello", 5.0)
        >>> trie.search("hello")
        5.0
        >>> trie.search("world") is None
        True
        """
        try:
            if not isinstance(word, str):
                raise TypeError(
                    f"Слово должно быть строкой, получен {type(word)}")

            if not word.islower() or not word.isalpha():
                raise ValueError(
                    "Слово должно содержать только строчные латинские буквы")

            node = self.root
            for char in word:
                idx = ord(char) - ord('a')
                if node.children[idx] is None:
                    return None
                node = node.children[idx]
            return node.best_weight

        except Exception as e:
            print(f"[red]Ошибка при поиске слова '{word}': {e}[/red]")
            return None

    # Красивый вывод через rich
    def visualize(self) -> None:
        """
        Визуализирует префиксное дерево с помощью библиотеки rich.

        Создает древовидную структуру, где:
            - Желтым цветом выделены символы
            - Красным цветом выделены веса (если слово заканчивается)
            - Зеленым выделен корень дерева

        Returns
        -------
        None

        Examples
        --------
        >>> trie = Trie()
        >>> trie.insert("cat", 3.0)
        >>> trie.insert("car", 5.0)
        >>> trie.visualize()  # выведет красивое дерево
        """
        try:
            tree = Tree("[bold green]🌳 Префиксное дерево[/bold green]")

            def add_nodes(rich_node: Tree, trie_node: TrieNode) -> None:
                try:
                    for idx in range(26):
                        child = trie_node.children[idx]
                        if child:
                            char: str = chr(ord('a') + idx)
                            label: str = f"[yellow]{char}[/yellow]"
                            if child.best_weight is not None:
                                label += f" [red](вес={child.best_weight:.2f})[/red]"
                            branch: Tree = rich_node.add(label)
                            add_nodes(branch, child)
                except Exception as e:
                    print(f"[red]Ошибка при визуализации узла: {e}[/red]")
                    raise

            add_nodes(tree, self.root)
            console.print(tree)

        except Exception as e:
            print(f"[red]Ошибка при визуализации дерева: {e}[/red]")


# =========================
# Безопасный ввод
# =========================

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

    Examples
    --------
    >>> name = safe_input("Введите имя: ")
    >>> # если пользователь введет "  John  ", получим "John"

    Notes
    -----
    При возникновении ошибок программа завершается с кодом 1.
    """
    try:
        return input(prompt).strip()
    except EOFError:
        print("[red]Обнаружен конец файла. Завершение программы...[/red]")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[yellow]Программа прервана пользователем[/yellow]")
        sys.exit(0)
    except Exception as e:
        print(f"[red]Ошибка ввода: {e}[/red]")
        return ""


# =========================
# Ввод строки S (исправленная версия)
# =========================

def read_string(interactive: bool = True) -> str:
    """
    Выполняет ввод и валидацию строки S.

    Функция запрашивает у пользователя строку и проверяет её соответствие
    требованиям:
        - Не пустая
        - Длина не более 10^5 символов
        - Содержит только строчные латинские буквы

    Parameters
    ----------
    interactive : bool
        Если True, выводит приглашения для ввода.
        Если False, читает из стандартного ввода без приглашений (для тестов).

    Returns
    -------
    str
        Корректная строка, введенная пользователем

    Raises
    ------
    RuntimeError
        При превышении количества попыток ввода
    KeyboardInterrupt
        При прерывании пользователем

    Examples
    --------
    >>> s = read_string(interactive=False)  # в тестовом режиме
    >>> s
    'helloworld'
    """
    max_attempts = 10
    attempts = 0

    while attempts < max_attempts:
        try:
            if interactive:
                s: str = safe_input("Введите строку S (≤ 10^5, только a-z): ")
            else:
                s: str = input().strip()

            if not s:
                if interactive:
                    print("[red]Строка не может быть пустой[/red]")
                attempts += 1
                continue

            if len(s) > 10**5:
                if interactive:
                    print("[red]Ошибка: длина строки превышает 10^5[/red]")
                attempts += 1
                continue

            if not re.match(r'^[a-z]+$', s):
                if interactive:
                    print("[red]Допустимы только строчные латинские буквы[/red]")
                attempts += 1
                continue

            return s

        except KeyboardInterrupt:
            if interactive:
                print("\n[yellow]Ввод прерван пользователем[/yellow]")
            raise
        except Exception as e:
            if interactive:
                print(f"[red]Неожиданная ошибка при вводе: {e}[/red]")
            attempts += 1

    raise RuntimeError(f"Превышено количество попыток ввода ({max_attempts})")


# =========================
# Ввод словаря (исправленная версия)
# =========================

def read_dictionary(trie: Trie, interactive: bool = True) -> None:
    """
    Выполняет ввод словаря и заполняет префиксное дерево.

    Функция запрашивает у пользователя количество записей в словаре,
    затем для каждой записи проверяет формат "слово вес" и вставляет
    слово в бор.

    Parameters
    ----------
    trie : Trie
        Объект префиксного дерева для заполнения
    interactive : bool
        Если True, выводит приглашения для ввода.
        Если False, читает из стандартного ввода без приглашений (для тестов).

    Raises
    ------
    RuntimeError
        При превышении количества попыток ввода
    KeyboardInterrupt
        При прерывании пользователем

    Examples
    --------
    >>> trie = Trie()
    >>> read_dictionary(trie, interactive=False)  # в тестовом режиме
    """
    max_attempts = 10
    attempts = 0

    try:
        while attempts < max_attempts:
            try:
                if interactive:
                    size: str = safe_input(
                        "Введите количество записей (≤ 10^4): ")
                else:
                    size: str = input().strip()

                if not size:
                    if interactive:
                        print("[red]Введите значение[/red]")
                    attempts += 1
                    continue

                if not size.isdigit():
                    if interactive:
                        print("[red]Введите натуральное число[/red]")
                    attempts += 1
                    continue

                m = int(size)

                if m <= 0:
                    if interactive:
                        print("[red]Количество должно быть положительным[/red]")
                    attempts += 1
                    continue

                if m > 10**4:
                    if interactive:
                        print("[red]Количество не может превышать 10^4[/red]")
                    attempts += 1
                    continue

                break

            except ValueError:
                if interactive:
                    print("[red]Ошибка преобразования числа[/red]")
                attempts += 1
            except KeyboardInterrupt:
                raise
            except Exception as e:
                if interactive:
                    print(f"[red]Ошибка: {e}[/red]")
                attempts += 1

        if attempts >= max_attempts:
            raise RuntimeError(
                "Превышено количество попыток ввода количества записей")

        if interactive:
            print("Введите записи в формате: слово вес")

        successful_inserts = 0

        # Прогресс-бар для вставки слов
        if interactive and m > 10:  # Показываем прогресс-бар только если записей много
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task(
                    "[yellow]Вставка слов в словарь...", total=m)

                for i in range(m):
                    entry_attempts = 0
                    while entry_attempts < max_attempts:
                        try:
                            if interactive:
                                line: str = safe_input(f"Запись {i+1}: ")
                            else:
                                line: str = input().strip()

                            if not line:
                                if interactive:
                                    print(
                                        "[red]Строка не может быть пустой[/red]")
                                entry_attempts += 1
                                continue

                            parts = line.split()

                            if len(parts) != 2:
                                if interactive:
                                    print("[red]Формат: слово вес[/red]")
                                entry_attempts += 1
                                continue

                            word, weight_str = parts

                            if not word.isalpha() or not word.islower():
                                if interactive:
                                    print(
                                        "[red]Только строчные латинские буквы[/red]")
                                entry_attempts += 1
                                continue

                            try:
                                weight: float = float(weight_str)
                            except ValueError:
                                if interactive:
                                    print("[red]Вес должен быть числом[/red]")
                                entry_attempts += 1
                                continue

                            trie.insert(word, weight)
                            successful_inserts += 1
                            progress.update(task, advance=1)
                            break

                        except KeyboardInterrupt:
                            raise
                        except Exception as e:
                            if interactive:
                                print(
                                    f"[red]Ошибка при обработке записи: {e}[/red]")
                            entry_attempts += 1

                    if entry_attempts >= max_attempts:
                        if interactive:
                            print(
                                f"[yellow]Пропуск записи {i+1} после {max_attempts} попыток[/yellow]")
                        progress.update(task, advance=1)
        else:
            # Обычный ввод без прогресс-бара для небольшого количества записей
            for i in range(m):
                entry_attempts = 0
                while entry_attempts < max_attempts:
                    try:
                        if interactive:
                            line: str = safe_input(f"Запись {i+1}: ")
                        else:
                            line: str = input().strip()

                        if not line:
                            if interactive:
                                print("[red]Строка не может быть пустой[/red]")
                            entry_attempts += 1
                            continue

                        parts = line.split()

                        if len(parts) != 2:
                            if interactive:
                                print("[red]Формат: слово вес[/red]")
                            entry_attempts += 1
                            continue

                        word, weight_str = parts

                        if not word.isalpha() or not word.islower():
                            if interactive:
                                print(
                                    "[red]Только строчные латинские буквы[/red]")
                            entry_attempts += 1
                            continue

                        try:
                            weight: float = float(weight_str)
                        except ValueError:
                            if interactive:
                                print("[red]Вес должен быть числом[/red]")
                            entry_attempts += 1
                            continue

                        trie.insert(word, weight)
                        successful_inserts += 1
                        break

                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        if interactive:
                            print(
                                f"[red]Ошибка при обработке записи: {e}[/red]")
                        entry_attempts += 1

                if entry_attempts >= max_attempts:
                    if interactive:
                        print(
                            f"[yellow]Пропуск записи {i+1} после {max_attempts} попыток[/yellow]")

        if interactive:
            print(
                f"[green]Успешно вставлено {successful_inserts} из {m} записей[/green]")

    except KeyboardInterrupt:
        if interactive:
            print("\n[yellow]Ввод словаря прерван пользователем[/yellow]")
        raise
    except Exception as e:
        if interactive:
            print(f"[red]Ошибка при вводе словаря: {e}[/red]")
        raise


# =========================
# ДП алгоритм O(n * Lmax)
# =========================

def segment_text(s: str, trie: Trie) -> Union[Tuple[None, None], Tuple[float, List[str]]]:
    """
    Выполняет сегментацию текста с использованием динамического программирования.

    Основной алгоритм решения задачи. Использует подход динамического
    программирования для нахождения оптимального разбиения строки на слова
    из словаря с максимальной суммой весов.

    Алгоритм:
        1. dp[i] - максимальная сумма весов для разбиения первых i символов
        2. prev[i] - индекс начала последнего слова в оптимальном разбиении
        3. chosen_weight[i] - вес последнего слова

    Для каждой позиции i (где есть корректное разбиение):
        - Проходим по строке до i + max_len (ограничение для оптимизации)
        - Для каждого возможного слова проверяем его наличие в боре
        - Обновляем dp[j+1] если нашли слово с весом

    Parameters
    ----------
    s : str
        Исходная строка для сегментации (только a-z)
    trie : Trie
        Заполненное префиксное дерево со словарем

    Returns
    -------
    Union[Tuple[None, None], Tuple[float, List[str]]]
        Если разбиение возможно:
            - Максимальная сумма весов
            - Список слов с весами в формате "слово(вес)"
        Если разбиение невозможно:
            - None, None

    Raises
    ------
    ValueError
        При некорректных входных данных
    MemoryError
        При недостатке памяти для массивов ДП

    Examples
    --------
    >>> trie = Trie()
    >>> trie.insert("hello", 5)
    >>> trie.insert("world", 3)
    >>> total, parts = segment_text("helloworld", trie)
    >>> total
    8.0
    >>> parts
    ['hello(5.00)', 'world(3.00)']

    Notes
    -----
    Сложность алгоритма: O(n * L_max), где:
        n - длина строки
        L_max - максимальная длина слова в словаре
    """
    try:
        if not isinstance(s, str):
            raise TypeError(f"Строка должна быть строкой, получен {type(s)}")
        if not isinstance(trie, Trie):
            raise TypeError(
                f"trie должен быть объектом Trie, получен {type(trie)}")

        n: int = len(s)
        if n == 0:
            raise ValueError("Строка не может быть пустой")

        # Инициализация массивов ДП
        try:
            dp: List[float] = [-float('inf')] * (n + 1)
            prev: List[int] = [-1] * (n + 1)
            chosen_weight: List[float] = [0.0] * (n + 1)
        except MemoryError:
            raise MemoryError("Недостаточно памяти для массивов ДП")

        dp[0] = 0

        # Основной цикл ДП
        for i in range(n):
            if dp[i] == -float('inf'):
                continue

            node = trie.root

            for j in range(i, min(n, i + trie.max_len)):
                try:
                    idx: int = ord(s[j]) - ord('a')

                    if idx < 0 or idx >= 26:
                        raise ValueError(
                            f"Недопустимый символ в позиции {j}: {s[j]}")

                    node = node.children[idx]
                    if node is None:
                        break

                    if node.best_weight is not None:
                        new_value: float = dp[i] + node.best_weight
                        if new_value > dp[j + 1]:
                            dp[j + 1] = new_value
                            prev[j + 1] = i
                            chosen_weight[j + 1] = node.best_weight

                except AttributeError:
                    raise RuntimeError("Ошибка структуры дерева")
                except IndexError:
                    raise RuntimeError(
                        f"Ошибка индекса при обработке позиции {j}")

        if dp[n] == -float('inf'):
            return None, None

        # Восстановление разбиения
        try:
            result: List[str] = []
            idx: int = n
            while idx > 0:
                start: int = prev[idx]
                if start < 0 or start >= idx:
                    raise RuntimeError("Ошибка восстановления пути")

                result.append(f"{s[start:idx]}({chosen_weight[idx]:.2f})")
                idx = start

            result.reverse()
            return dp[n], result

        except Exception as e:
            raise RuntimeError(f"Ошибка при восстановлении разбиения: {e}")

    except (ValueError, TypeError, MemoryError, RuntimeError) as e:
        print(f"[red]Ошибка в алгоритме сегментации: {e}[/red]")
        return None, None
    except Exception as e:
        print(f"[red]Неожиданная ошибка в алгоритме сегментации: {e}[/red]")
        return None, None

# =========================
# Тестирование (исправленная версия)
# =========================


class TestRunner:
    """
    Класс для запуска тестов и сбора результатов.

    Предоставляет функциональность для автоматического тестирования программы:
        - Запуск одиночных тестов
        - Запуск всех тестов с прогресс-баром
        - Вывод детальных результатов
        - Сводка статистики
        - Запуск интерактивных сценариев

    Attributes
    ----------
    results : Dict[str, Dict[str, Any]]
        Словарь с результатами тестов, где ключ - имя теста
    total_tests : int
        Общее количество запущенных тестов
    passed_tests : int
        Количество пройденных тестов
    failed_tests : int
        Количество проваленных тестов
    negative_passed : int
        Количество пройденных негативных тестов
    negative_total : int
        Общее количество негативных тестов
    """

    def __init__(self):
        """
        Инициализирует TestRunner с пустыми счетчиками и результатами.
        """
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.negative_passed = 0
        self.negative_total = 0

    def run_single_test(self, test: TestCase) -> Dict[str, Any]:
        """
        Запускает один тест и возвращает результат с реальным выводом программы.

        Функция подменяет стандартный ввод и вывод, чтобы симулировать
        пользовательский ввод и захватить вывод программы.

        Parameters
        ----------
        test : TestCase
            Объект тестового случая для запуска

        Returns
        -------
        Dict[str, Any]
            Словарь с результатами теста, содержащий:
            - name: название теста
            - description: описание
            - type: тип теста
            - status: статус ("passed" или "failed")
            - error: сообщение об ошибке (если есть)
            - expected: ожидаемый результат
            - got: фактический результат
            - time: время выполнения
            - segmentation: полученное разбиение
            - output: захваченный вывод программы
            - input_sequence: последовательность ввода
        """
        result = {
            "name": test.name,
            "description": test.description,
            "type": test.type.value,
            "status": "running",
            "error": None,
            "expected": test.expected_total,
            "got": None,
            "time": 0,
            "segmentation": None,
            "output": "",
            "input_sequence": []
        }

        # Формируем последовательность ввода
        inputs = [
            "1",  # Режим 1
            test.s,  # Строка S
            str(len(test.dictionary)),  # Количество записей
        ]

        # Записи словаря
        for word, weight in test.dictionary:
            inputs.append(f"{word} {weight}")

        # Не показывать бор
        inputs.append("н")

        result["input_sequence"] = inputs.copy()

        # Перехватываем вывод
        captured_output = StringIO()

        # Сохраняем оригинальные stdin и stdout
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_input = __builtins__.input if hasattr(
            __builtins__, 'input') else input

        try:
            start_time = time.time()

            # Создаем итератор для ввода
            input_iterator = iter(inputs.copy())

            def mock_input(prompt=""):
                try:
                    return next(input_iterator)
                except StopIteration:
                    return ""

            # Подменяем input и перенаправляем вывод
            sys.stdin = StringIO("\n".join(inputs) + "\n")
            sys.stdout = captured_output
            __builtins__.input = mock_input

            try:
                # Запускаем программу в режиме 1
                trie = Trie()
                s = read_string(interactive=False)
                read_dictionary(trie, interactive=False)

                # Запускаем алгоритм
                total, segmentation = segment_text(s, trie)

                # Выводим результат
                if total is None:
                    print("-1")
                else:
                    print(f"{total:.2f}")
                    if segmentation:
                        print(" + ".join(segmentation))

                result["got"] = total
                result["segmentation"] = segmentation

            except Exception as e:
                result["error"] = str(e)
                result["got"] = None
                print(f"Ошибка: {e}")

            finally:
                # Восстанавливаем всё обратно
                sys.stdin = original_stdin
                sys.stdout = original_stdout
                if hasattr(__builtins__, 'input'):
                    __builtins__.input = original_input

            end_time = time.time()
            result["time"] = end_time - start_time
            result["output"] = captured_output.getvalue()

            # Определяем результат теста
            if test.type == TestType.NEGATIVE:
                self.negative_total += 1

                # Для негативных тестов проверяем наличие сообщений об ошибках
                output_lower = result["output"].lower()
                error_keywords = [
                    "ошибк", "error", "недопустим", "только",
                    "must be", "invalid", "cannot", "пуст",
                    "превышено", "должно быть"
                ]

                if any(keyword in output_lower for keyword in error_keywords):
                    result["status"] = "passed"
                    self.negative_passed += 1
                    self.passed_tests += 1
                else:
                    result["status"] = "failed"
                    result["error"] = "Негативный тест: программа должна была вывести сообщение об ошибке"
                    self.failed_tests += 1

            else:
                # Для позитивных и граничных тестов
                if test.expected_total is None:
                    if result["got"] is None:
                        result["status"] = "passed"
                        self.passed_tests += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = f"Ожидалось None, получено {result['got']}"
                        self.failed_tests += 1
                else:
                    if result["got"] is not None:
                        if abs(result["got"] - test.expected_total) < 1e-10:
                            if test.expected_segmentation and result["segmentation"]:
                                if sorted(result["segmentation"]) == sorted(test.expected_segmentation):
                                    result["status"] = "passed"
                                    self.passed_tests += 1
                                else:
                                    result["status"] = "failed"
                                    result["error"] = f"Неверное разбиение: {result['segmentation']}"
                                    self.failed_tests += 1
                            else:
                                result["status"] = "passed"
                                self.passed_tests += 1
                        else:
                            result["status"] = "failed"
                            result["error"] = f"Ожидалось {test.expected_total}, получено {result['got']}"
                            self.failed_tests += 1
                    else:
                        result["status"] = "failed"
                        result["error"] = f"Ожидалось {test.expected_total}, получено None"
                        self.failed_tests += 1

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["output"] = captured_output.getvalue()
            self.failed_tests += 1

            # Обязательно восстанавливаем stdout даже при ошибке
            sys.stdout = original_stdout
            sys.stdin = original_stdin

        return result

    def run_all_tests(self, tests: List[TestCase]) -> None:
        """
        Запускает все тесты и собирает статистику.

        Отображает прогресс-бар во время выполнения тестов.

        Parameters
        ----------
        tests : List[TestCase]
            Список тестовых случаев для запуска

        Returns
        -------
        None
        """
        self.total_tests = len(tests)
        self.passed_tests = 0
        self.failed_tests = 0
        self.negative_passed = 0
        self.negative_total = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                "[cyan]Запуск тестов...", total=len(tests))

            for test in tests:
                progress.update(task, description=f"[cyan]Тест: {test.name}")
                result = self.run_single_test(test)
                self.results[test.name] = result
                progress.advance(task)

    def print_detailed_results(self) -> None:
        """
        Выводит детальные результаты тестирования с реальным выводом программы.

        Для каждого теста отображается:
            - Название и описание
            - Реальный вывод программы
            - Ожидаемый результат
            - Фактический результат
            - Время выполнения
            - Ошибка (если тест провален)

        Returns
        -------
        None
        """
        console.print(
            "\n[bold cyan]📊 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ[/bold cyan]\n")

        for test_type in TestType:
            type_tests = [r for r in self.results.values() if r["type"]
                          == test_type.value]
            if not type_tests:
                continue

            # Заголовок для типа тестов
            type_colors = {
                TestType.POSITIVE: ("✅ ПОЗИТИВНЫЕ ТЕСТЫ", "green"),
                TestType.NEGATIVE: ("⚠️  НЕГАТИВНЫЕ ТЕСТЫ", "yellow"),
                TestType.EDGE: ("🔷 ГРАНИЧНЫЕ ТЕСТЫ", "blue"),
                TestType.PERFORMANCE: ("⚡ ТЕСТЫ ПРОИЗВОДИТЕЛЬНОСТИ", "magenta")
            }

            title, color = type_colors.get(test_type, ("ТЕСТЫ", "white"))
            console.print(
                f"[bold {color}]{title} ({len(type_tests)})[/bold {color}]")
            console.print("─" * 80)

            for result in type_tests:
                if result["status"] != "failed":
                    continue
                status_icon = "✅" if result["status"] == "passed" else "❌"
                status_color = "green" if result["status"] == "passed" else "red"

                panel_content = [
                    f"[bold]{result['name']}[/bold]",
                    f"[dim]{result.get('description', '')}[/dim]",
                    "",
                    "[bold cyan]📤 РЕАЛЬНЫЙ ВЫВОД ПРОГРАММЫ:[/bold cyan]"
                ]

                # Форматируем вывод
                output_lines = result["output"].strip().split('\n')
                formatted_output = []
                for line in output_lines[:15]:
                    clean_line = re.sub(r'\[.*?\]', '', line)
                    if clean_line.strip():
                        formatted_output.append(f"  {clean_line}")

                if len(output_lines) > 15:
                    formatted_output.append(
                        f"  [dim]... и еще {len(output_lines) - 15} строк[/dim]")

                if formatted_output:
                    panel_content.extend(formatted_output)
                else:
                    panel_content.append("  [dim]<пустой вывод>[/dim]")

                panel_content.extend(["", "[bold]Ожидалось:[/bold]"])

                if test_type == TestType.NEGATIVE:
                    panel_content.append(
                        "  Программа должна вывести сообщение об ошибке")
                else:
                    panel_content.append(f"  Сумма: {result['expected']}")
                    if result.get('segmentation'):
                        panel_content.append(
                            f"  Разбиение: {' + '.join(result['segmentation'])}")

                panel_content.extend([
                    "",
                    "[bold]Получено:[/bold]"
                ])

                if result['got'] is None:
                    panel_content.append("  Разбиение невозможно")
                else:
                    panel_content.append(f"  Сумма: {result['got']:.2f}")
                    if result.get('segmentation'):
                        panel_content.append(
                            f"  Разбиение: {' + '.join(result['segmentation'])}")

                panel_content.extend([
                    "",
                    f"[dim]⏱ Время: {result['time']*1000:.2f} мс[/dim]"
                ])

                if result["status"] == "failed" and result["error"]:
                    panel_content.extend([
                        "",
                        f"[red]❌ Ошибка: {result['error']}[/red]"
                    ])

                panel = Panel(
                    "\n".join(panel_content),
                    title=f"[{status_color}]{status_icon} {result['name']}[/{status_color}]",
                    border_style=status_color,
                    padding=(1, 2),
                    width=100
                )

                console.print(panel)
                console.print()

    def print_summary(self) -> None:
        """
        Выводит сводку по результатам тестирования.

        Отображает таблицу с результатами по типам тестов:
            - Тип тестов
            - Всего
            - Пройдено
            - Провалено
            - Процент успеха

        Также показывает итоговый вердикт.

        Returns
        -------
        None
        """
        console.print("\n[bold cyan]📊 СВОДКА РЕЗУЛЬТАТОВ[/bold cyan]")

        table = Table(show_header=True,
                      header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Тип тестов", style="cyan")
        table.add_column("Всего", justify="right")
        table.add_column("Пройдено", justify="right")
        table.add_column("Провалено", justify="right")
        table.add_column("Процент", justify="right")

        type_names = {
            TestType.POSITIVE: "[green]Позитивные[/green]",
            TestType.NEGATIVE: "[yellow]Негативные[/yellow]",
            TestType.EDGE: "[blue]Граничные[/blue]",
            TestType.PERFORMANCE: "[magenta]Производительность[/magenta]"
        }

        for test_type in TestType:
            type_results = [r for r in self.results.values()
                            if r["type"] == test_type.value]
            if not type_results:
                continue

            total = len(type_results)
            passed = sum(1 for r in type_results if r["status"] == "passed")
            failed = total - passed
            percent = (passed / total * 100) if total > 0 else 0

            table.add_row(
                type_names.get(test_type, test_type.value.capitalize()),
                str(total),
                f"[green]{passed}[/green]",
                f"[red]{failed}[/red]" if failed > 0 else "[dim]0[/dim]",
                f"{percent:.1f}%"
            )

        total_percent = (self.passed_tests / self.total_tests *
                         100) if self.total_tests > 0 else 0
        table.add_row(
            "[bold]ВСЕГО[/bold]",
            str(self.total_tests),
            f"[bold green]{self.passed_tests}[/bold green]",
            f"[bold red]{self.failed_tests}[/bold red]",
            f"[bold]{total_percent:.1f}%[/bold]"
        )

        console.print(table)

        if self.negative_total > 0:
            console.print(
                f"\n[yellow]Негативные тесты: {self.negative_passed}/{self.negative_total} корректно обработаны[/yellow]")

        if self.failed_tests == 0:
            console.print(
                "\n[bold green]✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО![/bold green]")
        else:
            console.print(
                f"\n[bold red]❌ ПРОВАЛЕНО ТЕСТОВ: {self.failed_tests}[/bold red]")

    def run_interactive_scenario(self, scenario: Dict[str, Any]) -> bool:
        """
        Запускает интерактивный сценарий тестирования.

        Симулирует пользовательский ввод для проверки сценариев использования.

        Parameters
        ----------
        scenario : Dict[str, Any]
            Словарь с описанием сценария:
                - name: название сценария
                - inputs: список вводимых строк
                - expected_output_contains: список ожидаемых подстрок в выводе

        Returns
        -------
        bool
            True если сценарий пройден, False в противном случае
        """
        console.print(f"\n[cyan]Запуск сценария: {scenario['name']}[/cyan]")

        inputs = scenario["inputs"]
        expected_outputs = scenario["expected_output_contains"]

        # Сохраняем оригинальные потоки
        original_stdin = sys.stdin
        original_stdout = sys.stdout
        original_input = __builtins__.input if hasattr(
            __builtins__, 'input') else input

        try:
            # Подменяем ввод
            sys.stdin = StringIO("\n".join(inputs) + "\n")

            # Перехватываем вывод
            captured_output = StringIO()
            sys.stdout = captured_output

            # Подменяем input
            input_iterator = iter(inputs.copy())

            def mock_input(prompt=""):
                try:
                    return next(input_iterator)
                except StopIteration:
                    return ""

            if hasattr(__builtins__, 'input'):
                __builtins__.input = mock_input

            try:
                main()
            except SystemExit:
                pass
            except Exception as e:
                console.print(f"[red]Ошибка в сценарии: {e}[/red]")
                return False

            output = captured_output.getvalue()

            # Проверяем наличие ожидаемых строк
            for expected in expected_outputs:
                if expected not in output:
                    console.print(
                        f"[red]❌ Сценарий '{scenario['name']}' провален: не найдено '{expected}'[/red]")
                    return False

            console.print(
                f"[green]✅ Сценарий '{scenario['name']}' пройден[/green]")
            return True

        finally:
            # Восстанавливаем всё
            sys.stdin = original_stdin
            sys.stdout = original_stdout
            if hasattr(__builtins__, 'input'):
                __builtins__.input = original_input

    def run_interactive_scenarios(self) -> None:
        """
        Запускает все интерактивные сценарии.

        Последовательно выполняет все сценарии из INTERACTIVE_TEST_SCENARIOS
        и выводит статистику прохождения.

        Returns
        -------
        None
        """
        console.print(
            "\n[bold cyan]🎭 Запуск интерактивных сценариев[/bold cyan]")

        passed = 0
        total = len(INTERACTIVE_TEST_SCENARIOS)

        for scenario in INTERACTIVE_TEST_SCENARIOS:
            if self.run_interactive_scenario(scenario):
                passed += 1

        console.print(
            f"\n[cyan]Интерактивные сценарии: {passed}/{total} пройдено[/cyan]")

# =========================
# Справка / помощь
# =========================


def show_help() -> None:
    """
    Отображает подробную справку по программе.

    Выводит информацию о:
        - Описании задачи
        - Режимах работы
        - Форматах ввода
        - Командах
        - Тестировании

    Returns
    -------
    None
    """
    try:
        help_text = """
[bold cyan]Программа сегментации текста (Омонимия)[/bold cyan]

[bold yellow]Описание задачи:[/bold yellow]
Дана строка S и словарь слов с весами. Требуется разбить строку на слова
из словаря так, чтобы сумма весов была максимальной.

[bold yellow]Режимы работы:[/bold yellow]
• [green]1[/green] - Обычный ввод (интерактивный режим)
• [green]2[/green] - Стресс-тест (генерация случайных данных)
• [green]3[/green] - Тестирование (прогон всех тестов)

[bold yellow]Форматы ввода:[/bold yellow]
• Строка S: только строчные латинские буквы (a-z), длина ≤ 10^5
• Словарь: 
  - Сначала количество записей m (≤ 10^4)
  - Затем m строк в формате: [слово] [вес]

[bold yellow]Команды:[/bold yellow]
• /help - показать эту справку
• Ctrl+C - прерывание программы

[bold yellow]Тестирование:[/bold yellow]
В режиме 3 программа автоматически прогоняет:
• Позитивные тесты (корректные данные)
• Негативные тесты (должны вызывать ошибки)
• Граничные тесты (предельные случаи)
• Тесты производительности
• Интерактивные сценарии
        """

        panel = Panel(help_text, title="[bold cyan]Справка[/bold cyan]",
                      border_style="cyan", padding=(1, 2))
        console.print(panel)

        table = Table(title="Примеры форматов ввода",
                      show_header=True, header_style="bold magenta")
        table.add_column("Тип", style="cyan")
        table.add_column("Пример", style="green")
        table.add_column("Пояснение", style="white")

        table.add_row("Строка S", "helloworld",
                      "Только буквы a-z, без пробелов")
        table.add_row("Количество", "3", "Натуральное число ≤ 10^4")
        table.add_row("Запись словаря", "hello 5.5",
                      "Слово и вес через пробел")

        console.print(table)

    except Exception as e:
        print(f"[red]Ошибка при отображении справки: {e}[/red]")


# =========================
# Главная функция
# =========================

def main() -> None:
    """
    Главная функция программы.

    Реализует основной цикл работы:
        1. Выбор режима (обычный/стресс-тест/тестирование/помощь)
        2. Ввод или генерация данных
        3. Опциональный показ дерева
        4. Запуск алгоритма
        5. Вывод результатов

    Returns
    -------
    None

    Examples
    --------
    >>> if __name__ == "__main__":
    ...     main()  # запуск программы
    """
    try:
        console = Console()
        print("\n[bold cyan]╔════════════════════════════════════╗[/bold cyan]")
        print("[bold cyan]║    Сегментация текста (Омонимия)   ║[/bold cyan]")
        print("[bold cyan]╚════════════════════════════════════╝[/bold cyan]\n")

        while True:
            try:
                mode: str = safe_input(
                    "Выберите режим:\n"
                    "  [1] Обычный ввод\n"
                    "  [2] Стресс-тест\n"
                    "  [3] Тестирование\n"
                    "  [/help] Справка\n"
                    "→ "
                )

            except KeyboardInterrupt:
                print("\n[yellow]Программа завершена[/yellow]")
                return

            if mode not in ["1", "2", "3", "/help"]:
                print("[red]Введите 1, 2, 3 или /help[/red]")
                continue

            elif mode == "/help":
                show_help()
                continue

            elif mode == "3":
                # Режим тестирования
                console.print(
                    "[bold yellow]🧪 Запуск тестирования...[/bold yellow]")

                runner = TestRunner()

                # Получаем все тесты
                tests = get_all_tests()

                console.print(f"[cyan]Найдено тестов: {len(tests)}[/cyan]")
                console.print(
                    f"[cyan]Интерактивных сценариев: {len(INTERACTIVE_TEST_SCENARIOS)}[/cyan]")

                # Запускаем автоматические тесты
                runner.run_all_tests(tests)
                runner.print_detailed_results()
                runner.print_summary()

                # Запускаем интерактивные сценарии
                console.print(
                    "\n[bold yellow]🎭 Тестирование интерактивных сценариев[/bold yellow]")
                console.print("[dim]Это может занять некоторое время...[/dim]")
                runner.run_interactive_scenarios()

            elif mode == "2":
                # Режим стресс-теста
                try:
                    s, trie = gen_stress_test()

                    show = safe_input("Показать статистику? (д/н): ").lower()
                    if show in ['д', 'да', 'y', 'yes']:
                        console.print(f"\n[cyan]Статистика:[/cyan]")
                        console.print(f"  Длина строки: {len(s)}")
                        console.print(f"  Слов в словаре: {trie.word_count}")
                        console.print(f"  Макс. длина слова: {trie.max_len}")

                    print("\n[bold]Запуск алгоритма...[/bold]")
                    start = time.time()
                    total, seg = segment_text(s, trie)
                    elapsed = time.time() - start

                    if total is None:
                        print("[red]Разбиение невозможно[/red]")
                    else:
                        print(f"[green]Максимальная сумма: {total:.2f}[/green]")
                        if len(seg) <= 10:
                            print("Разбиение:", " + ".join(seg))
                        else:
                            print(f"Разбиение содержит {len(seg)} слов")

                    print(f"⏱ Время: {elapsed:.3f} сек")

                except Exception as e:
                    print(f"[red]Ошибка: {e}[/red]")

            else:
                # Обычный режим
                try:
                    trie = Trie()
                    s = read_string(interactive=True)
                    console.print("[green]✓ Строка принята[/green]\n")
                    read_dictionary(trie, interactive=True)
                    console.print(f"[green]✓ Словарь загружен[/green]\n")

                    show = safe_input("Показать бор? (д/н): ").lower()
                    if show in ['д', 'да', 'y', 'yes']:
                        trie.visualize()

                    print("\n[bold]Запуск алгоритма...[/bold]")
                    console.print(
                        "[bold]🚀 Запуск алгоритма динамического программирования...[/bold]")

                    # Прогресс-бар для алгоритма (для длинных строк)
                    if len(s) > 10000:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            BarColumn(),
                            TextColumn(
                                "[progress.percentage]{task.percentage:>3.0f}%"),
                            TimeElapsedColumn(),
                            console=console
                        ) as progress:
                            task = progress.add_task(
                                "[cyan]Обработка строки...", total=len(s))

                            start = time.time()

                            # Модифицируем алгоритм для обновления прогресса
                            n = len(s)
                            dp = [-float('inf')] * (n + 1)
                            prev = [-1] * (n + 1)
                            chosen_weight = [0.0] * (n + 1)
                            dp[0] = 0

                            for i in range(n):
                                if dp[i] == -float('inf'):
                                    progress.update(task, advance=1)
                                    continue

                                node = trie.root
                                for j in range(i, min(n, i + trie.max_len)):
                                    idx = ord(s[j]) - ord('a')
                                    if node.children[idx] is None:
                                        break
                                    node = node.children[idx]
                                    if node.best_weight is not None:
                                        new_value = dp[i] + node.best_weight
                                        if new_value > dp[j + 1]:
                                            dp[j + 1] = new_value
                                            prev[j + 1] = i
                                            chosen_weight[j + 1] = node.best_weight

                                progress.update(task, advance=1)

                            elapsed = time.time() - start

                            if dp[n] == -float('inf'):
                                total = None
                                seg = None
                            else:
                                total = dp[n]
                                seg = []
                                idx = n
                                while idx > 0:
                                    start_idx = prev[idx]
                                    seg.append(
                                        f"{s[start_idx:idx]}({chosen_weight[idx]:.2f})")
                                    idx = start_idx
                                seg.reverse()
                    else:
                        # Обычный запуск для коротких строк
                        with console.status("[bold cyan]Вычисление оптимального разбиения...[/bold cyan]", spinner="dots"):
                            start = time.time()
                            total, seg = segment_text(s, trie)
                            elapsed = time.time() - start

                    if total is None:
                        result_panel = Panel(
                            "[red]❌ Разбиение невозможно[/red]\n\n[dim]-1[/dim]",
                            title="[bold red]Результат[/bold red]",
                            border_style="red",
                            padding=(1, 2)
                        )
                        console.print(result_panel)
                    else:
                        # Создаем таблицу с разбиением
                        seg_table = Table(show_header=False,
                                        box=box.SIMPLE, padding=(0, 1))
                        seg_table.add_column("№", style="dim", width=3)
                        seg_table.add_column("Слово(вес)", style="green")

                        for i, word in enumerate(seg, 1):
                            seg_table.add_row(str(i), word)

                        # Информация о времени и сложности
                        info_panel = Panel(
                            f"[cyan]⏱ Время:[/cyan] [bold]{elapsed:.6f}[/bold] сек\n"
                            f"[cyan]📊 Сложность:[/cyan] [bold]O({len(s)} * {trie.max_len})[/bold]\n"
                            f"[cyan]📦 Слов в словаре:[/cyan] [bold]{trie.word_count}[/bold]",
                            title="[bold]Информация[/bold]",
                            border_style="cyan",
                            padding=(1, 2)
                        )

                        # Основной результат
                        console.print(
                            f"[bold green]✅ Максимальная сумма:[/bold green] [bold yellow]{total:.2f}[/bold yellow]")
                        console.print()
                        console.print(
                            f"[bold]📝 Разбиение ({len(seg)} слов):[/bold]")
                        console.print(seg_table)
                        console.print(info_panel)

                        # Дополнительная информация для длинных разбиений
                        if len(seg) > 20:
                            console.print(
                                f"\n[dim]Показано {len(seg)} слов. Всего слов в разбиении: {len(seg)}[/dim]")

                except KeyboardInterrupt:
                    print("\n[yellow]Операция прервана[/yellow]")
                except Exception as e:
                    print(f"[red]Ошибка: {e}[/red]")
                    console.print(f"[red]Ошибка: {e}[/red]")
    except KeyboardInterrupt:
        print("\n[yellow]Программа завершена[/yellow]")
    except Exception as e:
        print(f"[red]Критическая ошибка: {e}[/red]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[yellow]Программа прервана[/yellow]")
    except Exception as e:
        print(f"[red]Необработанная ошибка: {e}[/red]")
    finally:
        print("\n[dim]Программа завершена[/dim]")
