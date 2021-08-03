from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import DefaultDict, Deque, Optional


@dataclass
class Settings:
    account_number: str # 계좌 번호
    verbose: bool # 출력 허용
    closing_dtime: datetime # 매매 종료 시각

    min_exec_amount: int # 최소 체결 금액
    max_allow_outstanding_t_delta: timedelta # 최대 미체결 허용 시간
    sector_limit: int # 종목별 투자 금액 한도



@dataclass
class StockExecution:
    """체결 주문 정보"""
    sector_code: str  # 종목 코드
    price: int  # 주식 가격
    quantity: int  # 거래량
    dtime: datetime = field(default_factory=lambda: datetime.now())  # 거래 시각

    @property
    def amount(self) -> int:
        """총 거래금액"""
        return self.price*self.quantity


@dataclass
class StockOrder:
    """주문 요청 정보"""
    sector_code: str  # 종목 코드
    price: int  # 주식 가격
    quantity: int  # 거래량
    id: str = field(default='') # 주문 번호
    dtime: datetime = field(default_factory=lambda: datetime.now())  # 거래 시각

    @property
    def amount(self) -> int:
        """총 거래금액"""
        return self.price*self.quantity


class StockChart:
    """주식 거래 기록 모음"""

    stock_executions: DefaultDict[str, Deque[StockExecution]]
    stock_orders: DefaultDict[str, Deque[StockOrder]] # 요청 중인 주문

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

    # def __contains__(self, item: Union[str, StockExecution]) -> bool:
    #     """주어진 종목코드 혹은 체결주문정보가 이 모음안에 있는가 확인

    #     ```python
    #     >>> wallet = Wallet()
    #     >>> '00010' in wallet
    #     False

    #     >>> stock_exec = StockExecution('00011', 1100, 3)
    #     >>> stock_exec in wallet
    #     False
    #     ```
    #     """
    #     if isinstance(item, StockOrder):
    #         return item.sector_code in self.stock_orders
    #     elif isinstance(item, StockExecution):
    #         return item.sector_code in self.stock_executions
    #     else:
    #         return item in self.stock_executions or item in self.stock_orders

    def execute(self, stock_exec: StockExecution) -> None:
        """새로운 주식체결 정보를 저장함

        Args:
            stock_exec: (StockExecution) 주식 체결 정보
        """
        self.stock_executions[stock_exec.sector_code].append(stock_exec)

    def order(self, stock_order: StockOrder) -> None:
        """새로운 거래를 주문함

        Args:
            stock_order: (StockOrder) 주식 주문 정보
        """
        self.stock_orders[stock_order.sector_code].append(stock_order)

    def profit(self, sector_code: Optional[str] = None) -> int:
        """지금까지 얻은 총 수익을 반환함.

        종목 코드를 입력한다면, 해당 종목에 한하여 수익을 계산함.
        (*순수익이 아님.)

        Args:
            sector_code: (str) 종목코드

        Return:
            해당 종목코드에서 얻은 총 수익
        """
        profit = 0
        if sector_code is None:
            for sector_code in self.stock_executions:
                for stock_exec in self.stock_executions[sector_code]:
                    profit += stock_exec.amount
        else:
            for stock_exec in self.stock_executions[sector_code]:
                profit += stock_exec.amount
        return profit

    def outstanding(self, sector_code: Optional[str] = None) -> int:
        """지금까지의 총 미체결 수량을 반환함.

        종목 코드를 입력한다면, 해당 종목에 한하여 미체결 수량을 계산함.

        Args:
            sector_code: (str) 종목코드

        Return:
            해당 종목코드의 미체결 수량
        """
        outstanding = 0
        if sector_code is None:
            for sector_code in self.stock_orders:
                for stock_order in self.stock_orders[sector_code]:
                    outstanding += stock_order.amount
        else:
            for stock_order in self.stock_orders[sector_code]:
                outstanding += stock_order.amount
        return outstanding
