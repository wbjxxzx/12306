#!/usr/bin/env python3
#-*- coding:utf-8 -*-

import logging, logging.config
logging.config.fileConfig("conf/logging.conf")
logger = logging.getLogger("")


''' class Logger():
    logger = logging.getLogger("")
    fileFormatter = logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s")
    fileHandler = logging.FileHandler("12306.log")
    fileHandler.setFormatter(fileFormatter)
    fileHandler.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stdout)
    consoleFormatter = logging.Formatter("%(name)-10s: %(levelname)-8s %(message)s")
    console.setFormatter(consoleFormatter)
    console.setLevel(logging.INFO)
    logger.addHandler(fileHandler)
    logger.addHandler(console) '''

