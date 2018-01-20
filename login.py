#!/usr/bin/env python3
#-*- coding:utf-8 -*-
"""
登陆流程:
获取验证码 -> 校验验证码 -> 校验帐号密码 -> 登陆成功
"""

from urllib import request, parse
from http import cookiejar
from collections import namedtuple
from PIL import Image
import json, random, ssl, tempfile, os, time, sys, re
from myLogger import logger

try:
    import myInfo
except ImportError:
    class myInfo:
        user = "abcd"
        passwd = "123456"

ssl._create_default_https_context = ssl._create_unverified_context

class MyHTTPRedirectHandler(request.HTTPRedirectHandler, request.HTTPCookieProcessor):
    def http_error_301(self, req, fp, code, msg, httpmsg):
        logger.debug(req)
        logger.debug(httpmsg)
        return request.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, httpmsg)
    def http_error_302(self, req, fp, code, msg, httpmsg):
        logger.debug(req)
        logger.debug(httpmsg)
        return request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, httpmsg)

class My12306(object):
    _cj = cookiejar.LWPCookieJar()
    _opener = request.build_opener(MyHTTPRedirectHandler(_cj))
    ''' 
    8张图片模型 67*67 间隔为 5px
    -----------------
    |png|png|png|png|
    -----------------
    |png|png|png|png|
    -----------------
    各图片左上角对应坐标
    5,5  77,5  149,5  221,5
    5,77 77,77 149,77 221,77 
    '''
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
                AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
            "Host":       "kyfw.12306.cn",
            "Connection": "keep-alive",
        }
        self.cookie = {"Cookie": ""}
        self.tokenParams = {
            "tk": "",
            "newapptk": "",
            "globalRepeatSubmitToken": "",
            "key_check_isChange": "",
            "orderSequence_no": "",
        }
        self._startPage  = "https://kyfw.12306.cn/otn/login/init"
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
    
    # http.client.IncompleteRead: IncompleteRead(20241 bytes read, 2514 more expected)
    def doGET(self, url, data=None, headers=None):
        if data is not None: 
            url = url + "?" + data
        logger.debug("cookie: [{}]".format(self._cj))
        logger.info("GET: [{}]".format(url))
        if headers is None: headers = self.headers
        req = request.Request(url, headers=headers)
        try:
            with My12306._opener.open(req) as f:
                return f.status, f.read()
        except:
            return 400, iter("")

    def doPOST(self, url, data, headers=None):
        if headers is None: headers = self.headers
        req = request.Request(url, headers=headers)
        logger.debug("cookie: [{}]".format(self._cj))
        logger.info("POST: [{}] ,data [{}]".format(url, data))
        try:
            with My12306._opener.open(req, data=data.encode("utf-8")) as f:
                return f.status, f.read()
        except:
            return 400, iter("")
    
    # 一切从这里开始
    def getStartPage(self):
        self.doGET(self._startPage)

    def getCaptchaImg(self):
        while True:
            captchaImgData = {
                "login_site": "E",
                "module": "login",
                "rand": "sjrand",
                random.random(): ""
            }
            retCode, retData = self.doGET(self._captchaImg, parse.urlencode(captchaImgData))
            logger.info("retCode:{}".format(retCode))
            
            if retCode == 200:
                png = os.path.join(self._tmp, "captcha.png")
                logger.info("保存图片为:{}".format(png))
                with open(png, "wb") as fw:
                    fw.write(retData)
            try:
                img = Image.open(png)
            except:
                logger.info("未获取到验证码，重新获取...")
                continue
            yield img.show()

    def getPosInfo(self):
        validInput = False
        while not validInput:
            posInput = input("""请输入图片位置,如 1,3,6:\n1|2|3|4\n5|6|7|8\n以逗号分隔(默认为1):\n""")
            if len(posInput) == 0 :
                posInput = "1"
                validInput = True
            else:
                if re.match(r"[1-8](?:,[1-8])*", posInput):
                    validInput = True
        posList = []
        for pos in posInput.strip().strip(",").split(","):
            posList.append(random.randint(self._posMap[pos][0].a, self._posMap[pos][0].b))
            posList.append(random.randint(self._posMap[pos][1].a, self._posMap[pos][1].b)) 
        return ",".join([str(x) for x in posList])
        
    '''
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
    '''
    def checkCaptcha(self):
        ok = False
        g = self.getCaptchaImg()
        g.send(None)
        while not ok:
            # g = self.getCaptchaImg()
            posInfo = self.getPosInfo()
            captchaForm = {
                "answer": posInfo,
                "login_site": "E",
                "rand": "sjrand",
            }
            logger.debug(captchaForm)
            retCode, retData = self.doPOST(self._captchaChk, parse.urlencode(captchaForm))
            logger.info("retCode:[{}]".format(retCode))
            if retCode == 200:
                try:
                    result = json.loads(retData.decode("utf-8"))
                    logger.info("retData:[{}]".format(result))
                    if result["result_code"] == "4":
                        ok = True
                        break
                except:
                    pass
            g.send(None)
        g.close()
        logger.info("验证码校验成功, 尝试登陆")
    '''
    POST 帐号密码: https://kyfw.12306.cn/passport/web/login
    返回: {"result_message":"登录名不存在。","result_code":1}
    成功后返回: {"result_message":"登录成功","result_code":0,"uamtk":"VEqbgNHudMa-N1meoVuv0x9eL-MXBCP5gat1t0"}
    login 验证结果
        登录名不存在  result_code:1
        登录成功 result_code:0 
    '''
    def checkUser(self, user="12306", passwd="123456"):
        loginForm = {
            "username": user,
            "password": passwd,
            "appid": "otn",
        }
        logger.info("发送登录数据: {}".format(loginForm))
        ok = False
        while not ok:
            retCode, retData = self.doPOST(self._loginURL, parse.urlencode(loginForm))
            if retCode == 200:
                logger.debug(retData.decode("utf-8"))
                try:
                    result = json.loads(retData.decode("utf-8"))
                    if result["result_code"] == 0:
                        logger.info("用户名和密码验证通过")
                        ok = True
                        self.tokenParams["tk"] = result["uamtk"]
                    else:
                        logger.info(result["result_message"])
                        sys.exit(1)
                except json.decoder.JSONDecodeError as e:
                    logger.debug("json parse failed: {}".format(e))
                    time.sleep(2)
                except UnicodeDecodeError as e:
                    logger.debug("[{}]".format(e))
    '''
    POST uamtk: https://kyfw.12306.cn/passport/web/auth/uamtk
    request Headers [Referer:https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin]
    参数: appid:otn
    返回: {"result_message":"验证通过","result_code":0,"apptk":null,"newapptk":"OJ-LJPr1VyujjZUEsekzuT-Ll42Fb5LKbct1t0"}

    POST uamauthclient: https://kyfw.12306.cn/otn/uamauthclient
    request Headers [Referer:https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin]
    参数:(上一步的 uamtk)  tk:UV5AG4BN2u9zna6l5QHTQws_Ft2THVB4kot2t0
    返回: {"result_code":2,"result_message":"uamtk票据内容为空"}
    成功后返回:
    apptk=FUMjBieik2NEM2kc01s6uxls94vbBW4brwt1t0
    result_code=0
    result_message=验证通过
    username=张三
    '''
    def doLogin(self):
        headers = self.headers
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        retCode, retData = self.doPOST("https://kyfw.12306.cn/otn/login/userLogin", 
            parse.urlencode({"_json_att": ""}), headers=headers)
        # logger.debug("retCode:[{}], retData:[{}]".format(retCode, retData.decode("utf-8", errors="ignore")))

        logger.info("尝试 uamtk 验证...")
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        
        ok = False
        while not ok:
            retCode, retData = self.doPOST("https://kyfw.12306.cn/passport/web/auth/uamtk", 
                parse.urlencode({"appid": "otn"}), headers=headers)
            if retCode == 200:
                logger.debug("retCode:[{}], retData:[{}]".format(retCode, retData.decode("utf-8")))
                try:
                    result = json.loads(retData.decode("utf-8"))
                    if result["result_code"] == 0:
                        logger.info("uamtk 验证通过")
                        ok = True
                        self.tokenParams["newapptk"] = result["newapptk"]
                    else:
                        return result["result_message"]
                except:
                    pass

        logger.info("尝试 uamauthclient 验证...")
        
        ok = False
        while not ok:
            retCode, retData = self.doPOST("https://kyfw.12306.cn/otn/uamauthclient", 
                parse.urlencode({"tk": self.tokenParams["newapptk"]}), headers=headers)
            if retCode == 200:
                logger.debug("retCode:[{}], retData:[{}]".format(retCode, retData.decode("utf-8")))
                try:
                    result = json.loads(retData.decode("utf-8"))
                    if result["result_code"] == 0:
                        logger.info("uamauthclient 验证通过")
                        ok = True
                        logger.info("成功登录12306, 用户名[{}], 可以买票了".format(result["username"]))
                    else:
                        return result["result_message"]
                except:
                    pass

        self.afterLogin()

    def afterLogin(self):
        headers = self.headers
        # headers["Content-type"] = "text/html"
        headers["Referer"] = "https://kyfw.12306.cn/otn/passport?redirect=/otn/login/userLogin"
        retCode, retData = self.doGET("https://kyfw.12306.cn/otn/index/initMy12306", headers=headers)
        
        headers["Referer"] = "https://kyfw.12306.cn/otn/index/initMy12306"
        retCode, retData = self.doGET("https://kyfw.12306.cn/otn/leftTicket/init", headers=headers)
        logger.debug("retCode:[{}]".format(retCode))
        if retCode == 200:
            with open("initMy12306.html", "wb") as fw:
                fw.write(retData)
        

        headers["Referer"] = "https://kyfw.12306.cn/otn/leftTicket/init"
        self.doGET("https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew",
            parse.urlencode({
                "module": "passenger",
                "rand": "randp",
                random.random(): "",
            }), headers=headers)

if __name__ == "__main__":
    my12306 = My12306()
    my12306.getStartPage()
    my12306.checkCaptcha()
    my12306.checkUser(myInfo.user, myInfo.passwd)
    my12306.doLogin()
    