## 12306购票流程解析
---
未实现验证码自动识别，登录时需要手动输入，购票时也一样
### step1 获取cookie并保存
GET https://kyfw.12306.cn/otn/login/init
一般不会失败
### step2 带cookie抓取login验证码并保存
GET https://kyfw.12306.cn/passport/captcha/captcha-image
发送参数:
>login_site:E
module:login
rand:sjrand
0.3638160110014952

**0.3638160110014952** 可用 random.random() 计算
一般不会失败，否则重试

### step3 验证login验证码
POST https://kyfw.12306.cn/passport/captcha/captcha-check
发送参数:
>answer:42,38,253,34,54,116
login_site:E
rand:sjrand

**answer** 后跟图片里的坐标点
>8张图片模型 67*67 间隔为 5px

|png|png|png|png|
|png|png|png|png|

>各图片左上角对应坐标
5,5  77,5  149,5  221,5
5,77 77,77 149,77 221,77

返回json:
>{'result_message': '验证码校验成功', 'result_code': '4'}

验证码校验成功  ret_code:4
验证码校验失败  ret_code:5
验证码已经过期  ret_code:7
验证码校验失败,信息为空  ret_code:8

校验 result_code, 不为4则返回 step2

### step4 验证用户名密码
POST https://kyfw.12306.cn/passport/web/login
发送参数:
>username=user&password=passwd&appid=otn

验证成功返回json:
>{"result_message":"登录成功","result_code":0,"uamtk":"VEqbgNHudMa-N1meoVuv0x9eL-MXBCP5gat1t0"}

失败返回:
>{"result_message":"登录名不存在。","result_code":1}

校验 result_code, 不为0则返回 step2。
这一步的 uamtk 保存，带到后面的 POST 参数里

### step5 登录动作
POST https://kyfw.12306.cn/otn/login/userLogin
headers 带上 "Content-Type":"application/x-www-form-urlencoded"
发送参数:
>_json_att=

### step6 验证 uamtk
POST https://kyfw.12306.cn/passport/web/auth/uamtk
发送参数:
>appid:otn

返回json:
>{"result_message":"验证通过","result_code":0,"apptk":null,"newapptk":"FUMjBieik2NEM2kc01s6uxls94vbBW4brwt1t0"}

判断 result_code 是否为0
保存此处的 apptk , 下一步带上

### step7 验证 uamauthclient
POST https://kyfw.12306.cn/otn/uamauthclient
发送参数:
>tk=FUMjBieik2NEM2kc01s6uxls94vbBW4brwt1t0

这里的 tk 是 step6 的 apptk
成功后返回(以下是已经解析过的json):
>apptk=FUMjBieik2NEM2kc01s6uxls94vbBW4brwt1t0
result_code=0
result_message=验证通过
username=张三

失败则:
> {"result_code":2,"result_message":"uamtk票据内容为空"}

这一步验证通过，就是真正登录成功，可以买票了。

从 step4 到 step7, 脚本里经常返回一个错误页面:http://www.12306.cn/mormhweb/logFiles/error.html, 在浏览器登录却没有这个。

### step8 获取站点编码表(不登录也可以)
GET https://kyfw.12306.cn/otn/resources/js/framework/station_name.js
发送参数:
>station_version=1.9044

返回一坨json...

### step9 查询余票
GET https://kyfw.12306.cn/otn/leftTicket/queryZ
发送数据:
>"leftTicketDTO.train_date":   destDat,
"leftTicketDTO.from_station": "GZQ",
"leftTicketDTO.to_station":   "WHN",
"purpose_codes":              "ADULT"

返回的一坨json里有车次列表:
几个对应关系(人话 索引):
>车次 3  发车时间 8 到达 9 历时 10 发车日期 13 是否可预订 11
商务 32 一等 31 二等 30
无座 26 软卧 23 硬卧 28 硬座 29

### step10 发送订单信息
首先验证用户是否已登录:
POST https://kyfw.12306.cn/otn/login/checkUser
发送参数:
>_json_att=

返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"flag":true},"messages":[],"validateMessages":{}}

验证 result["data"]["flag"] 是否为 true

POST https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest
发送参数:
>secretStr=9YXJREQTn7FpxrpnjYe%2BKmcbV1UFxzCX%2BhoKgtd0GPhDS0BJgWvO1R1MQ5lTZ%2FX%2BHy7l7TSNLXqz%0Aqgc7zM9mhQOF0s6fN%2F3d6iKEPuco8QDgOGGyoxCEGSmhS%2FsIq6SgdBFIZHUeGh%2BKM6UgJdZCSGbH%0AadZyYPs0Tqb1S9yj3WbKhZmAkrZgDHjuRJFsepfSKbkBzCT8Nuvdle%2BgKG%2BZM7h7OISADPNGgBFH%0A2evh8a43gpwITXD01Y%2F%2BfVRbQCzP&train_date=2018-02-05&back_train_date=2018-01-15&tour_flag=dc&purpose_codes=ADULT&query_from_station_name=广州&query_to_station_name=武汉&undefined

secretStr 是 step9 里车次信息 0 索引
注意使用 urlencode 编码时要将 secretStr query_from_station_name query_to_station_name 排除在外，编码后再用字符串连接。
**dc** 代表单程
**ADULT** 表示成人
例如:
```
    data = {
        #"secretStr": wantTrainInfo[0],
        "train_date": destDate,
        "back_train_date": back_date,
        "tour_flag": "dc",
        "purpose_codes": "ADULT",
        "undefined": "",
    }
    queryData = parse.urlencode(data) + "&" + "secretStr" + "=" + wantTrainInfo[0]
    queryData = queryData + "&"+"query_from_station_name" + "=" + "广州"
    queryData = queryData + "&"+"query_to_station_name" + "=" + "武汉"
```
成功后返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":"N","messages":[],"validateMessages":{}}

判断这一步的 result["ststus"]

### step11 跳转到 initDc
POST https://kyfw.12306.cn/otn/confirmPassenger/initDc
发送参数:
>_json_att:

返回的 html 里提取 globalRepeatSubmitToken 和 key_check_isChange:
>var globalRepeatSubmitToken = '41ccc1848d24018ea59ea2534dcb6ef6';
'key_check_isChange':'8826E8156DC5DFA8352ECDEF23F70EB4B71710F26D47E691207507E7'

使用正则提取:
```
re.findall(r"globalRepeatSubmitToken\s+=\s+'(\w+)'", html)
re.findall(r"'key_check_isChange'\s*:\s*'(\w+)'", html)
```


### step12 拉取乘车人信息
POST https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs
发送参数:
>_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

这里的 *REPEAT_SUBMIT_TOKEN* 就是 step11 里提取的 globalRepeatSubmitToken

返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,
"httpstatus":200,"data":{"isExist":true,"exMsg":"","two_isOpenClick":["93","95","97","99"],
"other_isOpenClick":["91","93","98","99","95","97"],
"normal_passengers":[
{"code":"4","passenger_name":"张三","sex_code":"M","sex_name":"男","born_date":"2000-01-01 00:00:00",
"country_code":"CN","passenger_id_type_code":"1","passenger_id_type_name":"二代身份证","passenger_id_no":"二代身份证",
"passenger_type":"1","passenger_flag":"0","passenger_type_name":"成人","mobile_no":"电话","phone_no":"","email":"zhangsan@qq.com",
"address":"","postalcode":"","first_letter":"ZS","recordCount":"12","total_times":"99","index_id":"0"}],"dj_passengers":[]},"messages":[],"validateMessages":{}}

关注以下数据:
passenger_flag, passenger_type, passenger_name, passenger_id_type_code, passenger_id_no, mobile_no

### step13 拉取验证码
GET https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=passenger&rand=randp&0.8263549525374525
不解释

### step14 购票人确定
POST https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo
发送参数:
>cancel_flag:2
bed_level_order_num:000000000000000000000000000000
passengerTicketStr:O,0,1,张三,1,身份证号码,电话号码,N
oldPassengerStr:张三,1,身份证号码,1_
tour_flag:dc
randCode:
whatsSelect:1
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

返回座位信息:
>{'messages': [], 'validateMessages': {}, 'data': {'ifShowPassCodeTime': '2423', 'smokeStr': '', 
'ifShowPassCode': 'N', 'canChooseSeats': 'Y', 'submitStatus': True, 
'canChooseBeds': 'N', 'isCanChooseMid': 'N', 'choose_Seats': 'M9'}, 
'status': True, 'validateMessagesShowId': '_validatorMessage', 'httpstatus': 200}

关注 result["status"] 是否为 True，失败返回 step9
检查此处的 ifShowPassCode 为 Y 时，要验证验证码

### setp15 准备排队
POST https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount
发送参数:
>train_date:Tue Jan 16 2018 00:00:00 GMT+0800 (中国标准时间)
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

seatType 参考:
>"M": "一等座",
"O": "二等座",
"1": "硬座",
"3": "硬卧",
"4": "软卧",

这里POST发送的数据:
>train_date=Mon+Feb+05+2018+00%3A00%3A00+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&train_no=65000K410802&stationTrainCode=K4108&seatType=1&fromStationTelecode=GGQ&toStationTelecode=WCN&leftTicket=pbz2PUAqde3BnjcovsWlAHEMQpH2Q3TNonGIce%252F%252FCCFvkhXD&purpose_codes=00&train_location=Q7&_json_att=&REPEAT_SUBMIT_TOKEN=15f6179ae0daa85a6c17a0fa17d24462

train_date 不能直接由 parse.urlencode() 生成，用了如下方式:
```
    train_date = datetime.strptime(wantTrainInfo[13], "%Y%m%d").strftime("%a+%b+%d+%Y+") + \
        parse.quote("00:00:00") + "+" + parse.quote("GMT+0800") + "+(" + \
        parse.quote("中国标准时间") + ")"
    postData = parse.urlencode(postData) + "&" + "train_date=" + train_date + "&" +  "leftTicket=" + wantTrainInfo[12]
```
返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"count":"0","ticket":"2,1146","op_2":"false","countT":"0","op_1":"false"},"messages":[],"validateMessages":{}}

此步检查 result["status"] 是否为 true

### step16 确认购买
POST https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue
发送参数:
>passengerTicketStr:O,0,1,张三,1,身份证号码,电话号码,N
oldPassengerStr:张三,1,身份证号码,1_
randCode:
purpose_codes:00
key_check_isChange:7819EDE21F4BC814E2D8A055CB8B42AAA841B68CAB88AAC06455045B
leftTicketStr:OZR1tpi%2BCS0QS8hPbEkbAETALtfyHEorcZtzKm2GfmJfMqKMr78Z3Na4iWQ%3D
train_location:Q9
choose_seats:""
seatDetailType:000
whatsSelect:1
roomType:00
dwAll:N
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"submitStatus":true},"messages":[],"validateMessages":{}}

此步检查 result["status"] 是否为 true

### step17 每5秒查询排队
GET https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime
发送参数:
>random:1515829299528
tourFlag:dc
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"queryOrderWaitTimeStatus":true,"count":66,"waitTime":4,"requestId":6358601029630191520,"waitCount":1,"tourFlag":"dc","orderId":null},"messages":[],"validateMessages":{}}
{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"queryOrderWaitTimeStatus":true,"count":0,"waitTime":-1,"requestId":6358601029630191520,"waitCount":0,"tourFlag":"dc","orderId":"EG03339181"},"messages":[],"validateMessages":{}}

**random** 为毫秒数，可用以下代码获取
```
def getMillSeconds():
    millSec = time.time() * 1000
    return str(millSec).split(".")[0]
```
循环检查 result["data"]["count"]是否为0，为0时排队结束，可以查询购票结果，orderId 即为订单号

### step18 查询订单
POST https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue
发送参数:
>orderSequence_no:上一步的**orderId**
_json_att:
REPEAT_SUBMIT_TOKEN:41ccc1848d24018ea59ea2534dcb6ef6

返回json:
>{"validateMessagesShowId":"_validatorMessage","status":true,"httpstatus":200,"data":{"submitStatus":true},"messages":[],"validateMessages":{}}

检查 result["status"] 是否为 true

### 流程完毕

