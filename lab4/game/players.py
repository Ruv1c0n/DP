'''
Определяет классы участников игры: базовый Player и его наследник Dealer.

Player хранит имя и набор карт, полученных в ходе раздачи.
Dealer наследует Player без дополнительной логики — поведение дилера определяется
стратегией из модуля dealer_dp.
'''

from typing import List
from card_components import Card


class Player:
    '''
    Игрок в блэкджеке.

    Содержит имя игрока и список карт, находящихся у него в руке.
    Поддерживает добавление карт (по одной или списком) и сброс руки.
    '''

    def __init__(self):
        '''
        Инициализирует игрока с пустой рукой.
        '''
        self.all_cards: List[Card] = []
        
    def reset_hand(self):
        '''
        Сбрасывает руку игрока, очищая список карт.

        Обнуляет all_cards в пустой список.
        '''
        self.all_cards = []
    
    def add_cards(self, new_cards):
        '''
        Добавляет карты в руку игрока.

        Поддерживает как одиночную карту, так и список карт.
        Если передана одна карта (не список), она добавляется индивидуально.

        Args:
            new_cards (Card или list[Card]): Карта или список карт для добавления.
        '''
        if isinstance(new_cards, list):
            self.all_cards.extend(new_cards)
        else:
            self.all_cards.append(new_cards)


class Dealer(Player):
    '''
    Дилер в блэкджеке; наследует класс Player.

    Не добавляет новых атрибутов или методов. Стратегия дилера задаётся
    внешней функцией get_optimal_action из dealer_dp.
    '''

    pass