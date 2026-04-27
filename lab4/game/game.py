'''
Основной игровой модуль Блэкджека.

Содержит класс BlackjackGame, управляющий игровым циклом: приём ставок, раздача карт,
ходы игрока и дилера (использующего DP-стратегию), определение победителя и 
обновление счёта игрока.
'''

from typing import Any, Literal
from constants import chips
from card_components import Card, Deck, Hand
from players import Player, Dealer
from account import Account
from dealer_dp import get_optimal_action
import time
import os


def clear_screen() -> None:
    """
    Очищает консоль для улучшения читаемости интерфейса.

    Поддерживает Windows (команда 'cls') и Unix-подобные системы (команда 'clear').
    Не принимает аргументов и не возвращает значений.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


class BlackjackGame:
    '''
    Основной класс, управляющий игрой в блэкджек.

    Инкапсулирует игровую логику: управление колодой, руками игрока и дилера,
    финансовым счётом, ставками и ходами согласно правилам с применением 
    оптимальной стратегии дилера на основе DP.

    Attributes:
        deck (Deck): Игровая колода.
        player (Player): Объект игрока.
        dealer (Dealer): Объект дилера.
        player_account (Account): Банковский счёт игрока.
        current_bet (int): Текущая ставка.
        player_hand (Hand): Текущая рука игрока.
        dealer_hand (Hand): Текущая рука дилера.
    '''

    def __init__(self, initial_balance=10000) -> None:
        '''
        Инициализирует новую игру блэкджека.

        Args:
            initial_balance (float): Начальный баланс счёта (по умолчанию 10000).
        '''
        self.deck = Deck()
        self.player = Player()
        self.dealer = Dealer()
        self.player_account = Account(initial_balance)
        self.current_bet : int = 0
        self.player_hand : Hand = None
        self.dealer_hand : Hand = None

    def place_bet(self) -> None:
        '''
        Запрашивает у игрока ставку в фишках казино и списывает сумму со счёта.

        Циклически выводит доступные фишки и текущий баланс, принимает ввод в формате
        '<количество> <цвет> ...' (например, '2 b 1 g').
        При успешном вводе устанавливает self.current_bet и вызывает withdraw у счёта.

        Raises:
            Никаких исключений не выбрасывается; ошибки ввода обрабатываются с выводом сообщения.
        '''
        while True:
            print("\nДоступные ставки:", chips["description"])
            print(f"Баланс: {self.player_account.get_balance()}")

            bet_input: str = input("\nВведите свою ставку, используя цвета фишек (например, " \
            "\"2 b 1 g\" на сумму 225 долларов).: ")
            total_bet : int = 0


            valid = True
            try:
                bet_parts = bet_input.lower().split()
                if len(bet_parts) % 2 != 0:
                    print("Ошибка: количество элементов должно быть чётным (чередуются число и цвет).")
                    continue
                for i in range(0, len(bet_parts), 2):
                    try:
                        count = int(bet_parts[i])
                    except ValueError:
                        print(f"Ошибка: '{bet_parts[i]}' не является целым числом.")
                        valid = False
                        break
                    color = bet_parts[i + 1]
                    if count <= 0:
                        print("Ошибка: количество фишек должно быть положительным.")
                        valid = False
                        break
                    if color not in chips:
                        print(
                            f"Ошибка: недопустимый цвет '{color}'. Доступные цвета: {', '.join(chips.keys())}.")
                        valid = False
                        break
                    total_bet += count * chips[color]
                if not valid:
                    continue
                if total_bet <= 0:
                    print("Ставка не может быть нулевой или отрицательной.")
                    continue

                # Используем числовое значение баланса напрямую
                if total_bet <= self.player_account.get_balance():
                    self.current_bet = total_bet
                    # withdraw при успехе возвращает None, при ошибке — строку
                    error = self.player_account.withdraw(total_bet)
                    if error is not None:
                        print(f"Ошибка списания средств: {error}")
                        continue
                    print(f"\nСтавка принята: ${total_bet}")
                    break
                else:
                    print("Недостаточно средств!")
            except Exception as e:
                print(f"Непредвиденная ошибка: {e}. Пожалуйста, попробуйте снова.")
                        
    def deal_initial_cards(self) -> None:
        '''
        Перемешивает колоду и раздаёт начальные карты: две игроку и две дилеру,
        чередуя раздачу (игрок, дилер, игрок, дилер).
        '''
        self.deck.shuffle()
        self.player_hand = Hand()
        self.dealer_hand = Hand()

        # Deal cards alternately
        self.player_hand.add_card(self.deck.deal_one())
        self.dealer_hand.add_card(self.deck.deal_one())
        self.player_hand.add_card(self.deck.deal_one())
        self.dealer_hand.add_card(self.deck.deal_one())

    def player_turn(self) -> None:
        '''
        Обрабатывает ход игрока: предлагает действия hit, stand, double.

        При каждом действии обновляет состояние руки и отображает его.
        - hit: добавляет карту, проверяет на блэкджек (21) и перебор.
        - double: удваивает ставку, добавляет одну карту (только на двух первых картах
        и при достаточном балансе). Завершает ход.
        - stand: завершает ход игрока.

        При некорректном вводе выводит сообщение об ошибке и ожидает нового действия.
        '''
        while True:
            self.display_game_state(
                hide_dealer=True, message="Your move: (h)it / (s)tand / (d)ouble")
            action : str = input("> ").lower()

            if action in ('h', 'hit'):
                self.player_hand.add_card(self.deck.deal_one())
                if self.player_hand.value == 21:
                    self.display_game_state(hide_dealer=True, message="БЛЭКДЖЕК!")
                    time.sleep(2)
                    return
                if self.player_hand.value > 21:
                    self.display_game_state(hide_dealer=True, message="Проиграл!")
                    time.sleep(1.5)
                    return

            elif action in ('d', 'double'):
                if len(self.player_hand.cards) == 2:
                    balance = float(
                        self.player_account.get_balance().replace('$', ''))
                    if self.current_bet <= balance:
                        self.player_account.withdraw(self.current_bet)
                        self.current_bet *= 2
                        self.player_hand.add_card(self.deck.deal_one())
                        self.display_game_state(hide_dealer=True,
                                                message=f"Дабл! Ставка: {self.current_bet}. Итоговые карты:")
                        time.sleep(2)
                        return
                    else:
                        self.display_game_state(
                            hide_dealer=True, message="Недостаточно средств для удвоения суммы!")
                        time.sleep(1)
                else:
                    self.display_game_state(
                        hide_dealer=True, message="Можно удвоить ставку только при первой раздаче!")
                    time.sleep(1)

            elif action in ('s', 'stand'):
                return
            else:
                self.display_game_state(
                    hide_dealer=True, message="Неверный выбор! Используйте h/s/d")
                time.sleep(0.5)

    def dealer_turn(self) -> None:
        """
        Выполняет ход дилера согласно оптимальной стратегии, вычисленной с помощью DP.

        Сначала показывает вторую карту дилера (ранее скрытую).
        Затем циклически запрашивает действие у get_optimal_action на основе 
        текущей суммы дилера, наличия мягкого туза и финальной суммы игрока.
        Действие 'hit' добавляет карту, 'stand' останавливает ход.
        Перебор приводит к остановке с сообщением.
        Каждое действие сопровождается визуальным обновлением состояния.
        """
        player_final : int = self.player_hand.value

        # Показать вторую карту дилера
        self.display_game_state(
            hide_dealer=False, message="Дилер раскрывает вторую карту.")
        time.sleep(1)

        while True:
            dealer_sum : int = self.dealer_hand.value
            if dealer_sum > 21:
                self.display_game_state(hide_dealer=False, message="Дилер проиграл!")
                time.sleep(1.5)
                break

            soft : bool = self.dealer_hand.usable_ace
            action: Any | Literal['stand', 'hit'] = get_optimal_action(
                dealer_sum, soft, player_final)

            if action == 'hit':
                self.display_game_state(
                    hide_dealer=False, message="[DP] Дилер решает взять")
                time.sleep(1)
                card : Card = self.deck.deal_one()      # у вас, вероятно, метод deal_one()
                self.dealer_hand.add_card(card)
                self.display_game_state(
                    hide_dealer=False, message=f"Дилер получает карту: {card.rank, card.value}")
                time.sleep(1)
            else:
                self.display_game_state(
                    hide_dealer=False, message="[DP] Дилер решает остановиться")
                time.sleep(1)
                break

    def determine_winner(self) -> bool | None:
        '''
        Определяет победителя раунда на основе итоговых сумм.

        Сравнивает значения рук игрока и дилера с учётом переборов:
        - Игрок с перебором → победа дилера.
        - Дилер с перебором → победа игрока, выплата 2 * ставка.
        - Игрок > дилер → победа игрока, выплата 2 * ставка.
        - Игрок < дилер → победа дилера.
        - Равные суммы → ничья (push), ставка возвращается игроку.

        Returns:
            bool or None: True — игрок выиграл, False — проиграл, None — ничья.
        '''
        player_value : int = self.player_hand.value
        dealer_value : int = self.dealer_hand.value

        if player_value > 21:
            msg = "Ты проиграл! Дилер выиграл!"
            result = False
        elif dealer_value > 21:
            msg = "Дилер проиграл! Ты выиграл!"
            self.player_account.deposit(self.current_bet * 2)
            result = True
        elif player_value > dealer_value:
            msg = "Ты выиграл!"
            self.player_account.deposit(self.current_bet * 2)
            result = True
        elif dealer_value > player_value:
            msg = "Дилер выиграл!"
            result = False
        else:
            msg = "Ничья!"
            self.player_account.deposit(self.current_bet)
            result = None

        self.display_game_state(hide_dealer=False, message=msg)
        time.sleep(2)
        return result

    def play_again(self) -> bool | None:
        '''
        Спрашивает игрока о желании сыграть ещё раз.

        Принимает ответы 'y'/'yes' или 'n'/'no', нечувствительны к регистру.
        При положительном ответе возвращает True, иначе выводит финальный баланс и прощается.

        Returns:
            bool: True — продолжить игру, False — завершить.
        '''
        yes = {'yes', 'y'}
        no = {'no', 'n'}
        while True:
            replay = input(
                'Хотите сыграть ещё раз? ([y]es / [n]o): ').strip().lower()
            if len(replay) > 10:
                print("Слишком длинный ввод. Пожалуйста, введите 'y' или 'n'.")
                continue
            if replay in yes:
                return True
            elif replay in no:
                print(f"\nИтоговый баланс: ${self.player_account.get_balance()}")
                return False
            else:
                print("Пожалуйста, ответьте 'y' (да) или 'n' (нет).")

    def play(self):
        '''
        Запускает основной игровой цикл.

        Пока игрок хочет играть и имеет средства, повторяет:
        - Приветствие и приём ставки.
        - Раздачу карт.
        - Ход игрока.
        - Ход дилера (если игрок не перебрал).
        - Определение победителя.
        - Предложение сыграть снова.

        При обнулении баланса игра завершается принудительно.
        Если в колоде осталось менее 15 карт, колода пересоздаётся (имитация новой).
        '''
        game_on = True

        while game_on:
            # Start new round
            print("\n" + "=" * 50)
            print(f"Занимайте свое место!")

            self.place_bet()

            self.deal_initial_cards()

            self.player_turn()
            if self.player_hand.value <= 21:
                self.dealer_turn()
            self.determine_winner()

            if self.player_account.get_balance() == "$ 0":
                print(f"Вы не можете больше сделать ставки (баланс: {self.player_account.get_balance()})!")
                break

            game_on : bool = self.play_again()
            if not game_on:
                break

            # Reset deck if running low
            if len(self.deck.all_cards) < 15:
                self.deck = Deck()

    def display_game_state(self, hide_dealer=True, message="") -> None:
        """
        Очищает экран и выводит текущее состояние игры.

        Показывает баланс и ставку, карты игрока и его сумму, карты дилера
        (с возможностью скрыть первую карту) и его сумму (если не скрыта).
        В нижней части выводит переданное сообщение.

        Args:
            hide_dealer (bool): Скрывать ли первую карту дилера (рубашкой).
            message (str): Сообщение, отображаемое под игровым полем.
        """
        clear_screen()
        bal = self.player_account.get_balance()
        print(f"Баланс: {bal}   Ставка: {self.current_bet}\n")

        print("Ваши карты:")
        self.player_hand.print_hand()
        print(f"Сумма: {self.player_hand.value}")

        print("\Карты дилера:")
        self.dealer_hand.print_hand(hide_first=hide_dealer)
        if not hide_dealer:
            print(f"Сумма: {self.dealer_hand.value}")

        print("-" * 30)
        if message:
            print(message)
