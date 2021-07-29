import pandas as pd
import sqlite3
from tqdm import tqdm
import numpy as np
import winsound as sd
from dataclasses import dataclass


def data_filter(date, code_lst):
    con1 = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + date + ".db")  # 날짜 데이터도 수정 필요
    cursor1 = con1.cursor()
    con2 = sqlite3.connect("c:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + date + '_filter.db')
    new_data = {}
    total_count = 0
    new_count = 0
    for k in code_lst:
        try:
            cursor1.execute(f"SELECT * FROM '{k}'")
            temp = cursor1.fetchall()
            total_count += len(temp)
            if temp:
                new_data[k] = {'price': [], 'deal': [], 'clock': []}
                for i in range(len(temp)):
                    if temp[i][1] * int(temp[i][2]) >= 10000000:  # 지금 데이터에는 deal이 +, -가 나뉘어져 있다.
                        # + 데이터만 사용하는 것이 결과값이 더 좋지만 실제로는 어떻게 될지 모르겟음, 조금 더 지켜봐야 알 수 있을듯
                        # 매수는 천만원 기준으로 하되, 매도는 실시간으로 해주는 것이 덜 손해일 수도 있음, 한번 확인 요망, 프로그램 수정해보기
                        new_data[k]['price'].append(temp[i][1])
                        new_data[k]['deal'].append(temp[i][2])
                        new_data[k]['clock'].append(temp[i][3])
                new_count += len(new_data[k]['price'])
        except sqlite3.OperationalError:
            pass
    print(total_count, new_count)
    for i in new_data:
        df = pd.DataFrame(new_data[i])
        df.to_sql(i, con2, if_exists='replace')
        
        
# 원래는 구매할 수 있는 종목이 한정적이라 살 수 있는 종목의 개수에 limit 을 걸어야 하지만 이건 검증 과정이므로 생략
def method1(data):  # 한 시점의 거래량이 그 전 지점에 비해 폭발적으로 늘어나는 경우
    # 이건 누적 데이터를 받아와서 해야할 것 같은데...?
    # 일단 한 알고리즘에 집중하고 나머지는 백준 풀면서 시간 보내봐야함
    # 그래서 지금 받아야하는 데이터에 시간 데이터도 추가함
    pass


def method2(data, time_factor, buy_factor, sell_factor1, sell_factor2):
    # 조건 1, time_factor 분 내의 데이터만 저장해놓는다
    # 조건 2, 구매 후 ???분이 지나면 판다->이건 나중에 구현해봐도 될듯, 일단 기본조건에 맞는 주식들의 비율을 확인할 예정
    # 조건 3, MAX_NUM 의 개수를 넘으면 구매하지 않는다.->이것도 나중에 구현
    # 조건 4, 이미 구매했던 종목은 구매하지 않는다
    # 조건 5, buy_factor 만큼 주가 상승한 종목을 구매한다
    # 조건 6, sell_factor1만큼 주가가 상승하거나, sell_factor2만큼 주가가 하락하면 매도한다
    price_time = []
    buy_price = 0
    for i in range(len(data)):
        index, price, deal, time = data[i]
        price = eval(price)
        price = max(price, -price)
        time = int(time[11:13]) * 60 + int(time[14:16])
        if not buy_price:
            price_time.append((price, time))

            while price_time[0][1] < time - time_factor:  # 조건 1의 인자 위치
                del price_time[0]

            high = max(price_time, key=lambda x: x[0])
            low = min(price_time, key=lambda x: x[0])

            if high[0] >= low[0] * (1 + 1 / 100 * buy_factor) and high[1] > low[1]:  # 매수 조건의 인자
                price_time = [(price, time)]
                buy_price = price
        else:  # 매도 조건의 인자들 + 조건 4
            if buy_price * (1 + 1 / 100 * sell_factor1) <= price:
                return 1
            elif price <= buy_price * (1 - 1 / 100 * sell_factor2):
                return 0
    if buy_price:
        return 2
    return -1
# time_factor, buy_factor, sell_factor1, sell_factor2
# -1은 해당사항 없음, 0은 손해, 1은 이득, 2는 매수는 했지만 매도 조건에는 충족되지 않은 경우


def method2_test(date, code_lst):
    con = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + date + "_filter.db")
    # 날짜 데이터를 수정해서 넣어줘야함
    cursor = con.cursor()
    time_factor_list = tqdm([3, 4, 5, 6, 7, 8])
    buy_factor_list = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]
    # time_factor 와 buy_factor 가 같으면 -1의 개수는 같다, 를 이용하면 더 빨리 돌려볼 수 있을 것 같은데?->성공
    # buy_factor 가 증가하면 -1의 개수도 증가함
    # 원래 대략 126초정도 걸림->처음엔 46초, 그 이후에는 20초대에서 처리가능
    sell_factor1_list = [2, 2.5, 3, 3.5, 4, 4.5, 5]
    sell_factor2_list = [1, 1.5, 2, 2.5]
    total_data = []
    for q in time_factor_list:
        minus_one_list = {}
        for w in buy_factor_list:
            for e in sell_factor1_list:
                for r in sell_factor2_list:
                    count_list = {-1: len(minus_one_list), 0: 0, 1: 0, 2: 0}
                    for k in code_lst:
                        try:
                            if k not in minus_one_list:
                                cursor.execute(f"SELECT * FROM '{k}'")
                                temp = np.array(cursor.fetchall())  # index, price, deal, clock
                                result = method2(temp, q, w, e, r)  # method position
                                count_list[result] += 1
                                if result == -1:
                                    minus_one_list[k] = 0
                        except sqlite3.OperationalError:
                            pass
                    total_data.append([q, w, e, r, count_list[-1], count_list[0], count_list[1], count_list[2],
                                       e * count_list[1] - r * count_list[0] - r * 0.8 * count_list[2]
                                       - 0.33 * (count_list[0] + count_list[1] + count_list[2]),
                                       e * count_list[1] - r * count_list[0] - r * 0.8 * count_list[2]
                                       - 0.68 * (count_list[0] + count_list[1] + count_list[2])])
    con2 = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/method_test.db")
    df = pd.DataFrame(total_data, columns=['time', 'buy', 'up_sell', 'down_sell', 'none', 'loss', 'benefit', 'timeout',
                                           'score', 'simulate_score'])
    df.to_sql(date, con2, if_exists='replace')


def method3(data, time_factor, buy_factor, sell_factor1, sell_factor2):
    # method2를 사용해서 하루에 최대 이익을 얼마나 볼 수 있는지 그래프로 나타낼 예정
    # 베이스는 method2를 그대로 사용
    price_time = []
    buy_price = 0
    for i in range(len(data)):
        index, price, deal, time = data[i]
        price = eval(price)
        price = max(price, -price)
        time = int(time[11:13]) * 60 + int(time[14:16])
        if not buy_price:
            price_time.append((price, time))

            while price_time[0][1] < time - time_factor:  # 조건 1의 인자 위치
                del price_time[0]

            high = max(price_time, key=lambda x: x[0])
            low = min(price_time, key=lambda x: x[0])

            if high[0] >= low[0] * (1 + 1 / 100 * buy_factor) and high[1] > low[1]:  # 매수 조건의 인자
                price_time = [(price, time)]
                buy_price = price
        else:  # 매도 조건의 인자들 + 조건 4
            if buy_price * (1 + 1 / 100 * sell_factor1) <= price:
                return 1, time
            elif price <= buy_price * (1 - 1 / 100 * sell_factor2):
                return 0, time
    if buy_price:
        return 2
    return -1


def method3_test(date, code_lst):
    con = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/" + date + "_filter.db")
    # 날짜 데이터를 수정해서 넣어줘야함
    cursor = con.cursor()
    time_factor_list = tqdm([3, 4, 5, 6, 7, 8])
    buy_factor_list = [3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]
    # time_factor 와 buy_factor 가 같으면 -1의 개수는 같다, 를 이용하면 더 빨리 돌려볼 수 있을 것 같은데?->성공
    # buy_factor 가 증가하면 -1의 개수도 증가함
    # 원래 대략 126초정도 걸림->처음엔 46초, 그 이후에는 20초대에서 처리가능
    sell_factor1_list = [2, 2.5, 3, 3.5, 4, 4.5, 5]
    sell_factor2_list = [1, 1.5, 2, 2.5]
    total_data = []
    for q in time_factor_list:
        minus_one_list = {}
        for w in buy_factor_list:
            count_list = {-1: len(minus_one_list), 0: 0, 1: 0, 2: 0}
            for e in sell_factor1_list:
                for r in sell_factor2_list:
                    count_list[0] = 0
                    count_list[1] = 0
                    count_list[2] = 0
                    check_time_element = []
                    for k in code_lst:
                        try:
                            if k not in minus_one_list:
                                cursor.execute(f"SELECT * FROM '{k}'")
                                temp = np.array(cursor.fetchall())  # index, price, deal, clock
                                result = method3(temp, q, w, e, r)  # method position
                                if type(result) is tuple:
                                    count_list[result[0]] += 1
                                    check_time_element.append(result)
                                else:
                                    count_list[result] += 1
                                    if result == -1:
                                        minus_one_list[k] = 0
                        except sqlite3.OperationalError:
                            pass
                    check_time_element.sort(key=lambda x: x[1])
                    temp = []
                    for i in check_time_element:
                        if not temp:
                            if i[0] == 1:
                                temp.append(e)
                            else:
                                temp.append(r)
                        else:
                            temp_temp = temp[-1]
                            if i[0] == 1:
                                temp.append(temp_temp + e)
                            else:
                                temp.append(temp_temp - r)

                    total_data.append([q, w, e, r, count_list[-1], count_list[0], count_list[1], count_list[2],
                                       e * count_list[1] - r * count_list[0] - r * 0.8 * count_list[2]
                                       - 0.33 * (count_list[0] + count_list[1] + count_list[2]), max(temp) - temp.index(max(temp)) * 0.33,
                                       check_time_element[temp.index(max(temp)) - 1][1], temp[-1]])
    con2 = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/new_method_test.db")
    df = pd.DataFrame(total_data, columns=['time', 'buy', 'up_sell', 'down_sell', 'none', 'loss', 'benefit', 'timeout',
                                           'score', 'high_score', 'real_time', 'testing'])
    # print(df)
    df.to_sql(date, con2, if_exists='replace')


# 다 쓰고 원래대로 돌려주셈
def view_total_data():
    con = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/new_method_test.db")
    cursor = con.cursor()
    date = ["2021-07-19", "2021-07-22", "2021-07-26"]
    # 이 부분은 수기로 추가해줘야함, 텍스트 파일로 저장해도 무관한데 이부분은
    data = []
    for i in date:
        cursor.execute(f"SELECT * FROM '{i}'")
        data.append(cursor.fetchall())
    result = []
    for i in range(1512):
        temp = data[0][i]
        score = 0
        for j in range(len(date)):
            score += data[j][i][-3]
        temp_lst = [temp[1], temp[2], temp[3], temp[4], round(score / len(date), 2)]
        result.append(temp_lst)
    df = pd.DataFrame(result, columns=['time', 'buy', 'up_sell', 'down_sell', 'score'])
    df.to_sql("Score", con, if_exists='replace')


def view_total_data_simulate():
    con = sqlite3.connect("C:/Users/ooden/PycharmProjects/pythonProject1/stock_data/method_test.db")
    cursor = con.cursor()
    date = ["2021-07-19_simulate",
            "2021-07-22_simulate", "2021-07-26_simulate"]
    # 이 부분은 수기로 추가해줘야함, 텍스트 파일로 저장해도 무관한데 이부분은
    data = []
    for i in date:
        cursor.execute(f"SELECT * FROM '{i}'")
        data.append(cursor.fetchall())
    result = []
    for i in range(1512):
        temp = data[0][i]
        score = 0
        for j in range(len(date)):
            score += data[j][i][-1]
        temp_lst = [temp[1], temp[2], temp[3], temp[4], round(score / len(date) / 5, 2)]
        result.append(temp_lst)
    df = pd.DataFrame(result, columns=['time', 'buy', 'up_sell', 'down_sell', 'score'])
    df.to_sql("Score_simulate", con, if_exists='replace')


def find_sell_price(price, sell_factor2):
    # ~1000~5000~~10000~~50000~~~100000~~~500000~~~~
    # 1    5    10     50     100      500      1000
    # 이거로 해결 가능, 거래 도중 가격이 변경되면 단위도 변경된다
    standard_list = [1000, 5000, 10000, 50000, 100000, 500000, 1000000]
    sell_price = price * (1 + 1 / 100 * sell_factor2)
    standard = 5000
    for i in standard_list:
        if sell_price < i:
            standard = i // 1000
            break
    sell_price = (sell_price // standard - 1) * standard
    return int(sell_price)


def beepsound():
    sd.Beep(2000, 1000)


@dataclass
class Stock:
    price_time: list
    own_num: int = 0
    not_yet: int = 0
    sell_price: int = 0
    order_num = str
    own: bool = False
    undo: bool = False
    after_trade: bool = False
# 1, 매수가 순조롭게 이뤄지고 이득보고 매도한 경우 V
# 2, 매수가 순조롭게 이뤄지고 손해보고 매도한 경우 V
# 3, 매수가 순조롭게 이뤄지지 않고 이득보고 매도한 경우
# 3, 매수가 순조롭게 이뤄지지 않고 손해보고 매도한 경우


# '002420', '003280', '003620', '007630', '010580', '011300', '011690', '012600',
# '013000', '015540', '020560', '021820', '109070', '267850', '298690',


if __name__ == "__main__":
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
    # "2021-06-30", "2021-07-01", "2021-07-02",  # 데이터가 너무 좋은 값으로 나와서 일단 제외
    todays = ["2021-07-19", "2021-07-22", "2021-07-26"]
    for today in todays:
        method3_test(today, code_list)
    # data_filter(today, code_list)
    # print("데이터 filtering 끝")
    # today = "2021-07-19"

    # print(today)
    view_total_data()
    # view_total_data_simulate()
    # print("데이터 병합 끝")
    # print(find_sell_price(8270, 5))
    # 날짜별로 폴더를 따로 만들어줘야할 것 같은데, 폴더도 자동생성이 가능한가?
    # 가능은 한데 아직은 굳이
