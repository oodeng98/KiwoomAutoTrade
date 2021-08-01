

from datetime import date, datetime
from typing import Optional, Union

from PyQt5.QtCore import QEventLoop

from bot.db import Database
from kiwoom import KiwoomOpenAPI


class AutoTradingBot(KiwoomOpenAPI):
    def __init__(self, closing: Optional[date] = None) -> None:
        """자동 주식 매매 봇을 실행시킵니다.

        Args:
            closing: (Optional; datetime) 주식시장이 닫히는 시간. 이 시간에 맞춰 주식 자동매매가 종료됩니다.
        """
        super().__init__()

        self.db = Database()

        self._balance: int = 0
        self.closing: Union[date, None] = closing

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
        self.event_loop = QEventLoop()
        self.event_loop.exec()

    def stop(self, *args, **kwargs) -> None:
        """자동 주식 매매 봇을 정지시킵니다."""
        self.event_loop.exit()

    # Override

    def OnEventConnect(self, nErrCode: int) -> None:
        if nErrCode == 0:
            print('로그인 성공')
        else:
            print('로그인 실패')

    # Override

    def OnReceiveRealData(self, sJongmokCode: str, sRealType: str, sRealData: str) -> None:
        if self.closing is not None:
            # 현재 시간이 self.closing에 지정된 시간보다 이후이면 프로그램 종료
            now = datetime.now()
            if now.toordinal() >= self.closing.toordinal():
                self.stop()
                return
        if sRealType != '주식체결':
            self.on_stock_execution(sJongmokCode, sRealType, sRealData)

    def on_stock_execution(self, sJongmokCode: str, sRealType: str, sRealData: str) -> None:
        """주식 체결 될 때마다 실행 될 함수

        `OnReceiveRealData()`함수에서 이 함수가 호출 됨.
        """
        price = int(self.GetCommRealData(sJongmokCode, 10))  # 가격
        count = int(self.GetCommRealData(sJongmokCode, 15))  # 거래량

    @property
    def balance(self) -> int:
        """현재 계좌잔고"""
        return self._balance

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        order_number = int(self.get_chejan_data(FID.StockQuote.order_number))
        if not order_number:
            return
        sector_code = int(self.get_chejan_data(FID.OrderExecution.sector_code))
        sector_name = self.get_chejan_data(FID.CreditBalance.sector_name)
        outstanding = int(self.get_chejan_data(FID.OrderExecution.outstanding))
        if not outstanding:
            order_classification = self.get_chejan_data(
                FID.OrderExecution.order_classification)
            # XXX(oodeng98, Hepheir) 이 부분부터는 태완이와 함께 작업해야 할 듯
            if order_classification.startswith('+매수'):
                pass
            elif order_classification.startswith('-매도'):
                pass

        return super()._receive_chejan_data(gubun, item_cnt, fid_list)
