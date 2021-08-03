from datetime import datetime, timedelta
from sys import argv
import json

from PyQt5.QtWidgets import QApplication

from bot import AutoTradingBot
from bot.classes import Settings


def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())

    now = datetime.now()
    settings = Settings(
        account_number=config["계좌_번호"],
        verbose=config["출력_허용"],
        closing_dtime=datetime(
            year=now.year, month=now.month, day=now.day,
            hour=15, minute=25, second=0, microsecond=0),
        min_exec_amount=100*10000,
        max_allow_outstanding_t_delta=timedelta(seconds=20),
        sector_limit=1000000
    )


    app = QApplication(argv)
    bot = AutoTradingBot(settings=settings)

    # initial_capital = bot.balance  # 초기자본

    total_profit = bot.wallet.profit()
    total_outstanding = bot.wallet.outstanding()

    # try:
    #     summary['시작금액'] = bot.d2_deposit

    #     bot.set_input_value("계좌번호", config["계좌번호"])
    #     bot.event_loop = QEventLoop()
    #     bot.event_loop.exec()
    # except Exception:
    #     pass
    # finally:
    #     summary['종료금액'] = bot.d2_deposit


if __name__ == '__main__':
    main()
