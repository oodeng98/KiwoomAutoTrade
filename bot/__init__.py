from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict

from PyQt5.QtCore import QEventLoop

from bot.classes import StockChart, StockExecution, StockOrder, Settings
from bot.db import Database
from kiwoom import KiwoomOpenAPI


_SectorCode = str


class AutoTradingBot(KiwoomOpenAPI):
    def __init__(self, settings: Settings) -> None:
        """자동 주식 매매 봇을 실행시킵니다."""

        self.settings: Settings = settings

        super().__init__()

        self.db = Database()
        self.event_loop = QEventLoop()

        self.limit:Dict[_SectorCode, int] = defaultdict(lambda: self.settings.sector_limit)
        self.my_chart = StockChart() # 내 거래 기록 저장
        self.market_chart = StockChart() # 시장에서의 거래 기록 저장

        self.login()
        self.start()

    def login(self) -> None:
        """키움 증권 API로 로그인"""
        self.CommConnect()

    def start(self) -> None:
        """자동 주식 매매 봇을 시작합니다."""
        # Set Event Listners
        self.OCXconn.OnEventConnect.connect(self.OnEventConnect)
        self.OCXconn.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.OCXconn.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.OCXconn.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        # Start event
        self.event_loop.exec()

    def stop(self, *args, **kwargs) -> None:
        """자동 주식 매매 봇을 정지시킵니다."""
        self.event_loop.exit()

    def print(self, *values: object, sep: str | None = ' ', end: str | None = '\n') -> None:
        """설정에서 verbose 옵션이 활성화 되어있으면, 메세지를 출력."""
        if not self.settings.verbose:
            return
        print(*values, sep=sep, end=end)

    # Override

    def OnEventConnect(self, nErrCode: int) -> None:
        if nErrCode == 0:
            print('로그인 성공')
        else:
            print('로그인 실패')

    # Override

    def OnReceiveRealData(self, sJongmokCode: str, sRealType: str, sRealData: str) -> None:
        # 현재 시간이 self.closing에 지정된 시간보다 이후이면
        # 프로그램 종료
        now = datetime.now()
        if now.toordinal() >= self.settings.closing_dtime.toordinal():
            self.stop()
            return

        # XXX

        if sRealType == '주식체결':
            price = int(self.GetCommRealData(sJongmokCode, 10))  # 가격
            share = int(self.GetCommRealData(sJongmokCode, 15))  # 거래량
            stock_exec = StockExecution(sector_code=sJongmokCode,
                                        price=price,
                                        quantity=share)
            self.on_stock_execution(stock_exec)

    # Override

    def OnReceiveChejanData(self, sGubun: str, nItemCnt: str, sFidList: str) -> None:
        order = StockOrder(
            id=self.GetChejanData(9203), # 주문번호
            sector_code=self.GetChejanData(9001),
            price=int(self.GetChejanData(901)),
            quantity=int(self.GetChejanData(900))
        )

        # XXX

        total_outstanding = int(self.GetChejanData(902)) # 미체결수량
        if total_outstanding:
            pass

        self.my_chart.order(order)

        gubun = self.GetChejanData(905)
        if gubun == '+매수':
            self.SendOrder(
                sRQName="send_order_rq",
                sScreenNo="8020",
                sAccNo=self.settings.account_number,
                nOrderType=2,
                sCode=order.sector_code,
                nQty=order.quantity,
                nPrice=order.price,
                sHogaGb="00",
                sOrgOrderNo="")
        elif gubun == '-매도':
            pass


    def on_stock_execution(self, stock_exec: StockExecution) -> None:
        """데이터를 받아옴과 동시에 조건을 만족하면 주식을 구매, 판매한다.

        주식 체결 될 때마다 실행 될 함수로,
        `OnReceiveRealData()` 함수에서 호출되어 실행된다.

        Args:
            stock_exec: (StockExecution) 체결된 거래 정보
        """
        # 종목코드를 자주 사용할 것임으로, 별도의 변수로 할당함.
        sector_code = stock_exec.sector_code

        # XXX

        #
        if self.market_chart.stock_executions[sector_code]:
            if self.market_chart.profit(sector_code) == 0:
                return

        # 거래금액이 임계치를 넘지 않으면 무시함
        if stock_exec.amount < self.settings.min_exec_amount:
            return

        if self.market_chart.stock_orders[sector_code]:
            stock_order = self.market_chart.stock_orders[sector_code][0]

            stock_t_delta = datetime.now() - stock_order.dtime

            # 20초가 지났음에도 미체결수량이 0이 아니면 남은 수량 주문취소
            if stock_t_delta > self.settings.max_allow_outstanding_t_delta:
                error_code = self.SendOrder(
                    sRQName="send_order_rq",
                    sScreenNo="8010",
                    sAccNo=self.settings.account_number,
                    nOrderType=3,
                    sCode=sector_code,
                    nQty=self.market_chart.outstanding(sector_code),
                    nPrice=0,
                    sHogaGb='03',
                    sOrgOrderNo='')
                if error_code == KiwoomOpenAPI.OP_ERR_FAIL:
                    # 매수 취소에 실패한 경우 처리
                    self.print('매수 취소에 실패함')
                    pass

                if self.is_buyable(sector_code):
                    pass

        exec = StockExecution(
            sector_code=sector_code,
            price=0,
            quantity=1
        )
        self.market_chart.execute(exec)

    def is_buyable(self, sector_code: str) -> bool:
        """내가 지정한 매수 조건을 만족하는지 검사"""
        # XXX

        upper_bound = max(self.market_chart.stock_executions)
        return False