

from PyQt5.QtCore import QEventLoop

from bot.db import Database
from kiwoom import KiwoomOpenAPI


class AutoTradingBot(KiwoomOpenAPI):
    def __init__(self) -> None:
        super().__init__()

        self.db = Database()
        self._balance: int = 0

        # Login
        self.CommConnect()

        # Set Event Listners
        self.OCXconn.OnEventConnect.connect(self.OnEventConnect)
        self.OCXconn.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.OCXconn.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.OCXconn.OnReceiveChejanData.connect(self.OnReceiveChejanData)


    # Override
    def OnEventConnect(self, nErrCode: int) -> None:
        if nErrCode == 0:
            print('로그인 성공')
        else:
            print('로그인 실패')


    # Override
    def OnReceiveRealData(self, sJongmokCode: str, sRealType: str, sRealData: str) -> None:
        if sRealType != '주식체결':
            price = int(self.GetCommRealData(sJongmokCode, 10)) # 가격
            count = int(self.GetCommRealData(sJongmokCode, 15)) # 거래량




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
