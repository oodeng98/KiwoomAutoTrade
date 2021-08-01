from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import DefaultDict, Deque, Union, overload


@dataclass
class StockExecution:
    """체결된 주문 정보"""
    sector_code: str  # 종목 코드
    price: int  # 주식 가격
    count: int  # 거래량
    dtime: datetime = field(default_factory=lambda: datetime.now())  # 거래 시각

    @property
    def amount(self) -> int:
        """총 거래금액"""
        return self.price*self.count


@dataclass
class StockOrder:
    """요청된 주문 정보"""
    sector_code: str  # 종목 코드
    price: int  # 주식 가격
    count: int  # 거래량
    dtime: datetime = field(default_factory=lambda: datetime.now())  # 거래 시각

    @property
    def amount(self) -> int:
        """총 거래금액"""
        return self.price*self.count


class Wallet:
    """내가 가진 주들의 모음"""

    stock_executions: DefaultDict[str, Deque[StockExecution]]
    stock_orders: DefaultDict[str, Deque[StockOrder]]

    def __init__(self) -> None:
        """내가 가진 주들을 기록할 새로운 `Wallet`객체를 생성함"""
        self.stock_executions = defaultdict(lambda: deque())
        # 체결 정보를 저장하는 딕셔너리.
        # 키는 종목 코드(문자열),
        # 값은 주식체결정보(StockExecution)의 큐(Queue)이다.

        self.stock_stock_order = defaultdict(lambda: deque())
        # 주문 정보를 저장하는 딕셔너리.
        # 키는 종목 코드(문자열),
        # 값은 요청된 주문 정보(StockOrder)의 큐(Queue)이다.

    def __contains__(self, item: Union[str, StockExecution]) -> bool:
        """주어진 종목코드 혹은 체결주문정보가 이 모음안에 있는가 확인

        ```python
        >>> wallet = Wallet()
        >>> '00010' in wallet
        False

        >>> stock_exec = StockExecution('00011', 1100, 3)
        >>> stock_exec in wallet
        False
        ```
        """
        if isinstance(item, StockExecution):
            return self.__contains__(item.sector_code)
        else:
            return item in self.stock_executions

    @overload
    def execute(self, sector_code: str, price: int, count: int) -> None:
        stock_exec = StockExecution(sector_code=sector_code,
                                    price=price,
                                    count=count)
        self.execute(stock_exec)

    @overload
    def execute(self, stock_exec: StockExecution) -> None:
        """새로운 주식체결 정보를 저장함

        Args:
            stock_exec: (StockExecution) 주식 체결 정보
        """
        self.stock_executions[stock_exec.sector_code].append(stock_exec)

    @overload
    def order(self, sector_code: str, price: int, count: int) -> None:
        stock_order = StockOrder(sector_code=sector_code,
                                 price=price,
                                 count=count)
        self.order(stock_order)

    @overload
    def order(self, stock_order: StockOrder) -> None:
        """새로운 거래를 주문함

        Args:
            stock_order: (StockOrder) 주식 주문 정보
        """
        self.stock_orders[stock_order.sector_code].append(stock_order)

    def profit(self, sector_code: str) -> int:
        """입력한 종목코드에 대해 구매한 총 수익을 반환

        *순수익이 아님.

        Args:
            sector_code: (str) 종목코드

        Return:
            해당 종목코드에서 얻은 총 수익
        """
        profit = 0
        for stock_exec in self.stock_executions[sector_code]:
            profit += stock_exec.amount
        return profit

    def outstanding(self, sector_code: str) -> int:
        """입력한 종목코드에 대한 미체결 수량

        Args:
            sector_code: (str) 종목코드

        Return:
            해당 종목코드의 미체결 수량
        """
        outstanding = 0
        for stock_order in self.stock_orders[sector_code]:
            outstanding += stock_order.amount
        return outstanding
