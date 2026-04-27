'''
Модуль для вычисления оптимальной стратегии дилера в блэкджеке с помощью динамического программирования.

Реализует модель перебора карт дилером в бесконечной колоде и применяет алгоритм value iteration
для поиска политики, максимизирующей ожидаемый результат против фиксированной суммы игрока.
Результаты предрассчитываются для всех возможных сумм игрока (2-21) и кэшируются в словаре
DEALER_POLICIES, который затем используется в игровом процессе.
'''


# Вероятности вытянуть карту определённого номинала из бесконечной колоды.

# Ключи: 2-9, 10 (включает 10, J, Q, K, поэтому 4/13), 11 (туз).
# Значения: вероятности(float от 0 до 1).

# Type: dict[int, float]
from typing import Any, Literal


CARD_PROB = {i: 1/13 for i in range(2, 10)}
CARD_PROB[10] = 4 / 13
CARD_PROB[11] = 1 / 13   # Туз = 11


def step(dealer_sum, usable_ace, card) -> tuple[Any, Any | bool, Any]:
    """
    Моделирует добор одной карты дилером и возвращает новое состояние.

    Учитывает правила блэкджека:
    - Туз может быть 11 или 1 в зависимости от суммы.
    - При сумме > 21 и наличии мягкого туза происходит его "жёсткая" конвертация (сумма уменьшается на 10).

    Args:
        dealer_sum (int): Текущая сумма очков дилера.
        usable_ace (bool): Есть ли у дилера мягкий туз (учитываемый как 11).
        card (int): Номинал вытянутой карты (11 для туза, иначе 2-10).

    Returns:
        tuple: (new_sum, new_usable_ace, bust)
            new_sum (int): Новая сумма очков.
            new_usable_ace (bool): Новый статус мягкого туза.
            bust (bool): Произошёл ли перебор (new_sum > 21).
    """
    if card == 11:                      # вытянули туза
        if dealer_sum + 11 <= 21:
            new_sum : int = dealer_sum + 11
            # Если уже был usable_ace, то два туза по 11 — невозможно,
            # но на практике dealer_sum+11 <= 21 при usable_ace=True не случится
            new_usable_ace = True
        else:
            new_sum : int = dealer_sum + 1
            new_usable_ace = usable_ace
    else:
        new_sum : int = dealer_sum + card
        new_usable_ace = usable_ace

    # Если перебор, но был мягкий туз – превращаем его в 1
    if new_sum > 21 and new_usable_ace:
        new_sum -= 10
        new_usable_ace = False

    bust : bool = new_sum > 21
    return new_sum, new_usable_ace, bust


def get_all_states() -> list:
    """
    Генерирует список всех возможных состояний дилера (сумма, наличие мягкого туза).

    Используется как пространство состояний для value iteration.

    Returns:
        list[tuple]: Список кортежей (dealer_sum, usable_ace), где
            dealer_sum — от 2 до 21 включительно,
            usable_ace — True или False.
    """
    states : list = []
    for s in range(2, 22):          # от 2 до 21 включительно
        for ace in (False, True):
            states.append((s, ace))
    return states


def reward_stand(dealer_sum, player_sum) -> Literal[-1, 1, 0]:
    """
    Вычисляет награду для дилера, если он останавливается при заданных суммах.

    Args:
        dealer_sum (int): Сумма очков дилера.
        player_sum (int): Сумма очков игрока.

    Returns:
        int: 1 — дилер выиграл, 0 — ничья, -1 — дилер проиграл.

        Логика:
        - Если dealer_sum > 21 — дилер проигрывает (-1).
        - Если player_sum > 21 — дилер выигрывает (1).
        - Иначе сравниваются суммы: больше → 1, меньше → -1, равны → 0.
    """
    if dealer_sum > 21:
        # перебор дилера (хотя обычно он не вызывает stand при переборе)
        return -1
    if player_sum > 21:
        return 1                      # перебор игрока
    if dealer_sum > player_sum:
        return 1
    elif dealer_sum < player_sum:
        return -1
    else:
        return 0    
    

def value_iteration(player_sum, gamma=1.0, theta=1e-6) -> tuple[dict[Any, float], dict]:
    """
    Выполняет алгоритм value iteration для нахождения оптимальной стратегии дилера
    против заданной финальной суммы игрока.

    Состояния: (dealer_sum, usable_ace) для dealer_sum от 2 до 21.
    Действия: 'hit' (добрать карту) или 'stand' (остановиться).
    Переходы определяются функцией step и вероятностями CARD_PROB.
    Награда за stand — reward_stand, за hit — 0 (промежуточная), кроме случаев перебора (-1).

    Итерации продолжаются, пока максимальное изменение ценности (delta) не станет меньше theta.

    Args:
        player_sum (int): Финальная сумма очков игрока (от 2 до 21).
        gamma (float): Коэффициент дисконтирования (по умолчанию 1.0, так как эпизод конечен и цель не дисконтируется).
        theta (float): Порог сходимости для остановки итераций.

    Returns:
        tuple: (V, policy)
            V (dict): Словарь ценностей состояний {(dealer_sum, usable_ace): value}.
            policy (dict): Оптимальные действия для состояний: 'hit' или 'stand'.
    """
    states : list = get_all_states()

    # Инициализация ценности нулями
    V = {s: 0.0 for s in states}
    # policy пока пустой
    policy : dict = {}

    while True:
        delta = 0
        for s in states:
            dealer_sum, usable_ace = s
            # --- действие stand ---
            stand_value = reward_stand(dealer_sum, player_sum)

            # --- действие hit ---
            hit_value = 0.0
            for card, prob in CARD_PROB.items():
                new_sum, new_ace, bust = step(dealer_sum, usable_ace, card)
                if bust:
                    r = -1
                    hit_value += prob * r
                else:
                    hit_value += prob * V[(new_sum, new_ace)]

            # Лучшее действие и новая ценность состояния
            best_value = max(stand_value, hit_value)
            delta = max(delta, abs(best_value - V[s]))
            V[s] = best_value

            # Сохраняем лучшее действие
            if stand_value >= hit_value:
                policy[s] = 'stand'
            else:
                policy[s] = 'hit'

        if delta < theta:
            break

    return V, policy


def precompute_policies() -> dict:
    """
    Предрассчитывает оптимальные политики дилера для всех возможных сумм игрока (2-21).

    Для каждой player_sum вызывается value_iteration, результаты собираются в словарь.

    Returns:
        dict: policies[player_sum][(dealer_sum, usable_ace)] = 'hit'/'stand'.

    Используется при загрузке модуля для заполнения глобальной переменной DEALER_POLICIES.
    """
    policies : dict = {}
    for ps in range(2, 22):
        # можно выводить прогресс, но для скорости не обязательно
        _, policy = value_iteration(ps)
        policies[ps] = policy
    return policies


# Глобальная предрассчитанная таблица оптимальных действий дилера.

# Структура: DEALER_POLICIES[player_sum][(dealer_sum, usable_ace)] = 'hit' или 'stand'.

# Инициализируется при импорте модуля вызовом precompute_policies().
DEALER_POLICIES = precompute_policies()


def get_optimal_action(dealer_sum, usable_ace, player_sum) -> Any | Literal['stand', 'hit']:
    """
    Возвращает оптимальное действие дилера для заданного состояния и суммы игрока.

    Использует предрассчитанную таблицу DEALER_POLICIES. Предусмотрены защитные проверки:
    - Если player_sum > 21, действие 'stand'.
    - Если dealer_sum > 21, действие 'stand'.
    - Если player_sum < 2, действие 'stand'.
    - Если состояние не найдено в таблице, применяется fallback: 'hit' при dealer_sum < 17, иначе 'stand'.

    Args:
        dealer_sum (int): Текущая сумма очков дилера.
        usable_ace (bool): Наличие мягкого туза у дилера.
        player_sum (int): Финальная сумма очков игрока.

    Returns:
        str: 'hit' или 'stand'.
    """
    # Если игрок перебрал (player_sum > 21), дилер не должен ходить, но на всякий случай stand.
    if player_sum > 21:
        return 'stand'
    # Защита от некорректной суммы дилера
    if dealer_sum > 21:
        return 'stand'
    try:
        # Ищем политику для заданной суммы игрока; если сумма меньше 2 – stand
        if player_sum < 2:
            return 'stand'
        policy = DEALER_POLICIES[player_sum]
        # print(policy[(dealer_sum, usable_ace)])
        return policy[(dealer_sum, usable_ace)]
    except KeyError:
        return 'hit' if dealer_sum < 17 else 'stand'
    

if __name__ == "__main__":
    # Тест 1: 10 + туз = мягкие 21
    s, a, b = step(10, False, 11)
    assert s == 21 and a == True and b == False

    # Тест 2: мягкие 18 (A+7) + 8 = 16 жёсткие
    s, a, b = step(18, True, 8)
    assert s == 16 and a == False and b == False

    # Тест 3: жёсткие 12 + 10 = 22 перебор
    s, a, b = step(12, False, 10)
    assert s == 22 and a == False and b == True

    # ВАШ ТЕСТ: 20 (9+10+A=1) + туз = 21 (без перебора)
    s, a, b = step(20, False, 11)
    assert s == 21 and a == False and b == False

    print("Все тесты пройдены!")


    # Запускаем value iteration для суммы игрока 18
    V, policy = value_iteration(18)

    print("Примеры оптимальных действий для player_sum=18:")
    # Покажем несколько состояний
    examples = [(12, False), (16, False), (18, False),
                (18, True), (20, False), (21, False)]
    for s, ace in examples:
        act = policy.get((s, ace), '?')
        print(f"  Сумма {s:2d}, мягкий {'да' if ace else 'нет'}: {act}")

    # Проверим очевидный факт – на 21 всегда stand
    assert policy[(21, False)] == 'stand'
    assert policy[(21, True)] == 'stand'
    print("\nТесты пройдены!")


    # Демонстрация таблицы политик для нескольких сумм игрока
    test_sums = [15, 18, 21]
    for ps in test_sums:
        print(f"\n--- Игрок остановился на {ps} ---")
        print("Сумма дилера | Мягкий | Действие")
        for dealer_sum in (12, 13, 14, 15, 16, 17, 18, 20, 21):
            for ace in (False, True):
                act = get_optimal_action(dealer_sum, ace, ps)
                print(
                    f"     {dealer_sum:2d}       |   {'да' if ace else 'нет'}  |   {act}")

    # Простейшие проверки на логичность
    # Против 21 дилер всегда берёт, пока не 21 (или не перебор), кроме 21
    assert get_optimal_action(20, False, 21) == 'hit'
    assert get_optimal_action(21, False, 21) == 'stand'
    # Против 15 дилер с мягкими 18 добирает
    assert get_optimal_action(18, True, 15) == 'stand'
    # Жёсткие 17 против 15 – обычно stand
    assert get_optimal_action(17, False, 15) == 'stand'
    print("\nВсе проверки пройдены.")
