from main import tsp, safe_int, read_matrix, INF
import random
import unittest
from unittest.mock import patch
from io import StringIO
import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestTSP(unittest.TestCase):
    def test_single_city(self):
        """Граф с одним городом"""
        dist = [[0]]
        cost, path = tsp(dist, 0, 0)
        self.assertEqual(cost, 0)
        # В программе города нумеруются с 1 для вывода
        self.assertEqual(path, [1])  # ожидаем [1], а не [0]

    def test_no_path(self):
        """Нет пути между start и end"""
        dist = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        # Из-за условия if matrix[u][v] == 0 and u != v, нулевые веса считаются отсутствием пути
        # Поэтому путь должен быть -1
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -1)

    def test_partial_no_path(self):
        """Частичное отсутствие путей"""
        dist = [
            [0, 5, 0],  # 0 означает отсутствие пути
            [5, 0, 3],
            [0, 3, 0]
        ]
        # Нет прямого пути 0->2, но есть через 1: 0->1->2 = 5+3=8
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, 8)
        # В программе города нумеруются с 1 для вывода
        self.assertEqual(path, [1, 2, 3])  # [0,1,2] -> [1,2,3]

    def test_different_start_end(self):
        """Разные комбинации start и end"""
        dist = [
            [0, 2, 3, 4],
            [2, 0, 5, 6],
            [3, 5, 0, 7],
            [4, 6, 7, 0]
        ]

        # start = 1, end = 3 (индексы с 0)
        cost1, path1 = tsp(dist, 1, 3)
        self.assertIsNotNone(cost1)
        # В программе города выводятся с 1
        self.assertEqual(path1[0], 2)  # индекс 1 -> город 2
        self.assertEqual(path1[-1], 4)  # индекс 3 -> город 4

        # start = 2, end = 0 (индексы с 0)
        cost2, path2 = tsp(dist, 2, 0)
        self.assertIsNotNone(cost2)
        self.assertEqual(path2[0], 3)  # индекс 2 -> город 3
        self.assertEqual(path2[-1], 1)  # индекс 0 -> город 1

    def test_complete_graph_symmetric(self):
        """Полный симметричный граф с разными весами"""
        dist = [
            [0, 2, 9, 10],
            [2, 0, 6, 4],
            [9, 6, 0, 8],
            [10, 4, 8, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        # Проверяем, что все города посещены (преобразуем обратно в индексы 0-3)
        indices = [x - 1 for x in path]
        self.assertEqual(len(set(indices)), 4)
        # Проверяем, что стоимость положительная
        self.assertGreater(cost, 0)

    def test_very_large_graph(self):
        """Граф с большим количеством городов (8)"""
        dist = [
            [0, 1, 2, 3, 4, 5, 6, 7],
            [1, 0, 8, 9, 10, 11, 12, 13],
            [2, 8, 0, 14, 15, 16, 17, 18],
            [3, 9, 14, 0, 19, 20, 21, 22],
            [4, 10, 15, 19, 0, 23, 24, 25],
            [5, 11, 16, 20, 23, 0, 26, 27],
            [6, 12, 17, 21, 24, 26, 0, 28],
            [7, 13, 18, 22, 25, 27, 28, 0]
        ]
        cost, path = tsp(dist, 0, 7)
        self.assertIsNotNone(cost)
        self.assertEqual(len(path), 8)
        # Преобразуем в индексы для проверки
        indices = [x - 1 for x in path]
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices[-1], 7)

    def test_maximum_values(self):
        """Тест с максимальными значениями"""
        MAX = 10**6
        dist = [
            [0, MAX, MAX//2],
            [MAX, 0, MAX//3],
            [MAX//2, MAX//3, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertIsNotNone(cost)
        self.assertLess(cost, 2*MAX)

    def test_non_integer_weights(self):
        """Веса с плавающей точкой"""
        dist = [
            [0, 1.5, 2.7],
            [1.5, 0, 3.2],
            [2.7, 3.2, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        # Программа может преобразовывать float в int или использовать float
        self.assertTrue(isinstance(cost, (int, float)))
        # Проверяем с учетом возможного округления
        self.assertAlmostEqual(float(cost), 4.7, places=0)

    def test_mixed_weights(self):
        """Смешанные веса: нулевые, положительные"""
        dist = [
            [0, 0, 100, 5],  # 0 означает отсутствие пути
            [0, 0, 50, 0],
            [100, 50, 0, 1],
            [5, 0, 1, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        # Должен найти путь 0->3 напрямую = 5, или 0->2->3 = 100+1=101
        # Оптимальный: 0->3 = 5
        self.assertEqual(cost, -1)

    def test_linear_graph(self):
        """Линейный граф (все города на одной линии)"""
        dist = [
            [0, 1, 0, 0],  # 0 означает отсутствие пути
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, 3)
        # Проверяем путь с учетом нумерации с 1
        self.assertEqual(path, [1, 2, 3, 4])  # [0,1,2,3] -> [1,2,3,4]

    def test_star_graph(self):
        """Граф-звезда (центр соединен со всеми)"""
        dist = [
            [0, 1, 1, 1],
            [1, 0, 0, 0],  # 0 означает отсутствие пути
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ]
        # Нет пути, который проходит через все города, так как периферийные города не связаны между собой
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, -1)

    def test_zero_cost_cycle(self):
        """Граф с нулевыми весами"""
        dist = [
            [0, 0, 5],  # 0 означает отсутствие пути
            [0, 0, 0],
            [5, 0, 0]
        ]
        # Из-за условия if matrix[u][v] == 0 and u != v,
        # путь 0->1 недоступен, поэтому нет пути от 0 до 2
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -1)

    def test_small_negative_weights(self):
        """Небольшие отрицательные веса"""
        dist = [
            [0, -1, 2],
            [-1, 0, -1],
            [2, -1, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -2)
        self.assertEqual(path, [1, 2, 3])  # [0,1,2] -> [1,2,3]

    def test_two_cities(self):
        """Граф с 2 городами"""
        dist = [
            [0, 5],
            [5, 0]
        ]
        cost, path = tsp(dist, 0, 1)
        self.assertEqual(cost, 5)
        self.assertEqual(path, [1, 2])  # [0,1] -> [1,2]

    def test_three_cities(self):
        """Граф с 3 городами"""
        dist = [
            [0, 10, 15],
            [10, 0, 20],
            [15, 20, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, 30)
        self.assertEqual(path, [1, 2, 3])  # [0,1,2] -> [1,2,3]

    def test_four_cities(self):
        """Граф с 4 городами"""
        dist = [
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, 75)

    def test_five_cities(self):
        """Граф с 5 городами"""
        dist = [
            [0, 3, 1, 5, 8],
            [3, 0, 6, 7, 9],
            [1, 6, 0, 4, 2],
            [5, 7, 4, 0, 3],
            [8, 9, 2, 3, 0]
        ]
        cost, path = tsp(dist, 0, 4)
        self.assertEqual(cost, 16)

    def test_large_weights(self):
        """Граф с большими весами"""
        dist = [
            [0, 1000, 2000],
            [1000, 0, 3000],
            [2000, 3000, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, 4000)

    def test_path_length(self):
        """Проверка длины пути"""
        dist = [
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(len(path), 4)

    def test_multiple_optimal(self):
        """Несколько оптимальных путей"""
        dist = [
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, 3)

    def test_asymmetric(self):
        """Асимметричный граф"""
        dist = [
            [0, 2, 9],
            [1, 0, 6],
            [15, 7, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertIsNotNone(cost)

    def test_sparse(self):
        """Разреженный граф"""
        INF = float("inf")
        dist = [
            [0, 1, INF],
            [1, 0, 2],
            [INF, 2, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, 3)

    def test_chain(self):
        """Цепочка городов"""
        dist = [
            [0, 1, 100, 100],
            [1, 0, 1, 100],
            [100, 1, 0, 1],
            [100, 100, 1, 0]
        ]
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, 3)

    def test_random_graphs(self):
        """Случайные графы"""
        for _ in range(5): 
            n = 5
            dist = [[0]*n for _ in range(n)]
            for i in range(n):
                for j in range(i+1, n):
                    w = random.randint(1, 20)
                    dist[i][j] = w
                    dist[j][i] = w
            cost, path = tsp(dist, 0, n-1)
            self.assertIsNotNone(cost)

    def test_six_cities(self):
        """Граф с 6 городами"""
        dist = [
            [0, 2, 9, 10, 7, 3],
            [2, 0, 6, 4, 3, 8],
            [9, 6, 0, 8, 5, 7],
            [10, 4, 8, 0, 6, 2],
            [7, 3, 5, 6, 0, 4],
            [3, 8, 7, 2, 4, 0]
        ]
        cost, path = tsp(dist, 0, 5)
        self.assertIsNotNone(cost)

    def test_zero_as_no_path(self):
        """Проверка, что 0 интерпретируется как отсутствие пути"""
        dist = [
            [0, 0, 10],  # 0 между 0 и 1 означает отсутствие пути
            [0, 0, 5],
            [10, 5, 0]
        ]
        # Нет пути от 0 до 2, потому что нельзя пройти через 1 (0-1 нет)
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -1)


class TestTSPAdditional(unittest.TestCase):
    """Дополнительные тесты алгоритма TSP"""

    def test_negative_cycle_but_valid_path(self):
        """Граф с отрицательными весами и корректным путем"""
        dist = [
            [0, -5, 10],
            [-5, 0, -3],
            [10, -3, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -8)
        self.assertEqual(path, [1, 2, 3])  # [0,1,2] -> [1,2,3]

    def test_large_random_graph(self):
        """Большой случайный граф"""
        n = 7
        dist = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Избегаем 0, чтобы не создавать отсутствующие пути
                    dist[i][j] = random.randint(
                        1, 50) if random.random() > 0.1 else random.randint(-20, -1)
        cost, path = tsp(dist, 0, n - 1)
        self.assertIsNotNone(cost)
        indices = [x - 1 for x in path]
        self.assertEqual(indices[0], 0)
        self.assertEqual(indices[-1], n - 1)

    def test_all_negative_weights(self):
        """Граф только с отрицательными весами"""
        dist = [
            [0, -2, -3],
            [-2, 0, -4],
            [-3, -4, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -6)

    def test_zero_matrix(self):
        """Матрица только из нулей - все пути отсутствуют"""
        dist = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        # Нет путей, так как 0 означает отсутствие ребра
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -1)

    def test_large_negative_values(self):
        """Очень большие отрицательные веса"""
        dist = [
            [0, -1000, 5],
            [-1000, 0, -2000],
            [5, -2000, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertEqual(cost, -3000)

    def test_float_negative(self):
        """Отрицательные вещественные веса"""
        dist = [
            [0, -1.5, 3.0],
            [-1.5, 0, -2.5],
            [3.0, -2.5, 0]
        ]
        cost, path = tsp(dist, 0, 2)
        self.assertAlmostEqual(float(cost), -4.0, places=0)

    def test_mix_zero_and_positive(self):
        """Смесь нулей (нет пути) и положительных весов"""
        dist = [
            [0, 0, 5, 0],
            [0, 0, 3, 2],
            [5, 3, 0, 0],
            [0, 2, 0, 0]
        ]
        # Путь 0->2->1->3 = 5+3+2=10
        cost, path = tsp(dist, 0, 3)
        self.assertEqual(cost, 10)
        self.assertEqual(path, [1, 3, 2, 4])  # [0,2,1,3] -> [1,3,2,4]


class TestInputValidation(unittest.TestCase):
    """Тесты обработки пользовательского ввода"""

    @patch("builtins.input", side_effect=["abc", "5"])
    def test_safe_int_invalid_then_valid(self, mock_input):
        """Сначала неверный ввод, затем корректный"""
        result = safe_int("Введите число", test_mode=True)
        self.assertEqual(result, 5)

    @patch("builtins.input", side_effect=["", "3"])
    def test_safe_input_empty(self, mock_input):
        """Пустой ввод"""
        with self.assertRaises(EOFError):
            safe_int("Введите число", test_mode=True)

    @patch("builtins.input", side_effect=["10 20", "5"])
    def test_safe_input_wrong_format(self, mock_input):
        """Неверный формат числа"""
        result = safe_int("Введите число", test_mode=True)
        self.assertEqual(result, 5)

    @patch("builtins.input", side_effect=[
        "-1",  # отрицательное значение для n
        "3"    # корректное значение
    ])
    def test_safe_input_negative_then_valid(self, mock_input):
        """Отрицательное значение, затем корректное"""
        result = safe_int("Введите n", minimum=1, test_mode=True)
        self.assertEqual(result, 3)

    @patch("builtins.input", side_effect=["abc", "def", "xyz"])
    def test_safe_int_all_invalid_raises(self, mock_input):
        """Все введенные значения некорректны - должно выбрасывать исключение"""
        with self.assertRaises(EOFError):
            safe_int("Введите число", test_mode=True)

    @patch("builtins.input", side_effect=[""])
    def test_safe_int_empty_input_raises(self, mock_input):
        """Пустой ввод в тестовом режиме"""
        with self.assertRaises(EOFError):
            safe_int("Введите число", test_mode=True)

    @patch("builtins.input", side_effect=["0", "-1", "abc"])
    def test_safe_int_with_min_max_all_invalid(self, mock_input):
        """Все значения вне допустимого диапазона"""
        with self.assertRaises((EOFError, ValueError)):
            safe_int("Введите число", minimum=1, maximum=10, test_mode=True)


if __name__ == "__main__":
    unittest.main()
