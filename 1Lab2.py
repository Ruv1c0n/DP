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
        self.word_count = 0  # количество слов в боре

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
            self.word_count += 1
        else:
            node.best_weight = max(node.best_weight, weight)

    def visualize(self):
        """
        Улучшенная визуализация бора в виде дерева.
        Возвращает строку с графическим представлением.
        """
        if self.root is None:
            return "🌳 Бор пуст"

        lines = []
        lines.append("🌳 СТРУКТУРА ПРЕФИКСНОГО ДЕРЕВА (БОР)")
        lines.append("=" * 50)
        lines.append(
            f"📊 Статистика: {self.word_count} слов, макс. длина: {self.max_len}")
        lines.append("=" * 50)
        lines.append("")

        # Собираем все пути для более понятного отображения
        all_paths = self._collect_paths(self.root, "", [])

        # Сортируем пути для красивого вывода
        all_paths.sort()

        # Выводим слова с их весами
        if all_paths:
            lines.append("📚 СЛОВА В ДЕРЕВЕ:")
            for path, weight in all_paths:
                lines.append(f"   • '{path}' → вес: {weight}")
            lines.append("")

        lines.append("🔍 ДЕТАЛЬНАЯ СТРУКТУРА:")
        self._visualize_node(self.root, "", True, lines, 0)

        lines.append("")
        lines.append("=" * 50)
        lines.append("📌 Условные обозначения:")
        lines.append("   • ••→ - путь к узлу")
        lines.append("   • [ВЕС] - в этом узле заканчивается слово")
        lines.append("   • (буква) - переход по букве")

        return "\n".join(lines)

    def _collect_paths(self, node, current_path, paths):
        """Собирает все слова из дерева с их весами"""
        if node.best_weight is not None:
            paths.append((current_path, node.best_weight))

        for i in range(26):
            if node.children[i] is not None:
                char = chr(ord('a') + i)
                self._collect_paths(
                    node.children[i], current_path + char, paths)

        return paths

    def _visualize_node(self, node, prefix, is_last, lines, depth):
        """
        Улучшенный рекурсивный метод для визуализации узлов бора.
        """
        if node is None:
            return

        # Формируем красивое обозначение узла
        if depth == 0:
            # Корневой узел
            node_display = "● КОРЕНЬ"
            if node.best_weight is not None:
                node_display += f" [ВЕС: {node.best_weight}]"
            lines.append(node_display)
        else:
            # Для остальных узлов показываем последнюю букву
            current_char = prefix[-1] if prefix else "?"

            # Выбираем символ для ветвления
            branch = "└── " if is_last else "├── "

            # Формируем отступ
            if depth == 1:
                indent = ""
            else:
                indent = "    " * (depth - 1)
                if not is_last:
                    indent = indent[:-4] + "│   " * (depth - 1)

            # Собираем полный путь до этого узла для контекста
            path_so_far = self._get_path_to_node(prefix)

            # Отображаем узел
            node_display = f"{indent}{branch}• '{current_char}'"

            # Добавляем информацию о пути
            if depth > 0:
                node_display += f" (путь: '{path_so_far}')"

            # Если в узле заканчивается слово, выделяем это
            if node.best_weight is not None:
                node_display += f" ⭐ [ВЕС: {node.best_weight}]"

            lines.append(node_display)

        # Собираем всех потомков
        children_list = []
        for i in range(26):
            if node.children[i] is not None:
                char = chr(ord('a') + i)
                children_list.append((char, node.children[i]))

        # Если есть потомки, показываем их
        if children_list:
            # Добавляем небольшую информацию о количестве потомков
            if depth == 0:
                lines.append(f"   ↓ {len(children_list)} ветвей:")

            # Рекурсивно выводим всех потомков
            for idx, (char, child_node) in enumerate(children_list):
                is_last_child = (idx == len(children_list) - 1)
                self._visualize_node(child_node, prefix +
                                     char, is_last_child, lines, depth + 1)

    def _get_path_to_node(self, prefix):
        """Возвращает путь от корня до узла (для контекста)"""
        if not prefix:
            return "корень"
        return prefix


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
    print()

    trie = Trie()

    s = read_string()
    print()
    read_dictionary(trie)
    print()

    # Добавим возможность посмотреть бор
    while True:
        show_trie = safe_input("Показать структуру бора? (д/н): ").lower()
        if show_trie in ['д', 'да', 'y', 'yes', 'н', 'нет', 'n', 'no']:
            if show_trie in ['д', 'да', 'y', 'yes']:
                print("\n" + "=" * 60)
                print(trie.visualize())
                print("=" * 60)
            break
        else:
            print("Пожалуйста, ответьте д/н")

    print()
    total, segmentation = segment_text(s, trie)

    if total is None:
        print("\n❌ Разбиение невозможно.")
        print("-1")
    else:
        print("\n✅ Максимальная сумма:", total)
        print("📝 Оптимальное разбиение:")
        print("   " + " + ".join(segmentation))


if __name__ == "__main__":
    main()
