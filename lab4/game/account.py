import time
from typing import Literal
import pandas as pd


class Account:
    '''
    Класс для управления банковским счётом игрока.

    Хранит информацию о владельце, текущем балансе и истории транзакций.
    Транзакции фиксируются в pandas.DataFrame с колонками 'category' и 'amount'.
    '''

    def __init__(self, balance) -> None:
        '''
        Инициализирует счёт игрока.

        Args:
            balance (float): Начальный баланс счёта.

        Attributes:
            balance (float): Текущий баланс.
            transactions (pd.DataFrame): История пополнений и снятий; изначально пустой DataFrame.
        '''
        self.balance = balance
        self.transactions = pd.DataFrame(columns=['category', 'amount'])

    def __str__(self) -> str:
        '''
        Возвращает строковое представление счёта с текущим балансом.

        Returns:
            str: Информация о владельце и балансе в отформатированном виде.
        '''
        return f"Текущий баланс: $ {self.balance}"
    
    def deposit(self, amount) -> str | None:
        '''
        Вносит указанную сумму на счёт.

        Если аргумент не является числом, операция отклоняется, и метод возвращает строку с ошибкой.
        В случае успеха сумма добавляется к балансу, запись о транзакции добавляется в историю,
        и выводится сообщение о принятом депозите.

        Args:
            amount (int или float): Сумма пополнения. Должна быть числовым типом.

        Returns:
            str или None: Если тип amount некорректен, возвращает сообщение об ошибке;
                        иначе None (вывод информации происходит через print).
        '''
        if not isinstance(amount, (int, float)):
            return "Сумма пополнения должна быть числом."
        if amount <= 0:
            return "Сумма пополнения должна быть положительной."
        self.balance += amount
        new_row = pd.DataFrame({'category': ['Deposit'], 'amount': [amount]})
        self.transactions = pd.concat(
            [self.transactions, new_row], ignore_index=True)
        # Никаких выводов на экран – логика отображения в игровом модуле
        return None
    
    def withdraw(self, amount) -> str | None:
        '''
        Снимает указанную сумму со счёта.

        Если аргумент не является числом, возвращает сообщение об ошибке.
        Если запрашиваемая сумма превышает доступный баланс, операция отклоняется.
        При успешном снятии сумма вычитается из баланса, а транзакция записывается в историю
        с отрицательным значением. В консоль выводится подтверждение и актуальный баланс.

        Args:
            amount (int или float): Сумма для снятия.

        Returns:
            str или None: Сообщение об ошибке при некорректном вводе или недостатке средств,
                        иначе None.
        '''
        if not isinstance(amount, (int, float)):
            return "Сумма снятия должна быть числом."
        if amount <= 0:
            return "Сумма снятия должна быть положительной."
        if amount > self.balance:
            return f"Недостаточно средств (доступно: ${self.balance})."
        self.balance -= amount
        new_row = pd.DataFrame({'category': ['Withdraw'], 'amount': [-amount]})
        self.transactions = pd.concat(
            [self.transactions, new_row], ignore_index=True)
        return None

    def get_transactions(self) -> pd.DataFrame:
        '''
        Возвращает DataFrame со всей историей транзакций.

        Returns:
            pd.DataFrame: Таблица с колонками 'category' и 'amount', где каждая строка –
                        одна операция (пополнение или снятие).
        '''
        return self.transactions
    
    def get_balance(self) -> float:
        '''
        Возвращает текущий баланс.

        Returns:
            str: Строка вида "$ <баланс>".
        '''
        return self.balance
