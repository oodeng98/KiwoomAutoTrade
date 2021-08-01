from sys import argv
import json

from PyQt5.QtWidgets import QApplication

from bot import AutoTradingBot


def main():
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.loads(f.read())

    summary = {
        '시작금액': '',
        '종료금액': '',
    }

    app = QApplication(argv)
    bot = AutoTradingBot()

    # initial_capital = bot.balance  # 초기자본

    # print('시작금액:', bot.balance)
    # print('종료금액:', bot.balance)

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
