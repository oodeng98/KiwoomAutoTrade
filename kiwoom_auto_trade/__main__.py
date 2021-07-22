import json
import sys

from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QApplication

from kiwoom_auto_trade.api import KiwoomOpenAPI
from kiwoom_auto_trade.db import Database


class KiwoomAutoTrade(KiwoomOpenAPI):
    def __init__(self):
        self.db = Database()
        super().__init__()


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
