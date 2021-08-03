"""키움증권 OpenAPI

키움증권과 관련된 OLE사용자 지정 컨트롤 모듈

OCX (OLE Custom Extension)
"""

from warnings import warn

from PyQt5.QAxContainer import QAxWidget


class KiwoomOpenAPI:
    """키움증권 OpenAPI

    https://download.kiwoom.com/web/openapi/kiwoom_openapi_plus_devguide_ver_1.1.pdf
    """

    # 에러 코드
    OP_ERR_NONE = 0  # 정상처리
    OP_ERR_FAIL = -10  # 실패
    OP_ERR_LOGIN = -100  # 사용자정보교환실패
    OP_ERR_CONNECT = -101  # 서버접속실패
    OP_ERR_VERSION = -102  # 버전처리실패
    OP_ERR_FIREWALL = -103  # 개인방화벽실패
    OP_ERR_MEMORY = -104  # 메모리보호실패
    OP_ERR_INPUT = -105  # 함수입력값오류
    OP_ERR_SOCKET_CLOSED = -106  # 통신연결종료
    OP_ERR_SISE_OVERFLOW = -200  # 시세조회과부하
    OP_ERR_RQ_STRUCT_FAIL = -201  # 전문작성초기화실패
    OP_ERR_RQ_STRING_FAIL = -202  # 전문작성입력값오류
    OP_ERR_NO_DATA = -203  # 데이터없음.
    OP_ERR_OVER_MAX_DATA = -204  # 조회가능한종목수초과
    OP_ERR_DATA_RCV_FAIL = -205  # 데이터수신실패
    OP_ERR_OVER_MAX_FID = -206  # 조회가능한FID수초과
    OP_ERR_REAL_CANCEL = -207  # 실시간해제오류
    OP_ERR_ORD_WRONG_INPUT = -300  # 입력값오류
    OP_ERR_ORD_WRONG_ACCTNO = -301  # 계좌비밀번호없음
    OP_ERR_OTHER_ACC_USE = -302  # 타인계좌사용오류
    OP_ERR_MIS_2BILL_EXC = -303  # 주문가격이20억원을초과
    OP_ERR_MIS_5BILL_EXC = -304  # 주문가격이50억원을초과
    OP_ERR_MIS_1PER_EXC = -305  # 주문수량이총발행주수의1%초과오류
    OP_ERR_MIS_3PER_EXC = -306  # 주문수량은총발행주수의3%초과오류
    OP_ERR_SEND_FAIL = -307  # 주문전송실패
    OP_ERR_ORD_OVERFLOW = -308  # 주문전송과부하
    OP_ERR_MIS_300CNT_EXC = -309  # 주문수량300계약초과
    OP_ERR_MIS_500CNT_EXC = -310  # 주문수량500계약초과
    OP_ERR_ORD_WRONG_ACCTINFO = -340  # 계좌정보없음
    OP_ERR_ORD_SYMCODE_EMPTY = -500  # 종목코드없음

    def __init__(self, *args, **kwargs) -> None:
        self.OCXconn = QAxWidget()
        self.OCXconn.setControl("KHOPENAPI.KHOpenAPICtrl.1")

        self.OCXconn.OnReceiveTrData.connect(self.OnReceiveTrData)

    # 1)
    def CommConnect(self) -> int:
        """로그인 윈도우를 실행한다.

        로그인이 성공하거나 실패하는 경우 `OnEventConnect` 이벤트가 발생하고
        이벤트의 인자 값으로 로그인 성공 여부를 알 수 있다.

        Returns:
            0 - 성공, 음수값은 실패
        """
        return int(self.OCXconn.dynamicCall("CommConnect()"))

    # 2)
    def CommTerminate(self) -> None:
        """더 이상 지원하지 않는 함수

        통신 연결 상태는 GetConnectState 메소드로 알 수 있다
        """
        warn('이 함수는 더 이상 지원되지 않습니다.')
        return None

    # 3)
    def CommRqData(self,
                   sRQName: str,
                   sTrCode: str,
                   nPrevNext: int,
                   sScreenNo: str) -> int:
        """Tran을 서버로 송신한다.

        >>> self.CommRqData("RQ_1", "OPT00001", 0, "0101")

        Args:
            sRQName: (BSTR) 사용자구분 명
            sTrCode: (BSTR) Trans명 입력
            nPrevNext: (long) 0: 조회, 2: 연속
            sScreenNo: (BSTR) 4자리의 화면번호

        Returns:
            -   `OP_ERR_SISE_OVERFLOW` – 과도한 시세조회로 인한 통신불가
            -   `OP_ERR_RQ_STRUCT_FAIL` – 입력 구조체 생성 실패
            -   `OP_ERR_RQ_STRING_FAIL` – 요청전문 작성 실패
            -   `OP_ERR_NONE` – 정상처리
        """
        return int(self.OCXconn.dynamicCall(
            "CommRqData(QString, QString, int, QString)",
            sRQName,
            sTrCode,
            nPrevNext,
            sScreenNo
        ))

    # 4)
    def GetLoginInfo(self, sTag: str) -> str:
        """로그인한 사용자 정보를 반환한다.

        BSTR `sTag`에 들어 갈 수 있는 값은 아래와 같음
            -   "ACCOUNT_CNT" – 전체 계좌 개수를 반환한다.
            -   "ACCNO" – 전체 계좌를 반환한다. 계좌별 구분은 ';'이다.
            -   "USER_ID" - 사용자 ID를 반환한다.
            -   "USER_NAME" – 사용자명을 반환한다.
            -   "KEY_BSECGB" – 키보드보안 해지여부. 0:정상, 1:해지
            -   "FIREW_SECGB" – 방화벽 설정 여부. 0:미설정, 1:설정, 2:해지

        >>> self.GetLoginInfo("ACCOUNT_CNT")

        Args:
            sTag: (BSTR) 사용자 정보 구분 TAG값 (비고)

        Returns:
            TAG값에 따른 데이터 반환
        """
        return self.OCXconn.dynamicCall(
            "GetLoginInfo(QString)",
            sTag
        )

    # 5)
    def SendOrder(self,
                  sRQName: str,
                  sScreenNo: str,
                  sAccNo: str,
                  nOrderType: int,
                  sCode: str,
                  nQty: int,
                  nPrice: int,
                  sHogaGb: str,
                  sOrgOrderNo: str) -> int:
        """주식 주문을 서버로 전송한다.

        sHogaGb
            00:지정가,
            03:시장가,
            05:조건부지정가,
            06:최유리지정가,
            07:최우선지정가,
            10:지정가IOC,
            13:시장가IOC,
            16:최유리IOC,
            20:지정가FOK,
            23:시장가FOK,
            26:최유리FOK,
            61:장전시간외종가,
            62:시간외단일가,
            81:장후시간외종가

        ※ 시장가, 최유리지정가, 최우선지정가, 시장가IOC, 최유리IOC, 시장가FOK, 최유리FOK, 장전시간외, 장후시간외 주문시 주문가격을 입력하지 않습니다.

        ex)
            지정가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 48500, “00”, “”);
            시장가 매수 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 1, “000660”, 10, 0, “03”, “”);
            매수 정정 - openApi.SendOrder(“RQ_1”,“0101”, “5015123410”, 5, “000660”, 10, 49500, “00”, “1”);
            매수 취소 - openApi.SendOrder(“RQ_1”, “0101”, “5015123410”, 3, “000660”, 10, 0, “00”, “2”);

        Args:
            sRQName: (BSTR) 사용자 구분 요청 명
            sScreenNo: (BSTR) 화면번호[4]
            sAccNo: (BSTR) 계좌번호[10]
            nOrderType: (LONG) 주문유형 (1:신규매수, 2:신규매도, 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정)
            sCode: (BSTR) 주식종목코드
            nQty: (LONG) 주문수량
            nPrice: (LONG) 주문단가
            sHogaGb: (BSTR) 거래구분
            sOrgOrderNo: (BSTR) 원주문번호

        Returns:
            (LONG) 에러코드 (4.에러코드표 참고)
        """
        return int(self.OCXconn.dynamicCall(
            "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
            [sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo]
        ))

    # 9)
    def CommGetData(self, *args, **kwargs) -> str:
        """이 함수는 지원하지 않을 것이므로 용도에 맞는 전용 함수를 사용할 것

        조회 정보 요청 - openApi.GetCommData(“OPT00001”, RQName, 0, “현재가”);
        실시간정보 요청 - openApi.GetCommRealData(“000660”, 10);
        체결정보 요청 - openApi.GetChejanData(9203);
        """
        warn("이 함수는 지원하지 않을 것이므로 용도에 맞는 전용 함수를 사용할 것"
             "(함수 설명 참조)")
        return self.OCXconn.dynamicCall(
            "CommGetData()",
            *args,
            **kwargs
        )

    # 16)
    def GetMasterCodeName(self, strCode: str) -> str:
        """종목코드의 한글명을 반환한다.

        장내외, 지수선옵, 주식선옵 검색 가능.

        Args:
            strCode: (LPCTSTR) 종목코드
        Returns:
            (BSTR) 종목한글명
        """
        return self.OCXconn.dynamicCall("GetMasterCodeName(QString)", strCode)

    # 25)
    def GetCommRealData(self, strCode: str, nFid: int) -> str:
        """실시간 시세 데이터를 반환한다.

        Ex) 현재가출력 - openApi.GetCommRealData(“039490”, 10);
        참고) strCode는 OnReceiveRealData 첫번째 매개변수를 사용

        Args:
            strCode: (str) 종목코드
            nFid: (long) 실시간 아이템

        Returns:
            수신 데이터
        """
        return self.OCXconn.dynamicCall(
            "GetCommRealData(QString, int)",
            strCode,
            nFid
        ).strip()

    # 26)
    def GetChejanData(self, nFid: int) -> str:
        """체결잔고 데이터를 반환한다.

        Ex) 현재가출력 – `openApi.GetChejanData(10)`

        Args:
            nFid: (long) 체결잔고 아이템

        Returns:
            수신 데이터
        """
        return self.OCXconn.dynamicCall(
            "GetChejanData(int)",
            nFid
        ).strip()

    # OpenAPI 컨트롤 이벤트

    def OnReceiveTrData(self,
                        sScrNo: str,
                        sRQName: str,
                        sTrCode: str,
                        sRecordName: str,
                        sPreNext: str,
                        nDataLength: None = None,
                        sErrorCode: None = None,
                        sMessage: None = None,
                        sSplmMsg: None = None) -> None:
        """서버통신 후 데이터를 받은 시점을 알려준다.

        `sRQName` – `CommRqData의` `sRQName과` 매핑되는 이름이다.
        `sTrCode` – `CommRqData의` `sTrCode과` 매핑되는 이름이다.

        Args:
            sScrNo: (LPCTSTR) 화면번호
            sRQName: (LPCTSTR) 사용자구분 명
            sTrCode: (LPCTSTR) Tran 명
            sRecordName: (LPCTSTR) Record 명
            sPreNext: (LPCTSTR) 연속조회 유무
            nDataLength: (LONG) 1.0.0.1 버전 이후 사용하지 않음.
            sErrorCode: (LPCTSTR) 1.0.0.1 버전 이후 사용하지 않음.
            sMessage: (LPCTSTR) 1.0.0.1 버전 이후 사용하지 않음.
            sSplmMsg: (LPCTSTR) 1.0.0.1 버전 이후 사용하지 않음.

        Returns:
            없음
        """
        pass

    def OnReceiveRealData(self,
                          sJongmokCode: str,
                          sRealType: str,
                          sRealData: str) -> None:
        """실시간데이터를 받은 시점을 알려준다

        Args:
            sJongmokCode: (LPCTSTR) 종목코드
            sRealType: (LPCTSTR) 리얼타입
            sRealData: (LPCTSTR) 실시간 데이터전문

        Returns:
            없음
        """
        pass

    def OnReceiveMsg(self,
                     sScrNo: str,
                     sRQName: str,
                     sTrCode: str,
                     sMsg: str) -> None:
        """서버통신 후 메시지를 받은 시점을 알려준다

        Args:
            sScrNo: (LPCTSTR) 화면번호. CommRqData의 sScrNo와 매핑된다.
            sRQName: (LPCTSTR) 사용자구분 명. CommRqData의 sRQName 와 매핑된다.
            sTrCode: (LPCTSTR) Tran 명. CommRqData의 sTrCode 와 매핑된다.
            sMsg: (LPCTSTR) 서버메시지

        Returns:
            없음
        """
        pass

    def OnReceiveChejanData(self,
                            sGubun: str,
                            nItemCnt: str,
                            sFidList: str) -> None:
        """체결데이터를 받은 시점을 알려준다.

        Args:
            sGubun: (LPCTSTR) 체결구분. 0:주문체결통보, 1:잔고통보, 3:특이신호
            nItemCnt: (LPCTSTR) 아이템갯수
            sFidList: (LPCTSTR) 데이터리스트. 데이터 구분은 ‘;’ 이다.

        Returns:
            없음
        """
        pass

    def OnEventConnect(self,
                       nErrCode: int) -> None:
        """서버 접속 관련 이벤트

        Args:
            nErrCode: (LONG) 에러 코드. 0이면 로그인 성공, 음수면 실패. 음수인 경우는 에러 코드 참조

        Returns:
            없음
        """
        pass

    def OnReceiveCondition(self,
                           strCode,
                           strType,
                           strConditionName,
                           strConditionIndex) -> None:
        """조건검색 실시간 편입,이탈 종목을 받을 시점을 알려준다.

        Args:
            strCode: (LPCTSTR) 종목코드
            strType: (LPCTSTR) 편입(“I”), 이탈(“D”). `strType으로` 편입된 종목인지 이탈된 종목인지 구분한다.
            strConditionName: (LPCTSTR) 조건명. `strConditionName에` 해당하는 종목이 실시간으로 들어옴.
            strConditionIndex: (LPCTSTR) 조건명 인덱스

        Returns:
            없음
        """
        pass

    def OnReceiveTrCondition(self,
                             sScrNo: str,
                             strCodeList: str,
                             strConditionName: str,
                             nIndex: int,
                             nNext: int) -> None:
        """조건검색 조회응답으로 종목리스트를 구분자(“;”)로 붙어서 받는 시점.

        Args:
            sScrNo: (LPCTSTR) 종목코드
            strCodeList: (LPCTSTR) 종목리스트(“;”로 구분)
            strConditionName: (LPCTSTR) 조건명
            nIndex: (int) 조건명 인덱스
            nNext: (int) 연속조회(2:연속조회, 0:연속조회없음)

        Returns:
            없음
        """
        pass

    def OnReceiveConditionVer(self,
                              lRet: int,
                              sMsg: str) -> None:
        """로컬에 사용자 조건식 저장 성공 여부를 확인하는 시점

        Args:
            lRet: (long) 사용자 조건식 저장 성공여부 (1: 성공, 나머지 실패)
            sMsg: (str)

        Returns:
            없음
        """
        pass
