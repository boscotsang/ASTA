#!/usr/bin/python
# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_socket()
import gevent
import requests
import json
import logging
import datetime
import tornado.template as template

class BestEveryDay(object):

    STOCK_PRICE_URL = "http://ifzq.gtimg.cn/appstock/app/fqkline/get?p=1&param=%s,day,,,320,qfq"
    BOLL_TECH_ANAL = "http://ifzq.gtimg.cn/appstock/indicators/BOLL/D1?market=%s&code=%s&args=20&start=&end=&limit=320&fq=qfq"
    MACD_TECH_ANAL = "http://ifzq.gtimg.cn/appstock/indicators/MACD/D1?market=%s&code=%s&args=20&start=&end=&limit=320&fq=qfq"
    #http://baike.baidu.com/view/965844.htm
    SZ_A =  {
        "code": "000%03d",
        "market": "SZ",
        "full_code": "sz000%03d"
    }
    SH_A1 = {
        "code": "600%03d",
        "market": "SH",
        "full_code" : "sh600%03d"
    }
    SH_A2 = {
        "code" : "601%03d",
        "market" : "SH",
        "full_code" : "sh601%03d"
    }
    SH_A3 = {
        "code" : "603%03d",
        "market": "SH",
        "full_code" : "sh603%03d"
    }
    TIMEOUT = 10
    LOW_RATE = 0.03

    def __init__(self):
        logging.basicConfig(filename='best.log', format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        logging.getLogger('requests').setLevel(logging.ERROR)
        date = "%s" % datetime.datetime.today().date()
        self.json_file = file("../data/stock_every_day/%s.json" % date, "w")
        self.html_file = file("../data/stock_every_day/%s.html" % date, "w")
        self.best = []

    def fetch(self, stockurl, bollurl, stock_num, full_code):
            try:
                stock_info = requests.get(stockurl, timeout=self.TIMEOUT).json()
                boll_info = requests.get(bollurl, timeout=self.TIMEOUT).json()
                last_day_boll = boll_info['data'][-2]
                last_day_price = stock_info['data'][full_code]['qt'][full_code][3]
                name = stock_info['data'][full_code]['qt'][full_code][1]
                rate = (float(last_day_price) - float(last_day_boll['LB'])) / float(last_day_price)
                logging.info('start -- %s, %s, %s, %s, %s' % (name, stock_num, last_day_price,\
                                                              last_day_boll['LB'], rate))
                if rate <= self.LOW_RATE and name.find("ST") == -1 and name.find(u"退市") == -1:
                    logging.info('get -- (%s, %s, price: %s, rate: %s )' % (name, stock_num, last_day_price, rate))
                    self.best.append({
                        "name" : name,
                        "stock_code" : stock_num,
                        "current_price" : last_day_price,
                        "price_to_low_boll_rate": rate
                    })
            except Exception as e:
                logging.info("error %s" % e)
                pass

    def find_best(self, market):
        stocks = [(market['code'] % i, market['full_code'] % i) for i in xrange(1000)]
        urls = [(self.STOCK_PRICE_URL % full_code, self.BOLL_TECH_ANAL % (market['market'], stock_num), stock_num, full_code) for stock_num, full_code in stocks]
        gevent.joinall([gevent.spawn(self.fetch, stock_price_url, boll_url, stock_num, full_code) for (stock_price_url, boll_url, stock_num, full_code) in urls])

    def start(self):
        self.find_best(self.SZ_A)
        self.find_best(self.SH_A1)
        self.find_best(self.SH_A2)
        self.find_best(self.SH_A3)
        self.json_file.write(json.dumps(self.best))
        self.json_file.close()
        loader = template.Loader("../template")
        self.html_file.write(loader.load("success_every_day.html").generate(data=self.best))
        self.html_file.close()


if __name__ == "__main__":
    best_every_day = BestEveryDay()
    best_every_day.start()



