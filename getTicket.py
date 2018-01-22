#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from urllib import request, parse
from datetime import datetime, timedelta
import sys
import json, re, time
from login import My12306, logger
import trainIdxMap
try:
    import myInfo
except ImportError:
    class myInfo:
        user = "abcd"
        passwd = "123456"
        wantTrains = []
        passengers = [user]
        travelInfo = {
            "wantSeatType": "O",
            "train_date": "",
            "from_station": "GZQ",
            "to_station": "WHN",
            "query_from_station_name": "广州",
            "query_to_station_name": "武汉",
        }

    
def getTrainInfo(browser, wantTrains=None, **travelInfo):
    if "train_date" not in travelInfo or travelInfo["train_date"] == "":
        travelInfo["train_date"] = datetime.strftime(datetime.now() + timedelta(days=3), "%Y-%m-%d")
        logger.info("未填写查票日期，采用默认值(3天后): {}".format(travelInfo["train_date"]))
    if len(travelInfo["train_date"]) != 10:
        logger.error("wrong train_date format:{}, wanted: yyyy-mm-dd(2018-01-01).".format(travelInfo["train_date"]))
        sys.exit(1)
    ticketData = parse.urlencode([
        ("leftTicketDTO.train_date",   travelInfo["train_date"]),
        ("leftTicketDTO.from_station", travelInfo["from_station"]),
        ("leftTicketDTO.to_station",   travelInfo["to_station"]),
        ("purpose_codes",              "ADULT")
    ])
    logger.debug("ticketData: {}".format(ticketData))
    
    ok = False
    while not ok:
        retCode, retData = browser.doGET("https://kyfw.12306.cn/otn/leftTicket/queryZ", ticketData)
        logger.info("retCode:[{}]".format(retCode))
        try:
            trainData = json.loads(retData.decode("utf-8"))
            logger.debug(trainData)
            trains = filterTrainInfo(trainData["data"]["result"], wantTrains)
            if len(trains) == 0:
                logger.info("没有满足条件的车次，5秒后重新查询")
                ok = False
                time.sleep(5)
            else:
                ok = True
                return trains
        except:
            logger.info("服务器忙，5秒后重新查询")
            time.sleep(5)

def filterTrainInfo(trains, wantTrains):
    logger.info("查询需要的车次...")
    chosedTrains = []
    for item in trains:
        vals = item.split("|")
        if vals[trainIdxMap.bookable] == "Y" and (not vals[trainIdxMap.seat_2].strip().startswith(("无","-"))):
            chosedTrains.append(item)
    if wantTrains is None:
        logger.info("未填写需要的车次，将采用全量查询")
        return chosedTrains
    return list(filter(lambda x:x.split("|")[trainIdxMap.stationTrainCode] in wantTrains, chosedTrains))

"""
POST 验证用户是否登陆: https://kyfw.12306.cn/otn/login/checkUser
参数列表:
_json_att:
"""

def checkUser(browser):
    logger.info("验证用户是否已登陆...")
    data = {"_json_att": ""}
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/login/checkUser", parse.urlencode(data))
    logger.info("retCode:[{}]".format(retCode))
    ok = False
    while not ok:
        if retCode == 200:
            logger.debug("retCode:[{}], retData:[{}]".format(retCode, retData.decode("utf-8")))
            try:
                result = json.loads(retData.decode("utf-8"))
                if result["data"]["flag"] == True:
                    logger.info("验证通过，用户已登录")
                    ok = True
                    return True
                else:
                    logger.info("登陆信息过期，请重新登录")
                    sys.exit(1)
            except:
                pass

"""
POST 确认购票信息 https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest
参数列表:
secretStr:j/1PMOf74E0WmppV1A8k/vHAZYpxpgkaGq5AATeQE4eMEW09JSABTTN6SxpsMASmXWqC1ju2OAyf
8rSPiES/clHkQiWwta8XxUMylLOUmIq0LTcPQdxXkOamUvOox9qiEFDP1EcyrCiQPn4fu0MGrV6O
0egB0wtILTJngdf/qRTZmw20BtyeL40yjdZzm+csW8miS0LqYl/zU0U+IbhpoxOfDaNb7sA0QZtn
ljM2UMrgo6VZU3cE9HyaeOQ/yTc3EYgQBFjmjks=
train_date:2018-01-16
back_train_date:2018-01-13
tour_flag:dc
purpose_codes:ADULT
query_from_station_name:广州
query_to_station_name:武汉
undefined:
"""
def submitOrderRequest(browser, train, **travelInfo):
    logger.info("确认购票信息...")
    if "train_date" not in travelInfo or travelInfo["train_date"] == "":
        travelInfo["train_date"] = datetime.strftime(datetime.now() + timedelta(days=3), "%Y-%m-%d")
        logger.info("未填写查票日期，采用默认值(3天后): {}".format(travelInfo["train_date"]))
    back_date = datetime.strftime(datetime.now(), "%Y-%m-%d")
    wantTrainInfo = train.split("|")
    logger.info("成功获取车次: {}".format(wantTrainInfo))
    data = {
        #"secretStr": wantTrainInfo[0],
        "train_date": travelInfo["train_date"],
        "back_train_date": back_date,
        "tour_flag": "dc",
        "purpose_codes": "ADULT",
        "undefined": "",
    }
    ''' "query_from_station_name": "广州",
        "query_to_station_name": "武汉", '''
    queryData = parse.urlencode(data) + "&" + "secretStr" + "=" + wantTrainInfo[trainIdxMap.secretStr]
    queryData = queryData + "&"+"query_from_station_name" + "=" + travelInfo["query_from_station_name"]
    queryData = queryData + "&"+"query_to_station_name" + "=" + travelInfo["query_to_station_name"]
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest",
        queryData)
    logger.info("retCode:[{}]".format(retCode))
    if retCode == 200:
        try:
            result = json.loads(retData.decode("utf-8"))
            logger.info("retData: [{}]".format(result))
        except:
            pass
"""
POST initDc https://kyfw.12306.cn/otn/confirmPassenger/initDc
_json_att:
响应信息里提取:  var globalRepeatSubmitToken = '41ccc1848d24018ea59ea2534dcb6ef6';
'key_check_isChange':'8826E8156DC5DFA8352ECDEF23F70EB4B71710F26D47E691207507E7'
"""
def getSubmitToken(browser):
    # browser.doGET("https://kyfw.12306.cn/otn/index/initMy12306")
    browser.headers["Referer"] = "https://kyfw.12306.cn/otn/leftTicket/init"
    data = {"_json_att": ""}
    headers = browser.headers
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/confirmPassenger/initDc", parse.urlencode(data))
    if retCode == 200:
        html = retData.decode("utf-8")
        logger.debug(html)
        matchs = re.findall(r"globalRepeatSubmitToken\s+=\s+'(\w+)'", html)
        logger.debug(matchs)
        browser.tokenParams["globalRepeatSubmitToken"] = matchs[0] if matchs else ""

        matchs = re.findall(r"'key_check_isChange'\s*:\s*'(\w+)'", html)
        logger.debug(matchs)
        browser.tokenParams["key_check_isChange"] = matchs[0] if matchs else ""

"""
POST 获取乘车人信息: https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs
参数列表:
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6
"""
def getPassengerInfo(browser, passengers):
    logger.info("获取乘客信息...")
    postData = {
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
    }
    ok = False
    while not ok:
        retCode, retData = browser.doGET("https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs", 
            parse.urlencode(postData))
        logger.info("retCode:[{}]".format(retCode))
        try:
            passengerData = json.loads(retData.decode("utf-8"))
            logger.debug("passengerData:{}".format(passengerData))
            logger.info("查找[{}]信息...".format(passengers))
            finded = []
            for item in passengerData["data"]["normal_passengers"]:
                logger.debug(item)
                if item["passenger_name"] in passengers:
                    finded.append(item)
            if len(finded) == 0:
                logger.info("[{}]不在乘客名单!".format(passengers))
                return choosePassenger(passengerData["data"]["normal_passengers"])
            return True, finded
        except:
            logger.info("获取乘客信息失败, 5秒后重新获取")
            time.sleep(5)


def choosePassenger(passengers):
    for idx, v in enumerate(passengers):
        print("[{}] {}".format(idx, v["passenger_name"]))
    validInput = False
    while not validInput:
        pssengerIdx = input("请输入乘客编号,以逗号分隔\n默认为[0]号乘客:\n")
        if len(pssengerIdx) == 0 :
            pssengerIdx = "0"
            validInput = True
        else:
            if re.match(r"[0-9]*(?:,[0-9]*)*", pssengerIdx):
                validInput = True
    pssengerList = []
    for idx in pssengerIdx.strip().strip(",").split(","):
        pssengerList.append(passengers[int(idx)])
    return True, pssengerList

"""
POST 订单信息: https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo
多个乘客以 "_" 分隔
passengerTicketStr:O,0,1,张三,1,身份证号码,电话号码,N_O,0,1,李四,1,身份证号码,电话号码,N
"M": "一等座","O": "二等座","1": "硬座","3": "硬卧","4": "软卧"
oldPassengerStr:张三,1,身份证号码,1_李四,1,身份证号码,1_
参数列表:
cancel_flag:2
bed_level_order_num:000000000000000000000000000000
passengerTicketStr:O,0,1,张三,1,身份证号码,电话号码,N
oldPassengerStr:张三,1,身份证号码,1_
tour_flag:dc  # dc: 单程
randCode:
whatsSelect:1
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6
返回:
{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":
{"ifShowPassCode":"N","canChooseBeds":"N","canChooseSeats":"Y","choose_Seats":"O9M",
"isCanChooseMid":"N","ifShowPassCodeTime":"1","submitStatus":true,"smokeStr":""},
"messages":[],"validateMessages":{}}
{'messages': [], 'validateMessages': {}, 'data': {'ifShowPassCodeTime': '2423', 'smokeStr': '', 
'ifShowPassCode': 'N', 'canChooseSeats': 'Y', 'submitStatus': True, 
'canChooseBeds': 'N', 'isCanChooseMid': 'N', 'choose_Seats': 'M9'}, 
'status': True, 'validateMessagesShowId': '_validatorMessage', 'httpstatus': 200}
{'validateMessagesShowId': '_validatorMessage', 'status': True, 'data': 
{'submitStatus': False, 'checkSeatNum': True, 'errMsg': '您选择了1位乘车人，但本次列车二等座仅剩0张。'}, 
'messages': [], 'httpstatus': 200, 'validateMessages': {}}
"""
def checkOrderInfo(browser, passengers, seatType="O"):
    # "passengerTicketStr": "O,0,1,张三,1,身份证号码,电话号码,N",
    passengerAttrList = []
    oldPassengerAttrList = []
    cnt = 0
    for person in passengers:
        if cnt > 0 : passengerAttrList.append("_")
        passengerAttrList.append(seatType)
        passengerAttrList.append(person["passenger_flag"])
        passengerAttrList.append(person["passenger_type"])
        passengerAttrList.append(person["passenger_name"])
        passengerAttrList.append(person["passenger_id_type_code"])
        passengerAttrList.append(person["passenger_id_no"])
        passengerAttrList.append(person["mobile_no"])
        passengerAttrList.append("N")

        # "oldPassengerStr": "张三,1,身份证号码,1_",
        oldPassengerAttrList = []
        oldPassengerAttrList.append(person["passenger_name"])
        oldPassengerAttrList.append(person["passenger_id_type_code"])
        oldPassengerAttrList.append(person["passenger_id_no"])
        oldPassengerAttrList.append("1_")
        cnt += 1
     
    postData = {
        "cancel_flag": "2",
        "bed_level_order_num": "000000000000000000000000000000",
        "passengerTicketStr": ",".join(passengerAttrList),
        "oldPassengerStr": ",".join(oldPassengerAttrList),
        "tour_flag": "dc",
        "randCode": "",
        "whatsSelect": "1",
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
    }
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo", 
            parse.urlencode(postData))
    logger.info("retCode:[{}]".format(retCode))
    if retCode == 200:
        try:
            result = json.loads(retData.decode("utf-8"))
            logger.info("返回车次座位信息: [{}]".format(result))
            flag = result["status"]
            if (isinstance(flag, str)   and flag.upper() == "TRUE") or \
                (isinstance(flag, bool) and flag):
                if "errMsg" in result["data"]:
                    logger.info("座位信息: [{}]".format(result["data"]["errMsg"]))
                    return False
                else:
                    logger.info("有满足需要的票: {}".format(result["data"]))
                    return True
            else:
                logger.info("座位信息获取失败: [{}]".format(result["message"]))
                return False
        except:
            return False

"""
POST 抢票队列: https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount
seatType:
"M": "一等座",
"O": "二等座",
"1": "硬座",
"3": "硬卧",
"4": "软卧",
参数列表:
train_date:Tue Jan 16 2018 00:00:00 GMT+0800 (中国标准时间)
train_no:6c000G11100C
stationTrainCode:G1110
seatType:O
fromStationTelecode:IZQ
toStationTelecode:WHN
leftTicket:OZR1tpi%2BCS0QS8hPbEkbAETALtfyHEorcZtzKm2GfmJfMqKMr78Z3Na4iWQ%3D
purpose_codes:00
train_location:Q9
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6
"""
def getQueueCount(browser, train):
    wantTrainInfo = train.split("|")
    logger.info("准备进入排队...")
    train_date = datetime.strptime(wantTrainInfo[trainIdxMap.train_date], "%Y%m%d").strftime("%a+%b+%d+%Y+") + \
        parse.quote("00:00:00") + "+" + parse.quote("GMT+0800") + "+(" + \
        parse.quote("中国标准时间") + ")"

    postData = {
        "train_no": wantTrainInfo[trainIdxMap.train_no],
        "stationTrainCode": wantTrainInfo[trainIdxMap.stationTrainCode],
        "seatType": "O",
        "fromStationTelecode": wantTrainInfo[trainIdxMap.fromStationTelecode],
        "toStationTelecode": wantTrainInfo[trainIdxMap.toStationTelecode],
        "purpose_codes": "00",
        "train_location": wantTrainInfo[trainIdxMap.train_location],
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
    }
    postData = parse.urlencode(postData) + "&" + "train_date=" + train_date + "&" + \
        "leftTicket=" + wantTrainInfo[trainIdxMap.leftTicket]
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount", 
             postData)
    logger.info("retCode:[{}]".format(retCode))
    if retCode == 200:
        try:
            result = json.loads(retData.decode("utf-8"))
            flag = result["status"]
            if (isinstance(flag, str) and flag.upper() == "TRUE") or \
                (isinstance(flag, bool) and flag):
                logger.info("抢票队列: [{}]".format(result))
                return True
            else:
                logger.info("抢票失败: [{}]".format(result["message"]))
                return False
        except:
            return False



"""
POST 验证队列: https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue
passengerTicketStr:O,0,1,张三,1,身份证号码,电话号码,N
oldPassengerStr:张三,1,身份证号码,1_
randCode:
purpose_codes:00
key_check_isChange:7819EDE21F4BC814E2D8A055CB8B42AAA841B68CAB88AAC06455045B
leftTicketStr:OZR1tpi%2BCS0QS8hPbEkbAETALtfyHEorcZtzKm2GfmJfMqKMr78Z3Na4iWQ%3D
train_location:Q9
choose_seats:1A [or""]
seatDetailType:000
whatsSelect:1
roomType:00
dwAll:N
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6
"""
def confirmSingleForQueue(browser, passengers, train, seatType="O"):
    logger.info("验证抢票队列...")
    passengerAttrList = []
    oldPassengerAttrList = []
    cnt = 0
    for person in passengers:
        if cnt > 0 : passengerAttrList.append("_")
        passengerAttrList.append(seatType)
        passengerAttrList.append(person["passenger_flag"])
        passengerAttrList.append(person["passenger_type"])
        passengerAttrList.append(person["passenger_name"])
        passengerAttrList.append(person["passenger_id_type_code"])
        passengerAttrList.append(person["passenger_id_no"])
        passengerAttrList.append(person["mobile_no"])
        passengerAttrList.append("N")

        # "oldPassengerStr": "张三,1,身份证号码,1_",
        oldPassengerAttrList = []
        oldPassengerAttrList.append(person["passenger_name"])
        oldPassengerAttrList.append(person["passenger_id_type_code"])
        oldPassengerAttrList.append(person["passenger_id_no"])
        oldPassengerAttrList.append("1_")
        cnt += 1
    wantTrainInfo = train.split("|")
    postData = {
        "passengerTicketStr": ",".join(passengerAttrList),
        "oldPassengerStr": ",".join(oldPassengerAttrList),
        "randCode": "",
        "purpose_codes": "00",
        "whatsSelect": "1",
        "key_check_isChange": browser.tokenParams["key_check_isChange"],
        "leftTicketStr": wantTrainInfo[trainIdxMap.leftTicket],
        "train_location": wantTrainInfo[trainIdxMap.train_location],
        "choose_seats": "",
        "seatDetailType": "000",
        "whatsSelect": "1",
        "roomType": "00",
        "dwAll": "N",
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
    }
    retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue", 
            parse.urlencode(postData))
    logger.info("retCode:[{}]".format(retCode))
    if retCode == 200:
        try:
            result = json.loads(retData.decode("utf-8"))
            logger.info("确认购买: [{}]".format(result))
            flag = result["status"]
            if (isinstance(flag, str) and flag.upper() == "TRUE") or \
                (isinstance(flag, bool) and flag):
                logger.info("进入队列: [{}]".format(result))
                return True
            else:
                logger.info("进入队列失败: [{}]".format(result["message"]))
                return False
        except:
            return False

"""
GET https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime
random:1515829299528
tourFlag:dc
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

POST https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue
orderSequence_no:EG02217919
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6
"""
def getMillSeconds():
    millSec = time.time() * 1000
    return str(millSec).split(".")[0]

def queryOrderWaitTime(browser):
    endQ = False
    while not endQ:
        millSec = getMillSeconds()
        data = {
            "random": millSec,
            "tourFlag": "dc",
            "_json_att": "",
            "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
        }
        retCode, retData = browser.doGET("https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime", 
                parse.urlencode(data))
        logger.info("retCode:[{}]".format(retCode))
        if retCode == 200:
            try:
                result = json.loads(retData.decode("utf-8"))
                logger.info("队列号: [{}]".format(result))
                if result["data"]["count"] == 0:
                    endQ = True
                    browser.tokenParams["orderSequence_no"] = result["data"]["orderId"]
            except:
                pass
        time.sleep(3)

"""
验证返回结果里的 'data':{'submitStatus': False}
"""
def resultOrderForDcQueue(browser):
    logger.info("查询订单状态:")
    if browser.tokenParams["orderSequence_no"] == "":
        logger.info("未买到票")
        return False
    if browser.tokenParams["orderSequence_no"] is None:
        return True
    data = {
        "orderSequence_no": browser.tokenParams["orderSequence_no"],
        "_json_att": "",
        "REPEAT_SUBMIT_TOKEN": browser.tokenParams["globalRepeatSubmitToken"],
    }
    
    ok = False
    while not ok:
        retCode, retData = browser.doPOST("https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue", 
            parse.urlencode(data))
        logger.info("retCode:[{}]".format(retCode))
        if retCode == 200:
            ok = True
            try:
                result = json.loads(retData.decode("utf-8"))
                flag = result["data"]["submitStatus"]
                if (isinstance(flag, str) and flag.upper() == "TRUE") or \
                    (isinstance(flag, bool) and flag):
                    logger.info("订单: [{}]".format(result))
                    
                    return True
                else:
                    return False
            except:
                pass
    return False

if "__main__" == __name__:
    my12306 = My12306()
    my12306.getStartPage()
    my12306.checkCaptcha()
    my12306.checkUser(myInfo.user, myInfo.passwd)
    my12306.doLogin()

    isGetTicket, validPassenger = False, False
    while not isGetTicket:
        trains = getTrainInfo(my12306, myInfo.wantTrains, **myInfo.travelInfo)
        logger.info("find trains:{}".format(trains))
        isAcceptOrder, isEnterQueue, isConfirmedQueue,  = False, False, False
        passengers = myInfo.passengers
        for train in trains:
            checkUser(my12306)
            submitOrderRequest(my12306, train, **myInfo.travelInfo)

            if my12306.tokenParams["globalRepeatSubmitToken"] == "":
                getSubmitToken(my12306)

            if not validPassenger:
                validPassenger, passengers = getPassengerInfo(my12306, passengers)
            logger.debug(passengers)

            isAcceptOrder = checkOrderInfo(my12306, passengers)
            if isAcceptOrder:
                isEnterQueue = getQueueCount(my12306, train)
                if isEnterQueue:
                    isConfirmedQueue = confirmSingleForQueue(my12306, passengers, train)
                    if isConfirmedQueue:
                        queryOrderWaitTime(my12306)
                        if(resultOrderForDcQueue(my12306)):
                            isGetTicket = True
                            sys.exit(0)