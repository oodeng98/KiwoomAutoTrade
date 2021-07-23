import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import pandas as pd
import sqlite3
import datetime
import time
import os
from data_test import *

TR_REQ_TIME_INTERVAL = 0.2

TIME_FACTOR = 6
BUY_FACTOR = 5
SELL_FACTOR1 = 5
SELL_FACTOR2 = 2
STANDARD = 10000000
LIMIT = 5  # 조각의 개수를 제한해줘야 한다, 조각당 백만원은 있어야 할듯
MONEY = 1000000
ACCOUNT_NUM = "8000927211"


class Kiwoom(QAxWidget):  # 키움증권의 OpenAPI 가 제공하는 메서드를 호출하기 위해서 QAxWidget 클래스의 인스턴스 필요
    def __init__(self):
        super().__init__()
        self.save_data = {}

        times = datetime.datetime.today()
        self.today = '-'.join([times.strftime('%Y'), times.strftime('%m'), times.strftime('%d')])
        self.TICKS_PER_SAVE = 100000
        self.save_tick_cnt = 0
        self._create_kiwoom_instance()
        self._set_signal_slots()
        self.con = sqlite3.connect("c:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + self.today + '.db')
        self.stock = {}
        self.buy_list = []

    def _create_kiwoom_instance(self):  # _를 붙여준 이유는 이 메서드가 주로 Kiwoom 메서드에서 호출되기 때문
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")  # 무슨 역할인지 모르겠음

    def _set_signal_slots(self):  # 서버에서 발생한 이벤트(signal)와 이를 처리할 메서드(slot)을 연결
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveRealData.connect(self._receive_real_data)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.OnReceiveChejanData.connect(self._receive_chejan_data)  # 시그널과 슬롯 연결

    def comm_connect(self):
        self.dynamicCall("CommConnect()")  # API 로그인
        self.login_event_loop = QEventLoop()  # PyQt 를 통해 GUI 형태로 프로그램을 만들지 않아서 이벤트 루프를 생성
        self.login_event_loop.exec_()  # OnEventConnect 이벤트가 발생하기 전까지 프로그램이 종료되지 않음

    def _event_connect(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("disconnected")

        self.login_event_loop.exit()  # 이벤트 루프 종료

    def get_code_list_by_market(self, market):  # 종목 코드를 가져오는 메서드
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)  # dynamicCall 로 Open API 가 제공하는
        # GetCodeListByMarket 메서드를 호출, 아마 dynamicCall 이 C++을 위한 메서드를 가져오는 방법이 아닌가 싶은데
        code_list = code_list.split(';')  # 리스트가 ; 로 구분된다
        return code_list[:-1]  # 0: 장내, 10: 코스닥

    def get_master_code_name(self, code):  # 종목 코드로 한글 종목명을 얻어옴
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_connect_state(self):  # 연결된 상태인지 확인
        ret = self.dynamicCall("GetConnectState()")
        return ret

    def set_input_value(self, id, value):  # 마찬가지로 SetInputValue 를 사용하기 위한 메서드
        # 하지만 SetInputValue 가 무슨 역할을 하는지는 모르겠음, id에 종목코드를
        # value 에 000660을 넣는걸 보면 해당 화면을 띄워주는 역할을 하는게 아닌가 싶은데
        self.dynamicCall("SetInputValue(QString, QString)", id, value)

    def comm_rq_data(self, rqname, trcode, next, screen_no):  # 사용자구분 명, Tran명 입력, 0:조회 2: 연속, 4자리 화면번호
        # Ex openApi.CommRqData("RQ_1", "OPT00001", 0, "0101"), TR을 요청하는 함수
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def _comm_get_data(self, code, real_type, field_name, index, item_name):  # TR 처리에 대한 이벤트가 발생했을 때
        # 실제로 데이터를 가져오려면 CommGetData 메서드를 사용
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()  # 반환값 양쪽에 있는 공백을 지워줌

    def _get_repeat_cnt(self, trcode, rqname):  # TR을 요청하면 여러 개의 데이터가 반환, 그 데이터 개수 파악을 위한 메서드
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':  # 받아와야 하는 데이터가 남아있다는 뜻
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == "opt10001_req":
            self._opt10001(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        elif rqname == "opt10080_req":
            self._opt10080(rqname, trcode)

        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname)  # 데이터의 개수

        for i in range(data_cnt):  # 개수만큼 반복
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def send_order(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
        # 사용자 구분명, 화면번호, 계좌번호 10자리, 주문유형(1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
        # 종목코드, 주문수량, 주문가격, 거래구분(00: 지정가, 03:시장가...), 원주문번호->""로 대체

    def get_chejan_data(self, fid):  # '체'결'잔'고 데이터 가져옴
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        order_num = self.get_chejan_data(9203)
        if not order_num:
            return
        sCode = self.get_chejan_data(9001)[1:]
        self.stock[sCode].order_num = order_num
        print(self.stock[sCode].order_num, end=' ')  # 주문번호
        name = self.get_chejan_data(302).strip()
        print(name, sCode, end=' ')  # 종목명, 종목코드
        # print("주문수량:", self.stock[sCode].own_num, end=' ')  # 주문수량
        # price = self.get_chejan_data(901)
        # print("주문가격:", price, end=' ')  # 주문가격
        temp1 = self.get_chejan_data(902)  # 거래 잔량
        if temp1:
            self.stock[sCode].not_yet = int(temp1)  # 거래 잔량
        print("미체결수량:", self.stock[sCode].not_yet, end='\n\n')
        if self.stock[sCode].not_yet == 0:
            temp = self.get_chejan_data(905)  # 주문 종류 구분
            if temp == '+매수':
                if self.stock[sCode].own_num == 0:
                    return
                self.buy_list.append(sCode)
                print(self.stock[sCode].own_num, '주 매수 완료', end='\n')
                # print("가지고 있는 종목 개수: ", len(self.buy_list))
                # print(self.buy_list)
                self.stock[sCode].sell_price = find_sell_price(self.stock[sCode].price_time[0], SELL_FACTOR1)
                # time.sleep(0.2)
                self.send_order("send_order_rq", 8020 + len(self.buy_list), ACCOUNT_NUM, 2, sCode,
                                self.stock[sCode].own_num, self.stock[sCode].sell_price, '00', "")  # 매도 조건1의 위치
                print("+5% 매도주문")
            elif temp == '-매도':
                try:
                    print(name, "매도 완료")
                    self.buy_list.remove(sCode)
                    self.stock[sCode].after_trade = True
                except (KeyError, ValueError):
                    pass
                # 주문 취소를 하면 매도 완료가 된다, 근데 왜 매도 완료가 되느냐, 하고 묻는다면 매도 주문을 취소해서 그런 것 같다
                # 주문 취소를 하면 어디서인가 keyerror가 뜬다, 프로그램 오류 후 주문을 정정할때

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def _opw00001(self, rqname, trcode):
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    def _opw00018(self, rqname, trcode):  # 계좌평가잔고내역요청
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_earning_rate))
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price,
                                                  eval_profit_loss_price, earning_rate])

        total_earning_rate = Kiwoom.change_format(total_earning_rate)

        if self.get_server_gubun():  # 모의투자는 소수점이 포함된 데이터 전달, 실 서버는 아님, 둘을 공통되게 만드는 메서드
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(total_earning_rate)

    def reset_opw00018_output(self):
        self.opw00018_output = {'single': [], 'multi': []}

    def get_server_gubun(self):
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    # 여기부터 staticmethod 전까지는 임의로 작성한 코드

    def _opt10080(self, rqname, trcode):  # 주식 분봉차트 조회요청
        data_cnt = self._get_repeat_cnt(trcode, rqname)

        for i in range(data_cnt):
            time = self._comm_get_data(trcode, "", rqname, i, "체결시간")
            current = self._comm_get_data(trcode, "", rqname, i, "현재가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")

            self.thlc['time'].append(time)
            self.thlc['current'].append(int(current))
            self.thlc['high'].append(int(high))
            self.thlc['low'].append(int(low))

    def _opt10001(self, rqname, trcode):
        price = self._comm_get_data(trcode, "", rqname, 0, "현재가")
        print(price)

    def _save_callback(self):
        # con = sqlite3.connect("c:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + self.today + '.db')
        for i in self.save_data:
            df = pd.DataFrame(self.save_data[i])
            df.to_sql(i, self.con, if_exists='append')
        print('저장')

        self.save_data = {}

    def _tick_callback(self, sCode, price, deal, clock):
        if sCode in self.save_data:
            self.save_data[sCode]['price'].append(price)
            self.save_data[sCode]['deal'].append(deal)
            self.save_data[sCode]['clock'].append(clock)
        else:
            self.save_data[sCode] = {'price': [], 'deal': [], 'clock': []}

        self.save_tick_cnt += 1
        if self.save_tick_cnt > self.TICKS_PER_SAVE:
            self.save_tick_cnt = 0
            self._save_callback()

    def _receive_real_data(self, sCode, sRealType, sRealData):
        # 데이터를 받아옴과 동시에 조건을 만족하면 주식을 구매, 판매하는 형식으로 프로그램을 짬
        if sRealType == '주식체결':
            # 데이터 저장 파트
            price = int(self._comm_real_data(sCode, 10))  # 가격
            deal = int(self._comm_real_data(sCode, 15))  # 거래량
            # price와 deal은 str이었음, 앞에는 +이나 -가 붙어있는 경우도 다수 존재
            clock = datetime.datetime.now()
            self._tick_callback(sCode, price, deal, clock)
            # 시간 데이터 변환
            hour = clock.hour
            minute = clock.minute
            # event_loop 종료 기준 설정
            if hour == 15 and minute == 30:
                self._save_callback()
                self.event_loop.exit()
            price = max(-price, price)
            deal = max(-deal, deal)
            # 거래 파트
            # 매도 파트에서는 standard / 10 이상의 금액이 오고가는 거래만 취급한다
            if sCode in self.stock:
                if self.stock[sCode].after_trade:
                    return
            else:
                self.stock[sCode] = Stock(price_time=[])
            if price * deal >= STANDARD / 10:
                now = hour * 60 + minute  # now 는 시간을 분으로 바꿔놓은 것, ex)11시 30의 now = 690
                second = clock.second
                if self.stock[sCode].own:
                    # 20초가 지났음에도 미체결수량이 0이 아니면 남은 수량 주문취소
                    if (self.stock[sCode].price_time[1] + 10) < (now * 60 + second)\
                            and self.stock[sCode].not_yet != 0 and sCode not in self.buy_list:
                        self.stock[sCode].own_num = self.stock[sCode].own_num - self.stock[sCode].not_yet
                        if self.stock[sCode].own_num == 0:
                            self.stock[sCode].after_trade = True
                        print(str(sCode) + "의 매수취소량:", self.stock[sCode].not_yet, clock, end=' ')
                        temp = self.stock[sCode].not_yet
                        self.stock[sCode].not_yet = 0
                        self.send_order("send_order_rq", 8010, ACCOUNT_NUM, 3, sCode, temp, 0, '03',
                                        self.stock[sCode].order_num)
                        # 과열 종목이라 매수 취소가 아예 안먹는 경우가 있다, 어떻게 해결해야할까
                    if sCode in self.buy_list:
                        buy_price = self.stock[sCode].price_time[0]
                        if price <= buy_price * (1 - 1 / 100 * SELL_FACTOR2):  # 매도 조건2의 위치
                            self.stock[sCode].undo = True
                            self.send_order("send_order_rq", 8010 + self.buy_list.index(sCode), ACCOUNT_NUM, 4, sCode,
                                            self.stock[sCode].own_num, 0, '00', self.stock[sCode].order_num)
                            self.send_order("send_order_rq", 8011 + self.buy_list.index(sCode), ACCOUNT_NUM, 2, sCode,
                                            self.stock[sCode].own_num, 0, '03', "")
                            print(sCode, "손해 매도 주문", clock, "걸린 시간: " +
                                  str(now - self.stock[sCode].price_time[1] // 60) + "분")
                            # 손해를 보자마자 파는게 아니라 손해 1퍼를 찍고 나면 기댓값을 반으로 줄여서 돌려보는게 어떤가 싶기는 한데
                else:  # 한번 거래했던 종목은 다시 매수하지 않음
                    # deal 데이터 중 -데이터를 솎아내고 STANDARD 이상의 거래 금액을 가진 데이터만 사용함
                    if price * deal >= STANDARD:
                        self.stock[sCode].price_time.append((price, now))
                        # 일정 시간이 지난 데이터는 삭제
                        while self.stock[sCode].price_time[0][1] < now - TIME_FACTOR:  # time_factor 의 위치
                            del self.stock[sCode].price_time[0]
                        # 만약 가진 종목이 LIMIT 에 도달한 경우, 더이상은 사지 않는다
                        high = max(self.stock[sCode].price_time, key=lambda x: x[0])
                        low = min(self.stock[sCode].price_time, key=lambda x: x[0])
                        # 미리 검증한 조건에 맞는지 확인
                        if high[0] >= low[0] * (1 + 1 / 100 * BUY_FACTOR) and high[1] > low[1]:  # 매수 조건의 인자
                            self.stock[sCode].own = True
                            if LIMIT >= len(self.buy_list):
                                order_num = MONEY // price
                                self.stock[sCode].own_num = order_num  # 매수하고자 하는 개수
                                self.stock[sCode].not_yet = order_num  # 미체결 개수
                                beepsound()  # 삐 소리가 나게 함
                                self.send_order("send_order_rq", 8010 + len(self.buy_list), ACCOUNT_NUM, 1, sCode,
                                                order_num, 0, '03', "")
                                print("매수", sCode, price, find_sell_price(price, 5), find_sell_price(price, -2), clock.minute)
                                self.stock[sCode].price_time = [price, now * 60 + second]
                            else:
                                print('보유 주식 개수 초과,', sCode, '구매 불가')
                                self.stock[sCode].price_time = [price, now * 60 + second]
                        # 사고 난 후 1퍼가 떨어지면 목표를 조금 줄여주는 것이 효율적인가?데이터셋에서 확인해보는 것이 나을듯
                        # 거래량이 파멸적으로 줄어든 종목은 미래가 없다고 가정?
                        # 그 시점에서 팔아버리면?
                        # 손해 매도 주문을 시장가로 해야할 것 같은데?
                        # 처음에 일정 퍼센트 이상 오른 주식은 매수하지 않는 편이 나을지도?나중에 확인해보자

    def _comm_real_data(self, strcode, nFid):  # 종목 코드, 실시간 목록 내에 있는 피드값
        ret = self.dynamicCall("GetCommRealData(QString, int)", strcode, nFid)
        return ret.strip()

    def set_real_reg(self, strScreenNo, strCodeList, strFidList, strOptType):  # 화면번호, 종목코드리스트, 피드리스트
        ret = self.dynamicCall("SetRealReg(QString, QString, QString, QString)", strScreenNo, strCodeList, strFidList,
                               strOptType)  # 한번에 100개 등록 가능, 코드 리스트와 피드는 ; 로 구분
        return ret
    # 타입 0: 마지막에 등록한 종목들만 실시간등록, 1: 이전에 실시간 등록한 종목들에 추가하고 싶을 때

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0')
        if strip_data == '':
            strip_data = '0'

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'

        if strip_data.startswith('.'):
            strip_data = '0' + strip_data

        if data.startswith('-'):
            strip_data = '-' + strip_data

        return strip_data


if __name__ == "__main__":
    app = QApplication(sys.argv)  # Kiwoom 클래스는 QAxWidget 클래스를 상속받았기 때문에 먼저 QApplication 클래스의
    # 인스턴스를 생성해 주어야 한다
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    # code_list = kiwoom.get_code_list_by_market(0)
    #
    # leng = len(code_list)
    #
    # for i in range(leng - 1, -1, -1):
    #     stock_name = kiwoom.get_master_code_name(code_list[i])
    #     if "ETN" in stock_name or "ARIRANG" in stock_name or "HANARO" in stock_name or "TIGER" in stock_name:
    #         del code_list[i]
    #         continue
    #     elif "KODEX" in stock_name or "KINDEX" in stock_name or "KBSTAR" in stock_name or "KOSEF" in stock_name:
    #         del code_list[i]
    #         continue
    #     elif "SMART" in stock_name or "레버리지" in stock_name or "S&P" in stock_name or "코스피" in stock_name:
    #         del code_list[i]
    #         continue
    #     elif "ETN" in stock_name or "FOCUS" in stock_name or "200" in stock_name:
    #         del code_list[i]
    #         continue

    # sys.stdout = open('stock.txt', 'w')

    code_list = ['000020', '000040', '000050', '000060', '000070', '000075', '000080', '000087', '000100', '000105',
                 '000120', '000140', '000145', '000150', '000155', '000157', '000180', '000210', '000215', '000220',
                 '000225', '000227', '000230', '000240', '000270', '000300', '000320', '000325', '000370', '000390',
                 '000400', '000430', '000480', '000490', '000500', '000520', '000540', '000545', '000547', '000590',
                 '000640', '000650', '000660', '000670', '000680', '000700', '000720', '000725', '000760', '000810',
                 '000815', '000850', '000860', '000880', '000885', '00088K', '000890', '000910', '000950', '000970',
                 '000990', '000995', '001020', '001040', '001045', '00104K', '001060', '001065', '001067', '001070',
                 '001080', '001120', '001130', '001140', '001200', '001210', '001230', '001250', '001260', '001270',
                 '001275', '001290', '001340', '001360', '001380', '001390', '001420', '001430', '001440', '001450',
                 '001460', '001465', '001470', '001500', '001510', '001515', '001520', '001525', '001527', '001529',
                 '001530', '001550', '001560', '001570', '001620', '001630', '001680', '001685', '001720', '001725',
                 '001740', '001745', '001750', '001755', '001770', '001780', '001790', '001795', '001800', '001820',
                 '001880', '001940', '002020', '002025', '002030', '002070', '002100', '002140', '002150', '002170',
                 '002200', '002210', '002220', '002240', '002270', '002310', '002320', '002350', '002355', '002360',
                 '002380', '002390', '002410', '002450', '002460', '002600', '002620', '002630', '002690',
                 '002700', '002710', '002720', '002760', '002780', '002785', '002787', '002790', '002795', '00279K',
                 '002810', '002820', '002840', '002870', '002880', '002900', '002920', '002960', '002990', '002995',
                 '003000', '003010', '003030', '003060', '003070', '003075', '003080', '003090', '003120', '003160',
                 '003200', '003220', '003230', '003240', '003300', '003350', '003410', '003460', '003465',
                 '003470', '003475', '003480', '003490', '003495', '003520', '003530', '003535', '003540', '003545',
                 '003547', '003550', '003555', '003560', '003570', '003580', '003610', '003650', '003670',
                 '003680', '003690', '003720', '003780', '003830', '003850', '003920', '003925', '003960', '004000',
                 '004020', '004060', '004080', '004090', '004100', '004105', '004140', '004150', '004170', '004250',
                 '004255', '004270', '004310', '004360', '004365', '004370', '004380', '004410', '004415', '004430',
                 '004440', '004450', '004490', '004540', '004545', '004560', '004565', '004690', '004700', '004710',
                 '004720', '004770', '004800', '004830', '004835', '004840', '004870', '004890', '004910', '004920',
                 '004960', '004970', '004980', '004985', '004990', '00499K', '005010', '005030', '005070', '005090',
                 '005110', '005180', '005250', '005257', '005300', '005305', '005320', '005360', '005380', '005385',
                 '005387', '005389', '005390', '005420', '005430', '005440', '005490', '005500', '005610', '005680',
                 '005690', '005720', '005725', '005740', '005745', '005750', '005800', '005810', '005820', '005830',
                 '005850', '005870', '005880', '005930', '005935', '005940', '005945', '005950', '005960', '005965',
                 '006040', '006060', '006090', '006110', '006120', '006125', '006200', '006220', '006260', '006280',
                 '006340', '006345', '006360', '006370', '006380', '006390', '006400', '006405', '006490', '006570',
                 '006650', '006660', '006740', '006800', '006805', '00680K', '006840', '006880', '006890', '006980',
                 '007070', '007110', '007120', '007160', '007210', '007280', '007310', '007340', '007460', '007540',
                 '007570', '007575', '007590', '007610', '007660', '007690', '007700', '007810', '007815',
                 '00781K', '007860', '007980', '008040', '008060', '00806K', '008110', '008250', '008260', '008350',
                 '008355', '008420', '008490', '008500', '008560', '008600', '008700', '008730', '008770', '008775',
                 '008870', '008930', '008970', '009070', '009140', '009150', '009155', '009160', '009180', '009190',
                 '009200', '009240', '009270', '009275', '009290', '009310', '009320', '009410', '009415', '009420',
                 '009440', '009450', '009460', '009470', '009540', '009580', '009680', '009770', '009810', '009830',
                 '009835', '009900', '009970', '010040', '010050', '010060', '010100', '010120', '010130', '010140',
                 '010145', '010400', '010420', '010600', '010620', '010640', '010660', '010690', '010770',
                 '010780', '010820', '010950', '010955', '010960', '011000', '011070', '011090', '011150', '011155',
                 '011170', '011200', '011210', '011230', '011280', '011330', '011390', '011420', '011500',
                 '011700', '011760', '011780', '011785', '011790', '011810', '011930', '012030', '012160',
                 '012170', '012200', '012205', '012280', '012320', '012330', '012450', '012510', '012610',
                 '012630', '012690', '012750', '012800', '013360', '013520', '013570', '013580', '013700',
                 '013870', '013890', '014130', '014160', '014280', '014285', '014440', '014530', '014580', '014680',
                 '014710', '014790', '014820', '014825', '014830', '014910', '014915', '014990', '015020', '015230',
                 '015260', '015350', '015360', '015590', '015760', '015860', '015890', '016090', '016360',
                 '016380', '016385', '016450', '016580', '016590', '016610', '016710', '016740', '016800', '016880',
                 '017040', '017180', '017370', '017390', '017550', '017670', '017800', '017810', '017900', '017940',
                 '017960', '018250', '018260', '018470', '018500', '018670', '018880', '019170', '019175', '019180',
                 '019440', '019490', '019680', '019685', '020000', '020120', '020150', '020760', '021050',
                 '021240', '023000', '023150', '023350', '023450', '023530', '023590', '023800', '023810',
                 '023960', '024070', '024090', '024110', '024720', '024890', '024900', '025000', '025530', '025540',
                 '025560', '025620', '025750', '025820', '025860', '025890', '026890', '026940', '026960', '027410',
                 '027740', '027970', '028050', '028100', '028260', '02826K', '028670', '029460', '029530', '029780',
                 '030000', '030200', '030210', '030610', '030720', '030790', '031430', '031440', '031820', '032350',
                 '032560', '032640', '032830', '033180', '033240', '033250', '033270', '033530', '033660', '033780',
                 '033920', '034020', '034120', '034220', '034300', '034310', '034590', '034730', '03473K', '034830',
                 '035000', '035150', '035250', '035420', '035510', '035720', '036420', '036460', '036530', '036570',
                 '036580', '037270', '037560', '037710', '039130', '039490', '039570', '041650', '042660', '042670',
                 '042700', '044380', '044450', '044820', '047040', '047050', '047400', '047810', '049770', '049800',
                 '051600', '051630', '051900', '051905', '051910', '051915', '052690', '053210', '053690', '055490',
                 '055550', '057050', '058430', '058650', '058730', '058850', '058860', '060980', '063160', '064350',
                 '064960', '066570', '066575', '067830', '068270', '068290', '068400', '069260', '069460', '069620',
                 '069640', '069730', '069960', '070960', '071050', '071055', '071090', '071320', '071840', '071950',
                 '071970', '072130', '072710', '073240', '074610', '075180', '075580', '077500', '077970', '078000',
                 '078520', '078930', '078935', '079160', '079430', '079550', '079980', '081000', '081660', '082640',
                 '082740', '083420', '084010', '084670', '084680', '084690', '084695', '084870', '085310', '085620',
                 '086280', '086790', '088260', '088350', '088790', '088980', '089470', '089590', '090080', '090350',
                 '090355', '090370', '090430', '090435', '091090', '091810', '092200', '092220', '092230', '092440',
                 '092780', '093050', '093230', '093240', '093370', '094280', '094800', '095570', '095720', '096300',
                 '096760', '096770', '096775', '097230', '097950', '097955', '100220', '100250', '100840', '101060',
                 '101140', '101530', '102260', '102280', '102460', '103140', '103590', '104700', '105560', '105630',
                 '105840', '107590', '108670', '108675', '111110', '111770', '112610', '114090', '115390',
                 '117580', '118000', '119650', '120030', '120110', '120115', '122900', '123690', '123700', '123890',
                 '126560', '128820', '128940', '129260', '130660', '133820', '134380', '134790', '136490', '138040',
                 '138250', '138490', '138930', '139130', '139480', '140910', '143210', '144620', '145210', '145270',
                 '145720', '145990', '145995', '152550', '153360', '155660', '155900', '161000', '161390', '161890',
                 '163560', '168490', '170900', '172580', '175330', '176710', '180640', '18064K', '181710', '183190',
                 '185750', '192080', '192400', '192650', '192720', '192820', '194370', '195870', '200880', '204210',
                 '204320', '207940', '210540', '210980', '213500', '214320', '214330', '214390', '214420', '226320',
                 '227840', '229640', '234080', '241560', '241590', '244920', '248070', '248170', '249420', '251270',
                 '264900', '26490K', '267250', '267260', '267270', '267290', '268280', '271560', '271980',
                 '272210', '272450', '272550', '280360', '281820', '282330', '282690', '284740', '285130', '28513K',
                 '286940', '293480', '293940', '294870', '298000', '298020', '298040', '298050', '300720',
                 '302440', '306200', '307950', '308170', '316140', '317400', '322000', '326030', '330590', '334890',
                 '336260', '33626K', '33626L', '336370', '33637K', '33637L', '338100', '339770', '344820', '348950',
                 '350520', '352820', '353200', '35320K', '357120', '357250', '361610', '363280', '36328K', '365550',
                 '375500', '37550K', '378850', '380440', '383220', '383800', '38380K', '385590', '385600', '385710',
                 '385720', '950210', '900140']

    code_str_list = []

    for i in range(10):
        code_str = ""
        for j in range(100 * i, 100 * (i + 1)):
            if j >= len(code_list):
                break
            code_str += code_list[j]
            code_str += ";"
        code_str_list.append(code_str)

    kiwoom.set_real_reg(0, code_str_list[0], "10", "0")
    for i in range(1, 10):
        kiwoom.set_real_reg(i, code_str_list[i], "10", "1")

    kiwoom.set_input_value("계좌번호", "8000927211")
    kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "7777")

    start = kiwoom.d2_deposit
    print("시작 금액:", start)
    print("프로그램 시작")
    print(datetime.datetime.now())

    kiwoom.event_loop = QEventLoop()
    kiwoom.event_loop.exec()

    kiwoom.set_input_value("계좌번호", "8000927211")
    kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "7777")

    finish = kiwoom.d2_deposit
    print("시작 금액:", start)
    print("종료 금액:", finish, end='\n\n')

    print("데이터 수집 끝")
    data_filter(kiwoom.today, code_list)
    print("데이터 filtering 끝")
    method_test(kiwoom.today, code_list)
    print("method test 끝")
    view_total_data()
    print("total_result 생성 완료")
    print('프로그램 종료')
# 지금 프로그램을 어떻게 하면 실전으로 바꿀 수 있는지 확인해봐야함
# 단순히 계좌번호를 바꾸는 것으로는 안될 것 같은데?
# 파이썬 로거 사용해보기
# 3시가 되면 보유중인 주식을 싹 팔고 저장만 하는 것이 어떤가?
# 시장가로 하면 매수 주문이 성사되지 않을 가능성은? 없다면 매수 취소 부분은 제거해도 된다
# 주문이 안걸리는 경우는 buy_list에는 들어간 종목이 order_num이 없다면?이라는 조건으로 해결 가능할듯