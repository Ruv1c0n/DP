#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль с тестами для программы сегментации текста.
Содержит различные тестовые случаи для проверки работоспособности.
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TestType(Enum):
    """
    Типы тестовых случаев.

    Attributes
    ----------
    POSITIVE : str
        Корректные данные, ожидаем успех
    NEGATIVE : str
        Некорректные данные, ожидаем ошибки
    EDGE : str
        Граничные случаи
    PERFORMANCE : str
        Тесты производительности
    """
    POSITIVE = "positive"      # Корректные данные, ожидаем успех
    NEGATIVE = "negative"      # Некорректные данные, ожидаем ошибки
    EDGE = "edge"              # Граничные случаи
    PERFORMANCE = "performance"  # Производительность


@dataclass
class TestCase:
    """
    Класс для представления одного тестового случая.
    
    Содержит все необходимые данные для запуска теста и проверки результатов.

    Attributes
    ----------
    name : str
        Название теста
    description : str
        Описание теста
    type : TestType
        Тип теста
    s : str
        Входная строка
    dictionary : List[Tuple[str, float]]
        Словарь в формате [(слово, вес), ...]
    expected_total : Optional[float]
        Ожидаемая максимальная сумма (None если ошибка)
    expected_segmentation : Optional[List[str]]
        Ожидаемое разбиение (None если ошибка)
    should_fail : bool
        Должен ли тест завершиться ошибкой
    error_type : Optional[type]
        Ожидаемый тип ошибки

    Examples
    --------
    >>> test = TestCase(
    ...     name="Простой тест",
    ...     description="Проверка базового функционала",
    ...     type=TestType.POSITIVE,
    ...     s="hello",
    ...     dictionary=[("hello", 5.0)],
    ...     expected_total=5.0,
    ...     expected_segmentation=["hello(5.00)"]
    ... )
    """
    name: str
    description: str
    type: TestType
    s: str
    dictionary: List[Tuple[str, float]]
    expected_total: Optional[float] = None
    expected_segmentation: Optional[List[str]] = None
    should_fail: bool = False
    error_type: Optional[type] = None

    def __post_init__(self):
        """
        Пост-инициализация: нормализует формат ожидаемого разбиения.
        """
        if self.expected_segmentation:
            # Нормализуем формат для сравнения
            self.expected_segmentation = [
                f"{word}({weight:.2f})" if '(' not in word else word # pyright: ignore[reportUndefinedVariable]
                for word in self.expected_segmentation
            ]


# =========================
# Позитивные тесты (корректные данные)
# =========================

POSITIVE_TESTS = [
    TestCase(
        name="Простой случай",
        description="Одно слово из словаря",
        type=TestType.POSITIVE,
        s="hello",
        dictionary=[("hello", 5.0)],
        expected_total=5.0,
        expected_segmentation=["hello(5.00)"]
    ),

    TestCase(
        name="Два слова",
        description="Строка из двух слов",
        type=TestType.POSITIVE,
        s="helloworld",
        dictionary=[("hello", 5.0), ("world", 3.0)],
        expected_total=8.0,
        expected_segmentation=["hello(5.00)", "world(3.00)"]
    ),

    TestCase(
        name="Перекрывающиеся слова",
        description="Слова с общими префиксами",
        type=TestType.POSITIVE,
        s="catcatch",
        dictionary=[("cat", 2.0), ("catch", 5.0), ("at", 1.0)],
        expected_total=7.0,
        expected_segmentation=["cat(2.00)", "catch(5.00)"]
    ),

    TestCase(
        name="Несколько вариантов",
        description="Выбор оптимального разбиения",
        type=TestType.POSITIVE,
        s="abcde",
        dictionary=[("a", 1.0), ("ab", 3.0), ("abc", 2.0),
                    ("abcd", 4.0), ("abcde", 10.0)],
        expected_total=10.0,
        expected_segmentation=["abcde(10.00)"]
    ),

    TestCase(
        name="Конкурирующие варианты",
        description="Несколько возможных разбиений",
        type=TestType.POSITIVE,
        s="aaaa",
        dictionary=[("a", 1.0), ("aa", 3.0), ("aaa", 4.0), ("aaaa", 5.0)],
        expected_total=6.0,
        expected_segmentation=["aa(3.00)", "aa(3.00)"]
    ),

    TestCase(
        name="Дубликаты слов",
        description="Слова с разными весами, должен выбраться максимальный",
        type=TestType.POSITIVE,
        s="hello",
        dictionary=[("hello", 5.0), ("hello", 10.0), ("hello", 3.0)],
        expected_total=10.0,
        expected_segmentation=["hello(10.00)"]
    ),

    TestCase(
        name="Длинная строка",
        description="Строка из многих слов",
        type=TestType.POSITIVE,
        s="thequickbrownfoxjumpsoverthelazydog",
        dictionary=[
            ("the", 3.0), ("quick", 5.0), ("brown", 4.0), ("fox", 3.0),
            ("jumps", 5.0), ("over", 4.0), ("lazy", 3.0), ("dog", 2.0)
        ],
        expected_total=32.0,
        expected_segmentation=[
            "the(3.00)", "quick(5.00)", "brown(4.00)", "fox(3.00)",
            "jumps(5.00)", "over(4.00)", "the(3.00)", "lazy(3.00)", "dog(2.00)"
        ]
    ),

    TestCase(
        name="Вещественные веса",
        description="Проверка работы с вещественными числами",
        type=TestType.POSITIVE,
        s="test",
        dictionary=[("test", 5.5)],
        expected_total=5.5,
        expected_segmentation=["test(5.50)"]
    ),
]


# =========================
# Негативные тесты (должны вызывать ошибки)
# =========================

NEGATIVE_TESTS = [
    TestCase(
        name="Пустая строка",
        description="Пустая входная строка",
        type=TestType.NEGATIVE,
        s="",
        dictionary=[("test", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Заглавные буквы в строке",
        description="Недопустимые символы в строке",
        type=TestType.NEGATIVE,
        s="HelloWorld",
        dictionary=[("hello", 1.0), ("world", 2.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Цифры в строке",
        description="Недопустимые символы в строке",
        type=TestType.NEGATIVE,
        s="hello123",
        dictionary=[("hello", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Строка слишком длинная",
        description="Превышение лимита длины",
        type=TestType.NEGATIVE,
        s="a" * (10**5 + 1),
        dictionary=[("a", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Пустое слово в словаре",
        description="Попытка вставить пустое слово",
        type=TestType.NEGATIVE,
        s="test",
        dictionary=[("", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Заглавные буквы в слове",
        description="Недопустимые символы в слове словаря",
        type=TestType.NEGATIVE,
        s="test",
        dictionary=[("Test", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Цифры в слове",
        description="Недопустимые символы в слове словаря",
        type=TestType.NEGATIVE,
        s="test",
        dictionary=[("test123", 1.0)],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Нечисловой вес",
        description="Вес не является числом",
        type=TestType.NEGATIVE,
        s="test",
        dictionary=[("test", "not_a_number")],
        should_fail=True,
        error_type=ValueError
    ),

    TestCase(
        name="Отрицательный вес",
        description="Вес может быть отрицательным? В условии не запрещено",
        type=TestType.POSITIVE,  # Должно работать
        s="test",
        dictionary=[("test", -5.0)],
        expected_total=-5.0,
        expected_segmentation=["test(-5.00)"]
    ),
]


# =========================
# Граничные тесты
# =========================

EDGE_TESTS = [
    TestCase(
        name="Минимальная строка",
        description="Строка из одного символа",
        type=TestType.EDGE,
        s="a",
        dictionary=[("a", 1.0)],
        expected_total=1.0,
        expected_segmentation=["a(1.00)"]
    ),

    TestCase(
        name="Максимальная длина слова",
        description="Слово максимальной длины (20)",
        type=TestType.EDGE,
        s="a" * 20,
        dictionary=[("a" * 20, 100.0)],
        expected_total=100.0,
        expected_segmentation=[f"{'a'*20}(100.00)"]
    ),

    TestCase(
        name="Нет подходящих слов",
        description="Ни одно слово не подходит",
        type=TestType.EDGE,
        s="abcde",
        dictionary=[("xyz", 1.0), ("test", 2.0)],
        expected_total=None,
        expected_segmentation=None
    ),

    TestCase(
        name="Частичное совпадение",
        description="Совпадает только часть строки",
        type=TestType.EDGE,
        s="hello world",
        dictionary=[("hello", 5.0)],
        expected_total=None,  # Пробел недопустим, поэтому не должно работать
        expected_segmentation=None
    ),

    TestCase(
        name="Огромный вес",
        description="Очень большой вес",
        type=TestType.EDGE,
        s="big",
        dictionary=[("big", 1e9)],
        expected_total=1e9,
        expected_segmentation=["big(1000000000.00)"]
    ),

    TestCase(
        name="Очень маленький вес",
        description="Очень маленький вес",
        type=TestType.EDGE,
        s="small",
        dictionary=[("small", 1e-9)],
        expected_total=1e-9,
        expected_segmentation=["small(0.00)"]
    ),

    TestCase(
        name="Много дубликатов",
        description="Много дубликатов с разными весами",
        type=TestType.EDGE,
        s="test",
        dictionary=[("test", i) for i in range(1, 101)],
        expected_total=100.0,
        expected_segmentation=["test(100.00)"]
    ),
]


# =========================
# Тесты производительности
# =========================

PERFORMANCE_TESTS = [
    TestCase(
        name="Большая строка",
        description="Строка из 10^5 символов",
        type=TestType.PERFORMANCE,
        s="a" * 10**5,
        dictionary=[("a", 1.0), ("aa", 2.0), ("aaa", 3.0)],
        expected_total=float(10**5),  # все 'a' по 1.0
        expected_segmentation=None  # Не проверяем разбиение для производительности
    ),

    TestCase(
        name="Большой словарь",
        description="Словарь из 10^4 слов",
        type=TestType.PERFORMANCE,
        s="abcdefghijklmnopqrstuvwxyz" * 1000,
        dictionary=[(chr(97 + i) * (i+1), float(i+1)) for i in range(26)],
        expected_total=None,  # Трудно предсказать
        expected_segmentation=None
    ),
]


# =========================
# Объединение всех тестов
# =========================

def get_all_tests() -> List[TestCase]:
    """
    Возвращает список всех тестов.

    Returns
    -------
    List[TestCase]
        Список всех тестовых случаев

    Examples
    --------
    >>> tests = get_all_tests()
    >>> len(tests) > 0
    True
    """
    return POSITIVE_TESTS + NEGATIVE_TESTS + EDGE_TESTS + PERFORMANCE_TESTS


def get_tests_by_type(test_type: TestType) -> List[TestCase]:
    """
    Возвращает тесты указанного типа.

    Parameters
    ----------
    test_type : TestType
        Тип тестов для фильтрации

    Returns
    -------
    List[TestCase]
        Список тестов указанного типа

    Examples
    --------
    >>> pos_tests = get_tests_by_type(TestType.POSITIVE)
    >>> all(t.type == TestType.POSITIVE for t in pos_tests)
    True
    """
    return [test for test in get_all_tests() if test.type == test_type]


# =========================
# Тестовые сценарии для интерактивного ввода
# =========================

INTERACTIVE_TEST_SCENARIOS = [
    {
        "name": "Базовый сценарий",
        "inputs": [
            "1",  # режим обычного ввода
            "helloworld",  # строка
            "2",  # количество записей
            "hello 5",  # запись 1
            "world 3",  # запись 2
            "н",  # не показывать бор
        ],
        "expected_output_contains": ["8.00", "hello", "world"]
    },

    {
        "name": "Сценарий с ошибкой ввода",
        "inputs": [
            "1",
            "HelloWorld",  # ошибка - заглавные
            "helloworld",  # правильный ввод
            "2",
            "hello 5",
            "world abc",  # ошибка - вес не число
            "world 3",  # правильный ввод
            "н",
        ],
        "expected_output_contains": ["8.00", "hello", "world"]
    },

    {
        "name": "Сценарий с показом дерева",
        "inputs": [
            "1",
            "test",
            "1",
            "test 10",
            "да",  # показать бор
        ],
        "expected_output_contains": ["10.00", "test", "Префиксное дерево"]
    },

    {
        "name": "Сценарий с невозможным разбиением",
        "inputs": [
            "1",
            "xyz",
            "1",
            "test 10",
            "н",
        ],
        "expected_output_contains": ["-1", "невозможно"]
    },

    {
        "name": "Сценарий с отрицательным весом",
        "inputs": [
            "1",
            "negative",
            "1",
            "negative -5",
            "н",
        ],
        "expected_output_contains": ["-5.00", "negative"]
    },
]

if __name__ == "__main__":
    """
    При запуске модуля самостоятельно выводит информацию о загруженных тестах.
    """
    print(f"Загружено тестов:")
    print(f"  Позитивных: {len(POSITIVE_TESTS)}")
    print(f"  Негативных: {len(NEGATIVE_TESTS)}")
    print(f"  Граничных: {len(EDGE_TESTS)}")
    print(f"  Производительности: {len(PERFORMANCE_TESTS)}")
    print(f"  Интерактивных сценариев: {len(INTERACTIVE_TEST_SCENARIOS)}")
    print(f"  Всего: {len(get_all_tests())}")
