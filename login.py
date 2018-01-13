#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"""
登陆流程:
校验验证码 -> 校验帐号密码 -> 登陆成功
GET  验证码:
https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.3638160110014952

POST 请求
验证码校验: https://kyfw.12306.cn/passport/captcha/captcha-check
校验结果:
    验证码校验成功  ret_code:4
    验证码校验失败  ret_code:5
    验证码校验失败,信息为空  ret_code:8
参数:
answer:42,38,253,34,54,116
login_site:E
rand:sjrand

8张图片模型
-----------------
|   |   |   |   |
-----------------
|   |   |   |   |
-----------------
各图片左上角对应坐标
0,0  80,0  160,0  240,0
0,80 80,80 160,80 240,80
"""

from urllib import request, parse
import logging;logging.basicConfig(level=logging.DEBUG)

captchaImg = "https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.3638160110014952"
captchaURL = "https://kyfw.12306.cn/passport/captcha/captcha-check"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.3",
    "Referer":    "https://kyfw.12306.cn/otn/login/init",
    "Host":       "kyfw.12306.cn",
    "X-Requested-With": "XMLHttpRequest",
    }
data = {
    "answer": "42,38,253,34,54,116",
    "login_site": "E",
    "rand": "sjrand",
}
postData = parse.urlencode(data)
logging.debug(postData)
req = request.Request(captchaImg, headers=headers)
with request.urlopen(req) as f:
    bImg = f.read()
    logging.debug(bImg)
    with open("captcha.png", "wb") as fw:
        fw.write(bImg)

req = request.Request(captchaURL, headers=headers)
with request.urlopen(req, data=postData.encode("utf-8")) as f:
    logging.debug(f.read().decode("utf-8"))