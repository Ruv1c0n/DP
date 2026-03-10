#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Лабораторная работа №2
Задача коммивояжера (вариант 4)

Алгоритм:
Динамическое программирование с битовыми масками

Сложность:
O(n^2 * 2^n)
"""

VIS_AVAILABLE = True

try:
    import networkx as nx
    import matplotlib.pyplot as plt
except:
    VIS_AVAILABLE = False

import random
import time

INF = float("inf")

# =====================================
# Проверка GUI
# =====================================

GUI_AVAILABLE = True

try:
    import tkinter as tk
except:
    GUI_AVAILABLE = False


# =====================================
# Безопасный ввод числа
# =====================================

def safe_int(prompt):

    while True:

        value = input(prompt).strip()

        if value == "":
            print("❌ Пустой ввод.")
            continue

        try:
            return int(value)
        except:
            print("❌ Нужно ввести число.")


# =====================================
# Печать матрицы
# =====================================

def print_matrix(matrix):

    n = len(matrix)

    print("\nМатрица расстояний\n")

    print("   ", end="")
    for i in range(n):
        print(f"{i+1:4}", end="")
    print()

    for i in range(n):

        print(f"{i+1:3}", end="")

        for j in range(n):
            print(f"{matrix[i][j]:4}", end="")

        print()


# =====================================
# Генерация случайного графа
# =====================================

def random_graph(n):

    matrix = [[0]*n for _ in range(n)]

    for i in range(n):

        for j in range(i+1, n):

            w = random.randint(1, 20)

            matrix[i][j] = w
            matrix[j][i] = w

    return matrix


# =====================================
# Проверка корректности
# =====================================

def validate_matrix(matrix):

    n = len(matrix)

    for i in range(n):

        for j in range(n):

            if matrix[i][j] < 0:
                raise ValueError("Отрицательные веса недопустимы")

            if i == j and matrix[i][j] != 0:
                matrix[i][j] = 0


# =====================================
# Консольный ввод матрицы
# =====================================

def console_matrix(n):

    matrix = []

    print("\nВведите матрицу:")

    for i in range(n):

        while True:

            row = input(f"Строка {i+1}: ").split()

            if len(row) != n:
                print("❌ Нужно", n, "чисел")
                continue

            try:
                row = [int(x) for x in row]
                matrix.append(row)
                break
            except:
                print("❌ Только числа")

    return matrix


# =====================================
# GUI ввод матрицы
# =====================================

def gui_matrix():

    root = tk.Tk()
    root.title("Матрица расстояний")

    size_var = tk.IntVar(value=4)

    entries = []

    frame = tk.Frame(root)
    frame.pack()

    matrix = []

    def build():

        nonlocal entries

        for widget in frame.winfo_children():
            widget.destroy()

        n = size_var.get()

        entries = [[None]*n for _ in range(n)]

        for i in range(n):
            for j in range(n):

                e = tk.Entry(frame, width=4)
                e.grid(row=i, column=j)

                if i == j:
                    e.insert(0, "0")

                def callback(event, i=i, j=j):

                    value = entries[i][j].get()

                    if value.isdigit():

                        entries[j][i].delete(0, tk.END)
                        entries[j][i].insert(0, value)

                e.bind("<KeyRelease>", callback)

                entries[i][j] = e

    def submit():

        nonlocal matrix

        n = size_var.get()

        matrix = [[0]*n for _ in range(n)]

        for i in range(n):
            for j in range(n):

                try:
                    matrix[i][j] = int(entries[i][j].get())
                except:
                    matrix[i][j] = 0

        root.destroy()

    top = tk.Frame(root)
    top.pack()

    tk.Label(top, text="Размер матрицы").pack(side="left")

    tk.Spinbox(top, from_=2, to=12, textvariable=size_var,
               width=5).pack(side="left")

    tk.Button(top, text="Создать", command=build).pack(side="left")

    build()

    tk.Button(root, text="Готово", command=submit).pack()

    root.mainloop()

    return matrix


# =====================================
# Алгоритм TSP
# =====================================

def tsp(dist, start, end):

    n = len(dist)

    dp = [[INF]*n for _ in range(1 << n)]
    parent = [[-1]*n for _ in range(1 << n)]

    dp[1 << start][start] = 0

    for mask in range(1 << n):

        for u in range(n):

            if dp[mask][u] == INF:
                continue

            for v in range(n):

                if mask & (1 << v):
                    continue

                new_mask = mask | (1 << v)

                cost = dp[mask][u] + dist[u][v]

                if cost < dp[new_mask][v]:

                    dp[new_mask][v] = cost
                    parent[new_mask][v] = u

    final_mask = (1 << n)-1

    cost = dp[final_mask][end]

    if cost == INF:
        return -1, []

    path = []

    mask = final_mask
    city = end

    while city != -1:

        path.append(city)

        prev = parent[mask][city]

        mask ^= (1 << city)
        city = prev

    path.reverse()

    return cost, path


# =====================================
# Вывод результата
# =====================================

def print_result(cost, path):

    print("\n========== РЕЗУЛЬТАТ ==========\n")

    if cost is None:
        print("Маршрут не найден")
        return

    print("Минимальная стоимость:", cost)

    print("Маршрут:")

    print(" -> ".join(str(x+1) for x in path))

    print()


def visualize_graph(matrix, path=None):

    if not VIS_AVAILABLE:
        print("⚠ Визуализация недоступна (нет matplotlib/networkx)")
        return

    n = len(matrix)

    G = nx.Graph()

    for i in range(n):
        G.add_node(i+1)

    for i in range(n):
        for j in range(i+1, n):

            w = matrix[i][j]

            if w != 0:
                G.add_edge(i+1, j+1, weight=w)

    pos = nx.spring_layout(G)

    edges = G.edges()

    weights = nx.get_edge_attributes(G, 'weight')

    nx.draw(G, pos, with_labels=True, node_color="lightblue")

    nx.draw_networkx_edge_labels(G, pos, edge_labels=weights)

    if path:

        path_edges = []

        for i in range(len(path)-1):
            path_edges.append((path[i]+1, path[i+1]+1))

        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=path_edges,
            edge_color="red",
            width=3
        )

    plt.title("Граф городов и найденный маршрут")

    plt.show()

# =====================================
# Основная программа
# =====================================

def main():

    print("\nЗадача коммивояжёра\n")

    if GUI_AVAILABLE:

        print("GUI доступен")

    else:

        print("GUI недоступен — используется консоль")

    n = safe_int("\nКоличество городов: ")

    if n > 15:
        print("❌ Слишком много городов (макс 15)")
        return

    print("\n1 — ввод матрицы")
    print("2 — случайный граф")

    if GUI_AVAILABLE:
        print("3 — ввод через GUI")

    mode = safe_int("Выбор: ")

    if mode == 2:

        matrix = random_graph(n)

    elif mode == 3 and GUI_AVAILABLE:

        matrix = gui_matrix()

        n = len(matrix)

    else:

        matrix = console_matrix(n)

    validate_matrix(matrix)

    print_matrix(matrix)

    start = safe_int("\nНачальный город: ") - 1
    end = safe_int("Конечный город: ") - 1

    t1 = time.time()

    cost, path = tsp(matrix, start, end)

    t2 = time.time()

    print_result(cost, path)

    print("Время выполнения:", round(t2-t1, 5), "сек")
    visualize_graph(matrix, path)


if __name__ == "__main__":
    main()
