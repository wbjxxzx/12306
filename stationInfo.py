#!/usr/bin/env python3
#-*- coding:utf-8 -*-

from pprint import pprint
from urllib import request, parse
import json, sys
import logging
logging.basicConfig(level=logging.DEBUG)

def formatChinese(data, width=16):
    count = 0
    for s in data:
        if ord(s) > 127:
            count += 1
    return "{:^{wd}}".format(data, wd=width-count)

def getStationName():
    stationVersion = 1.9044
    url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
    reqData = parse.urlencode([("station_version", stationVersion)])
    url = url + "?" + reqData
    logging.debug(url)
    req = request.Request(url)
    with request.urlopen(req) as f:
        names = f.read()
        with open("stationInfo.txt", "wb") as fw:
            fw.write(names)
        
        itemsTMP = names.decode('utf-8').split("'")
        formatStr = "{}|{}|{}|{}|{}|{}"
        if len(itemsTMP) == 3:
            with open("stationTable.txt", "wt", encoding="utf-8") as fw:
                items = itemsTMP[1].split('@')
                logging.debug(formatStr.format(
                    formatChinese("代号"),
                    formatChinese("中文名"),
                    formatChinese("车站代码"),
                    formatChinese("中文拼音"),
                    formatChinese("拼音首字母"),
                    formatChinese("序号")))
                fw.write(formatStr.format(
                    formatChinese("代号"),
                    formatChinese("中文名"),
                    formatChinese("车站代码"),
                    formatChinese("中文拼音"),
                    formatChinese("拼音首字母"),
                    formatChinese("序号")))
                fw.write("\n")
                for item in items:
                    if len(item) == 0: continue
                    info = item.split("|")
                    logging.debug(formatStr.format( *list( map( formatChinese, info) ) ) )
                    fw.write(formatStr.format(*list(map(formatChinese, info))))
                    fw.write("\n")

def getTrainInfo2():
    "GET"
    destDat = "2018-01-25"
    baseURL = "https://kyfw.12306.cn/otn/leftTicket/queryZ"
    reqData = parse.urlencode([
        ("leftTicketDTO.train_date",   destDat),
        ("leftTicketDTO.from_station", "GZQ"),
        ("leftTicketDTO.to_station",   "WHN"),
        ("purpose_codes",              "ADULT")
    ])
    destURL = baseURL + "?" + reqData

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.3",
        "Referer":    "https://kyfw.12306.cn/otn/leftTicket/init",
        "Host":       "kyfw.12306.cn",
        "X-Requested-With": "XMLHttpRequest",
    }
    req = request.Request(destURL, headers=headers)

    with request.urlopen(req) as f:
        logger.debug("Status:{} {}".format(f.status, f.reason))
        for k, v in f.getheaders():
            logger.debug("{}: {}".format(k, v))
        try:
            data = json.loads(f.read().decode("utf-8"))
        except:
            sys.exit("something wrong")
        
        pprint(data)
        # 车次 3  发车时间 8 到达 9 历时 10 发车日期 13 是否可预订 11
        # 商务 32 一等 31 二等 30
        # 无座 26 软卧 23 硬卧 28 硬座 29
        if data["httpstatus"] == 200:
            for item in data["data"]["result"]:
                for i, v in enumerate(item.split("|")):
                    logger.debug("[{}] {}".format(i, v))
                    # print(v, end=" ")

if "__main__" == __name__:
    getStationName()