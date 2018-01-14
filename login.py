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

8张图片模型 67*67 间隔为 5px
-----------------
|png|png|png|png|
-----------------
|png|png|png|png|
-----------------
各图片左上角对应坐标
5,5  77,5  149,5  221,5
5,77 77,77 149,77 221,77

POST 帐号密码: https://kyfw.12306.cn/passport/web/login
login 验证结果
    登录名不存在  result_code:1
    登录成功 result_code:0

登陆成功后:
POST userLogin: https://kyfw.12306.cn/otn/login/userLogin
request Headers [Referer:https://kyfw.12306.cn/otn/login/init]
参数:
_json_att:

POST uamtk: https://kyfw.12306.cn/passport/web/auth/uamtk
request Headers [Referer:https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin]
参数:
appid:otn

POST uamauthclient: https://kyfw.12306.cn/otn/uamauthclient
request Headers [Referer:https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin]
参数:
tk:UV5AG4BN2u9zna6l5QHTQws_Ft2THVB4kot2t0

GET userLogin: https://kyfw.12306.cn/otn/login/userLogin
request Headers [Referer:https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin]


"""

from urllib import request, parse
from http import cookiejar
from requests import cookies
from collections import namedtuple
from PIL import Image
from multiprocessing import Process, Queue
import json, random, ssl, tempfile, os, time
import my12306
import logging;logging.basicConfig(level=logging.DEBUG)
ssl._create_default_https_context = ssl._create_unverified_context

class MyHTTPRedirectHandler(request.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, httpmsg):
        logging.debug(req)
        logging.debug(httpmsg)
        return request.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, httpmsg)
    def http_error_302(self, req, fp, code, msg, httpmsg):
        logging.debug(req)
        logging.debug(httpmsg)
        return request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, httpmsg)

class Browser(object):
    # _cj = cookiejar.LWPCookieJar()
    _cj = cookies.RequestsCookieJar()
    _opener = request.build_opener(request.HTTPCookieProcessor(_cj))
    _headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "Host":       "kyfw.12306.cn",
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }

    def __init__(self):
        self._captchaImg = "https://kyfw.12306.cn/passport/captcha/captcha-image"
        self._captchaChk = "https://kyfw.12306.cn/passport/captcha/captcha-check"
        self._loginURL   = "https://kyfw.12306.cn/passport/web/login"
        self._tmp = tempfile.mkdtemp(prefix="12306_", suffix="_png")
        Point = namedtuple("Point", ["a", "b"])
        # 取坐标点不要超过点的范围
        self._posMap = {
            "1": (Point(20, 60),  Point(20, 60)),
            "2": (Point(100,140), Point(20, 60)),
            "3": (Point(170,210), Point(20, 60)),
            "4": (Point(250,280), Point(20, 60)),
            "5": (Point(20, 60),  Point(90, 140)),
            "6": (Point(100,140), Point(90, 140)),
            "7": (Point(170,210), Point(90, 140)),
            "8": (Point(250,280), Point(90, 140)),
        }

    def makeUrlData(self, data):
        return parse.urlencode(data)

    def doGET(self, url, data=None):
        if data is not None: 
            url = url + "?" + data
        logging.debug("GET: [{}]".format(url))
        req = request.Request(url, headers=Browser._headers)
        with Browser._opener.open(req) as f:
            return f.status, f.read()

    def doPOST(self, url, data):
        req = request.Request(url, headers=Browser._headers)
        logging.debug("POST: [{}] ,data [{}]".format(url, data))
        with Browser._opener.open(req, data=data.encode("utf-8")) as f:
            return f.status, f.read()

    def getCaptchaImg(self):
        captchaImgData = {
            "login_site": "E",
            "module": "login",
            "rand": "sjrand",
            random.random(): ""
        }
        retCode, retData = self.doGET(self._captchaImg, parse.urlencode(captchaImgData))
        ''' url = self._captchaImg + "?" + parse.urlencode(captchaImgData)
        req = request.Request(url)
        with request.urlopen(req) as f:
            logging.debug("getheaders:")
            for k, v in f.getheaders():
                logging.debug("[{}]:[{}]".format(k, v))
            retCode, retData = f.status, f.read() '''
        logging.info("retCode:{}".format(retCode))
        
        if retCode == 200:
            fpath = os.path.join(self._tmp, "captcha.png")
            logging.info("保存图片为:{}".format(fpath))
            with open(fpath, "wb") as fw:
                fw.write(retData)
        try:
            img = Image.open(fpath)
            img.show()
        except:
            raise "未获取到验证码，请重新获取"

    def getPosInfo(self):
        posInput = input("""请输入图片位置,如 1,3,6:\n1|2|3|4\n5|6|7|8\n以逗号分隔(默认为1):\n""")
        if len(posInput) == 0 :
            posInput = "1"
        posList = []
        for pos in posInput.strip().split(","):
            posList.append(random.randint(self._posMap[pos][0].a, self._posMap[pos][0].b))
            posList.append(random.randint(self._posMap[pos][1].a, self._posMap[pos][1].b)) 
        return ",".join([str(x) for x in posList])
        

    def checkCaptcha(self):
        result = {}
        result["result_code"] = "5"
        while result["result_code"] != "4":
            self.getCaptchaImg()
            posInfo = self.getPosInfo()
            captchaForm = {
                "answer": posInfo,
                "login_site": "E",
                "rand": "sjrand",
            }
            logging.debug(captchaForm)
            retCode, retData = self.doPOST(self._captchaChk, parse.urlencode(captchaForm))
            logging.info("retCode:[{}]".format(retCode))
            if retCode == 200:
                try:
                    result = json.loads(retData.decode("utf-8"))
                    logging.info("retData:[{}]".format(result))
                except:
                    result["result_code"] = "5"
        logging.info("验证码校验成功, 尝试登陆")

    def doLogin2(self, user="12306", passwd="123456"):
        loginForm = {
            "username": user,
            "password": passwd,
            "appid": "otn",
        }
        logging.debug(loginForm)
        logging.debug(Browser._cj)
        retCode, retData = self.doPOST(self._loginURL, parse.urlencode(loginForm))
        if retCode == 200:
            logging.debug(retData.decode("utf-8"))
            try:
                result = json.loads(retData.decode("utf-8"))
            except json.decoder.JSONDecodeError as e:
                logging.error("json parse failed: {}".format(e))
        logging.debug("cookie:[{}]".format(Browser._cj))
        retCode, retData = self.doPOST("https://kyfw.12306.cn/otn/login/userLogin", parse.urlencode({"_json_att":""}))
        logging.info("retCode:{}".format(retCode))
        retCode, retData = self.doPOST("https://kyfw.12306.cn/passport/web/auth/uamtk", parse.urlencode({"appid":"otn"}))
        logging.info("retCode:{}".format(retCode))

    def doLogin(self, user="12306", passwd="123456"):
        loginForm = {
            "username": user,
            "password": passwd,
            "appid": "otn",
        }
        logging.debug(loginForm)
        cookie = "; ".join(k + "=" + v for k, v in Browser._cj.iteritems())
        result = {}
        result["result_code"] = "5"
        while result["result_code"] != 0:
            opener = request.build_opener(MyHTTPRedirectHandler)
            headers = Browser._headers
            headers["Cookie"] = cookie
            # headers["Referer"] = "https://kyfw.12306.cn/otn/login/init"
            req = request.Request(self._loginURL, headers=headers)
            with opener.open(req, data=parse.urlencode(loginForm).encode("utf-8") ) as f:
                logging.info("retCode:{}".format(f.status))
                retData = f.read()
                if f.status == 200:
                    logging.debug(retData.decode("utf-8"))
                    try:
                        result = json.loads(retData.decode("utf-8"))
                        logging.info("登陆成功, 可以买票了")
                    except json.decoder.JSONDecodeError as e:
                        logging.error("json parse failed: {}".format(e))
                        time.sleep(2)
        # logging.debug("cookie:[{}]".format(Browser._cj))



if __name__ == "__main__":
    bwr = Browser()
    bwr.checkCaptcha()
    bwr.doLogin(my12306.user, my12306.passwd)
    