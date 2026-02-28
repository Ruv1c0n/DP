import sys


# =========================
# Класс узла префиксного дерева (бор)
# =========================
class TrieNode:
    def __init__(self):
        # Массив из 26 букв (a-z) вместо словаря — быстрее
        self.children = [None] * 26

        # Максимальный вес слова, если слово заканчивается в этом узле
        self.best_weight = None

        # Длина слова (нужна для восстановления)
        self.word_length = 0


# =========================
# Класс бора
# =========================
class Trie:
    def __init__(self):
        self.root = TrieNode()
        self.max_len = 0  # максимальная длина слова в словаре

    def insert(self, word, weight):
        """
        Вставка слова в бор.
        Если слово встречается несколько раз (омонимия),
        сохраняем только максимальный вес.
        """
        node = self.root
        length = len(word)
        self.max_len = max(self.max_len, length)

        for char in word:
            index = ord(char) - ord('a')

            if node.children[index] is None:
                node.children[index] = TrieNode()

            node = node.children[index]

        # Если слово уже существовало — оставляем максимальный вес
        if node.best_weight is None:
            node.best_weight = weight
            node.word_length = length
        else:
            node.best_weight = max(node.best_weight, weight)


# =========================
# Безопасный ввод строки
# =========================
def safe_input(prompt):
    while True:
        try:
            return input(prompt).strip()
        except EOFError:
            print("Ошибка ввода. Повторите попытку.")


# =========================
# Ввод строки S
# =========================
def read_string():
    while True:
        s = safe_input("Введите строку S (только строчные латинские буквы): ")

        if not s:
            print("Ошибка: строка не может быть пустой.")
            continue

        if not s.isalpha() or not s.islower():
            print("Ошибка: допустимы только строчные латинские буквы.")
            continue

        return s


# =========================
# Ввод словаря
# =========================
def read_dictionary(trie):
    while True:
        m_str = safe_input("Введите количество записей в словаре: ")

        if not m_str.isdigit():
            print("Ошибка: введите натуральное число.")
            continue

        m = int(m_str)

        if m <= 0:
            print("Ошибка: количество должно быть больше 0.")
            continue

        break

    print("Введите записи в формате: слово вес")

    for i in range(m):
        while True:
            line = safe_input(f"Запись {i + 1}: ")
            parts = line.split()

            if len(parts) != 2:
                print("Ошибка: введите слово и вес через пробел.")
                continue

            word, weight_str = parts

            if not word.isalpha() or not word.islower():
                print("Ошибка: слово должно содержать только строчные латинские буквы.")
                continue

            try:
                weight = float(weight_str)
            except ValueError:
                print("Ошибка: вес должен быть числом.")
                continue

            trie.insert(word, weight)
            break


# =========================
# Основной алгоритм ДП
# =========================
def segment_text(s, trie):
    n = len(s)

    # dp[i] — максимальная сумма для первых i символов
    dp = [-float('inf')] * (n + 1)

    # prev[i] — индекс начала последнего слова
    prev = [-1] * (n + 1)

    # хранение веса выбранного слова
    chosen_weight = [0] * (n + 1)

    dp[0] = 0  # база

    # Проходим по всем позициям строки
    for i in range(n):

        # Если в позицию i попасть нельзя — пропускаем
        if dp[i] == -float('inf'):
            continue

        node = trie.root

        # Идём вперёд по бору (не дальше max_len)
        for j in range(i, min(n, i + trie.max_len)):

            index = ord(s[j]) - ord('a')

            if node.children[index] is None:
                break

            node = node.children[index]

            # Если найдено слово
            if node.best_weight is not None:
                new_value = dp[i] + node.best_weight

                # Обновляем dp
                if new_value > dp[j + 1]:
                    dp[j + 1] = new_value
                    prev[j + 1] = i
                    chosen_weight[j + 1] = node.best_weight

    # Если до конца строки не добрались
    if dp[n] == -float('inf'):
        return None, None

    # =========================
    # Восстановление ответа
    # =========================
    result = []
    index = n

    while index > 0:
        start = prev[index]
        word = s[start:index]
        weight = chosen_weight[index]

        result.append(f"{word}({weight})")
        index = start

    result.reverse()

    return dp[n], result


# =========================
# Главная функция
# =========================
def main():
    print("=== Вариант 4: Омонимия (оптимизированная версия) ===")

    trie = Trie()

    s = read_string()
    read_dictionary(trie)

    total, segmentation = segment_text(s, trie)

    if total is None:
        print("\nРазбиение невозможно.")
        print("-1")
    else:
        print("\nМаксимальная сумма:", total)
        print("Оптимальное разбиение:")
        print(" ".join(segmentation))


if __name__ == "__main__":
    main()
