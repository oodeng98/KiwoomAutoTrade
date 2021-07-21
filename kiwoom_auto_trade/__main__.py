from kiwoom_auto_trade.api import KiwoomAPI
from kiwoom_auto_trade.db import Database


class KiwoomAutoTrade(KiwoomAPI):
    def __init__(self):
        self.db = Database()
        super().__init__()
