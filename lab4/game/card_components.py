from typing import List
from random import shuffle
from constants import suits, ranks, values, rank_viz, suit_viz


class Card:
    '''
    Представляет игральную карту с мастью, рангом, числовым значением и символами для визуализации.

    Attributes:
        suit (str): Масть карты (из constants.suits).
        rank (str): Ранг карты (из constants.ranks).
        value (int): Числовое значение согласно словарю values (2..14).
        rank_viz (str): Символ ранга для отображения (2-10, J, Q, K, A).
        suit_viz (str): Символ масти (♥, ♦, ♠, ♣).
    '''

    def __init__(self, suit: str, rank: str) -> None:
        '''
        Инициализирует карту с заданными мастью и рангом.

        Args:
            suit (str): Масть карты (например, 'Hearts').
            rank (str): Ранг карты (например, 'Ace').

        Значения для визуализации и числового значения берутся из глобальных констант.
        '''
        self.suit = suit
        self.rank = rank
        self.value : int = values[rank]
        self.rank_viz : str = rank_viz[ranks.index(rank)]
        self.suit_viz : str = suit_viz[suits.index(suit)]
        
    def get_blackjack_value(self, current_total=0) -> int:
        '''
        Возвращает значение карты в блэкджеке с учётом текущей суммы очков игрока (для правильной оценки туза).

        Args:
            current_total (int): Текущая сумма очков руки. По умолчанию 0.

        Returns:
            int: Номинал карты в блэкджеке:
                - Для туза: 11, если current_total + 11 <= 21, иначе 1.
                - Для карт с рангом J, Q, K и десяток: 10.
                - Для остальных: числовое значение (value), но не более 10 (для 2-9 value и так ≤10).
        '''
        if self.rank == 'Ace':
            return 11 if current_total + 11 <= 21 else 1
        return min(10, self.value)


class Deck:
    '''
    Колода из 52 игральных карт (все комбинации мастей и рангов).

    При создании генерируется полный набор карт. Поддерживает перемешивание и раздачу карт по одной.
    '''

    def __init__(self) -> None:
        '''
        Инициализирует колоду, создавая список из 52 карт (все комбинации suits × ranks).
        '''
        self.all_cards = [Card(suit, rank) for suit in suits for rank in ranks]
                
    def shuffle(self) -> None:
        '''
        Перемешивает карты в колоде, используя random.shuffle.

        Вызов shuffle на пустой колоде допустим, но последующая раздача приведёт к ошибке.
        '''
        shuffle(self.all_cards)
        
    def deal_one(self) -> Card:
        '''
        Извлекает и возвращает верхнюю карту из колоды.

        Returns:
            Card: Последняя карта в списке all_cards.

        Raises:
            ValueError: Если колода пуста и раздача невозможна.
        '''
        if not self.all_cards:
            raise ValueError('No cards left in the deck!')
        return self.all_cards.pop()


class Hand:
    '''
    Представляет руку игрока или дилера в блэкджеке.

    Управляет картами, вычисляет сумму очков с корректировкой тузов и определяет наличие «мягкого» туза.

    Attributes:
        cards (list[Card]): Карты в руке.
        value (int): Текущая сумма очков.
        aces (int): Количество тузов, учитываемых как 11.
    '''

    def __init__(self) -> None:
        '''
        Инициализирует пустую руку: карт нет, сумма 0, мягких тузов нет.
        '''
        self.cards = []
        self.value = 0
        self.aces = 0
        
    def add_card(self, card) -> None:
        '''
        Добавляет карту в руку и пересчитывает сумму очков.

        Args:
            card (Card): Карта для добавления.
        '''
        self.cards.append(card)
        self.calculate_value()
    
    def calculate_value(self) -> None:
        '''
        Вычисляет сумму очков руки по правилам блэкджека.

        Суммирует значения всех карт, временно считая тузы за 11. 
        Если сумма превышает 21 и есть тузы, учтённые как 11, последовательно 
        превращает их в 1 (уменьшая сумму на 10), пока не будет достигнуто 
        значение ≤ 21 или не закончатся мягкие тузы. 
        Обновляет self.value и self.aces.
        '''
        self.value = 0
        self.aces = 0
        
        for card in self.cards:
            if card.rank == 'Ace':
                self.aces += 1
            self.value += card.get_blackjack_value()
        
        while self.value > 21 and self.aces:
            self.value -= 10
            self.aces -= 1

    @property
    def usable_ace(self) -> bool:
        """
        Возвращает True, если в руке есть хотя бы один туз, учитываемый как 11 (мягкий туз).

        Returns:
            bool: Наличие мягкого туза.
        """
        return self.aces > 0
    
    def print_hand(self, hide_first=False) -> None:
        '''
        Выводит в консоль визуальное представление карт руки с использованием символов псевдографики.

        Args:
            hide_first (bool): Если True, первая карта отображается рубашкой вверх (***). 
                                Используется для скрытия первой карты дилера.
        '''
        for i, card in enumerate(self.cards):
            if i == 0 and hide_first:
                print("+-------+")
                print("|  ***  |")
                print("|  ***  |")
                print("|  ***  |")
                print("+-------+")
            else:
                print("+-------+")
                print(f"| {card.rank_viz.ljust(2)}    |")
                print(f"|   {card.suit_viz}   |")
                print(f"|    {card.rank_viz.rjust(2)} |")
                print("+-------+")