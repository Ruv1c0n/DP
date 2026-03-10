import random
import unittest
from main import tsp


class TestTSP(unittest.TestCase):

    # --------------------------
    # Минимальные графы
    # --------------------------

    def test_two_cities(self):

        dist = [
            [0, 5],
            [5, 0]
        ]

        cost, path = tsp(dist, 0, 1)

        self.assertEqual(cost, 5)
        self.assertEqual(path, [0, 1])

    def test_three_cities(self):

        dist = [
            [0, 10, 15],
            [10, 0, 20],
            [15, 20, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 30)

    # --------------------------
    # Нормальные графы
    # --------------------------

    def test_four_cities(self):

        dist = [
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 75)

    def test_five_cities(self):

        dist = [
            [0, 3, 1, 5, 8],
            [3, 0, 6, 7, 9],
            [1, 6, 0, 4, 2],
            [5, 7, 4, 0, 3],
            [8, 9, 2, 3, 0]
        ]

        cost, path = tsp(dist, 0, 4)

        self.assertEqual(cost, 16)

    # --------------------------
    # Edge cases
    # --------------------------

    def test_zero_weights(self):

        dist = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 0)

    def test_large_weights(self):

        dist = [
            [0, 1000, 2000],
            [1000, 0, 3000],
            [2000, 3000, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 4000)

    def test_negative_weights(self):

        dist = [
            [0, -1, 2],
            [-1, 0, 3],
            [2, 3, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertIsNotNone(cost)

    # --------------------------
    # Проверка маршрута
    # --------------------------

    def test_path_length(self):

        dist = [
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(len(path), 4)

    def test_all_cities_unique(self):

        dist = [
            [0, 2, 3],
            [2, 0, 4],
            [3, 4, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(len(set(path)), 3)

    def test_start_end_correct(self):

        dist = [
            [0, 5, 6],
            [5, 0, 2],
            [6, 2, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(path[0], 0)
        self.assertEqual(path[-1], 2)

    # --------------------------
    # Несколько оптимальных путей
    # --------------------------

    def test_multiple_optimal(self):

        dist = [
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 3)

    # --------------------------
    # Асимметричный граф
    # --------------------------

    def test_asymmetric(self):

        dist = [
            [0, 2, 9],
            [1, 0, 6],
            [15, 7, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertIsNotNone(cost)

    # --------------------------
    # Разреженный граф
    # --------------------------

    def test_sparse(self):

        INF = float("inf")

        dist = [
            [0, 1, INF],
            [1, 0, 2],
            [INF, 2, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 3)

    # --------------------------
    # Цепной граф
    # --------------------------

    def test_chain(self):

        dist = [
            [0, 1, 100, 100],
            [1, 0, 1, 100],
            [100, 1, 0, 1],
            [100, 100, 1, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 3)

    # --------------------------
    # Случайные графы
    # --------------------------

    def test_random_graphs(self):

        for _ in range(20):

            n = 5

            dist = [[0]*n for _ in range(n)]

            for i in range(n):
                for j in range(i+1, n):

                    w = random.randint(1, 20)

                    dist[i][j] = w
                    dist[j][i] = w

            cost, path = tsp(dist, 0, n-1)

            self.assertIsNotNone(cost)

    # ============================
    # Простые тесты
    # ============================

    def test_two_cities(self):

        dist = [
            [0, 5],
            [5, 0]
        ]

        cost, path = tsp(dist, 0, 1)

        self.assertEqual(cost, 5)
        self.assertEqual(path, [0, 1])

    def test_three_cities(self):

        dist = [
            [0, 10, 15],
            [10, 0, 20],
            [15, 20, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 30)

    def test_four_cities(self):

        dist = [
            [0, 10, 15, 20],
            [10, 0, 35, 25],
            [15, 35, 0, 30],
            [20, 25, 30, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 75)

    # ============================
    # Средние графы
    # ============================

    def test_five_cities(self):

        dist = [
            [0, 3, 1, 5, 8],
            [3, 0, 6, 7, 9],
            [1, 6, 0, 4, 2],
            [5, 7, 4, 0, 3],
            [8, 9, 2, 3, 0]
        ]

        cost, path = tsp(dist, 0, 4)

        self.assertEqual(cost, 16)

    def test_six_cities(self):

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

    # ============================
    # Edge cases
    # ============================

    def test_start_equals_end(self):

        dist = [
            [0, 1, 2],
            [1, 0, 3],
            [2, 3, 0]
        ]

        cost, path = tsp(dist, 0, 0)

        self.assertIsNotNone(cost)

    def test_zero_weights(self):

        dist = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 0)

    def test_large_weights(self):

        dist = [
            [0, 1000, 2000],
            [1000, 0, 3000],
            [2000, 3000, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 4000)

    # ============================
    # Проверка маршрута
    # ============================

    def test_path_length(self):

        dist = [
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(len(path), 4)

    def test_all_cities_visited(self):

        dist = [
            [0, 1, 2, 3],
            [1, 0, 4, 5],
            [2, 4, 0, 6],
            [3, 5, 6, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(len(set(path)), 4)

    # ============================
    # Несколько оптимальных путей
    # ============================

    def test_multiple_optimal_paths(self):

        dist = [
            [0, 1, 1, 1],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [1, 1, 1, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 3)

    # ============================
    # Сложные тесты
    # ============================

    def test_asymmetric_graph(self):

        dist = [
            [0, 2, 9],
            [1, 0, 6],
            [15, 7, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertIsNotNone(cost)

    def test_sparse_graph(self):

        INF = float("inf")

        dist = [
            [0, 1, INF],
            [1, 0, 2],
            [INF, 2, 0]
        ]

        cost, path = tsp(dist, 0, 2)

        self.assertEqual(cost, 3)

    def test_chain_graph(self):

        dist = [
            [0, 1, 100, 100],
            [1, 0, 1, 100],
            [100, 1, 0, 1],
            [100, 100, 1, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertEqual(cost, 3)

    def test_random_like(self):

        dist = [
            [0, 7, 3, 8],
            [7, 0, 2, 5],
            [3, 2, 0, 6],
            [8, 5, 6, 0]
        ]

        cost, path = tsp(dist, 0, 3)

        self.assertIsNotNone(cost)


if __name__ == "__main__":
    unittest.main()
