#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"""
登陆流程:
获取验证码 -> 校验验证码 -> 校验帐号密码 -> 登陆成功

GET  验证码: https://kyfw.12306.cn/passport/captcha/captcha-image
参数:
login_site:E
module:login
rand:sjrand
0.3638160110014952

POST 验证码校验: https://kyfw.12306.cn/passport/captcha/captcha-check
校验结果: result_message
    验证码校验成功  ret_code:4
    验证码校验失败  ret_code:5
    验证码已经过期  ret_code:7
    验证码校验失败,信息为空  ret_code:8
参数:
answer:42,38,253,34,54,116
login_site:E
rand:sjrand

8张图片模型
-----------------
|png|png|png|png|
-----------------
|png|png|png|png|
-----------------
各图片左上角对应坐标
0,0  80,0  160,0  240,0
0,80 80,80 160,80 240,80

POST 帐号密码: https://kyfw.12306.cn/passport/web/login
login 验证结果
    登录名不存在  result_code:1
"""

from urllib import request, parse
from http import cookiejar
from collections import namedtuple
import json, random, ssl
import my12306
import logging;logging.basicConfig(level=logging.DEBUG)

ssl._create_default_https_context = ssl._create_unverified_context
c = cookiejar.LWPCookieJar()
cookie = request.HTTPCookieProcessor(c)
opener = request.build_opener(cookie)

captchaImg = "https://kyfw.12306.cn/passport/captcha/captcha-image"
captchaChk = "https://kyfw.12306.cn/passport/captcha/captcha-check"
loginURL   = "https://kyfw.12306.cn/passport/web/login"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    "Referer":    "https://kyfw.12306.cn/otn/login/init",
    "Host":       "kyfw.12306.cn",
    "X-Requested-With": "XMLHttpRequest",
    }

captchaImgData = {
    "login_site": "E",
    "module": "login",
    "rand": "sjrand",
    random.random(): ""
}
captchaImgData = parse.urlencode(captchaImgData)
logging.debug(captchaImgData)
req = request.Request(captchaImg + "?" + captchaImgData, headers=headers)
with opener.open(req) as f:
    bImg = f.read()
    logging.debug(bImg)
    with open("captcha.png", "wb") as fw:
        fw.write(bImg)

posInput = input("""
请输入图片位置:
1|2|3|4
5|6|7|8
以逗号分隔:
""")
Point = namedtuple("Point", ["a", "b"])
posMap = {
    "1": (Point(20, 60),  Point(20, 60)),
    "2": (Point(100,140), Point(20, 60)),
    "3": (Point(170,210), Point(20, 60)),
    "4": (Point(250,280), Point(20, 60)),
    "5": (Point(20, 60),  Point(90, 140)),
    "6": (Point(100,140), Point(90, 140)),
    "7": (Point(170,210), Point(90, 140)),
    "8": (Point(250,280), Point(90, 140)),
}
posList = []
for pos in posInput.strip().split(","):
    posList.append(random.randint(posMap[pos][0].a, posMap[pos][0].b))
    posList.append(random.randint(posMap[pos][1].a, posMap[pos][1].b))

captchaForm = {
    "answer": ",".join([str(x) for x in posList]),
    "login_site": "E",
    "rand": "sjrand",
}
captchaData = parse.urlencode(captchaForm)
logging.debug(captchaData)

result = ""
req = request.Request(captchaChk, headers=headers)
with opener.open(req, data=captchaData.encode("utf-8")) as f:
    data = f.read().decode("utf-8")
    logging.debug(data)
    try:
        result = json.loads(data)
    except:
        result["result_code"] = 5

if result["result_code"] == "4":
    logging.info("验证码校验成功")
    loginForm = {
        "username": my12306.user,
        "password": my12306.passwd,
        "appid": "otn",
    }
    loginData = parse.urlencode(loginForm)
    logging.debug(loginData)
    headers["Content-Length"] = len(loginData)
    req = request.Request(loginURL, headers=headers)
    with opener.open(req, data=loginData.encode("utf-8")) as f:
        data = f.read().decode("utf-8")
        logging.debug(data)
        try:
            result = json.loads(data)
        except json.decoder.JSONDecodeError as e:
            logging.error("json parse failed: {}".format(e))
else:
    logging.info("验证码校验失败")