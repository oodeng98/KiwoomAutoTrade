from kiwoom_auto_trade.api import KiwoomOpenAPI
from kiwoom_auto_trade.db import Database


class KiwoomAutoTrade(KiwoomOpenAPI):
    def __init__(self):
        self.db = Database()
        super().__init__()
