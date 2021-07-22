import json
import sys

from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QApplication

from kiwoom_auto_trade.api import FID
from kiwoom_auto_trade.api import KiwoomOpenAPI
from kiwoom_auto_trade.db import Database


class KiwoomAutoTrade(KiwoomOpenAPI):
    def __init__(self):
        self.db = Database()
        super().__init__()


    def get_chejan_data(self, fid) -> str:
        """체결 잔고 데이터를 가져옵니다.

        '체'결 '잔'고 -> CHE JAN 깔깔
        """
        return super().get_chejan_data(fid).strip()


    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        order_number = int(self.get_chejan_data(FID.StockQuote.order_number))
        if not order_number:
            return
        sector_code = int(self.get_chejan_data(FID.OrderExecution.sector_code))
        sector_name = self.get_chejan_data(FID.CreditBalance.sector_name)
        outstanding = int(self.get_chejan_data(FID.OrderExecution.outstanding))
        if not outstanding:
            order_classification = self.get_chejan_data(FID.OrderExecution.order_classification)
            #XXX(oodeng98, Hepheir) 이 부분부터는 태완이와 함께 작업해야 할 듯
            if order_classification.startswith('+매수'):
                pass
            elif order_classification.startswith('-매도'):
                pass

        return super()._receive_chejan_data(gubun, item_cnt, fid_list)


if __name__ == "__main__":
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())

    summary = {
        '시작금액': '',
        '종료금액': '',
    }

    app = QApplication(sys.argv)

    kat = KiwoomAutoTrade()
    kat.comm_connect()

    try:
        summary['시작금액'] = kat.d2_deposit

        kat.set_input_value("계좌번호", config["계좌번호"])
        kat.event_loop = QEventLoop()
        kat.event_loop.exec()
    except Exception:
        pass
    finally:
        summary['종료금액'] = kat.d2_deposit
