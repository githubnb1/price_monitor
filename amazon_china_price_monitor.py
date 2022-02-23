#!/usr/bin/env python
# coding: utf-8
# @Author : JackLee
# @contact: jackleeforce@gmail.com
# @Time : 2019-06-10 15:56
# @File : amazon_china_price_monitor.py
# @desc:
import logging
import time
from urllib.parse import urlparse

import requests
from lxml import etree
from user_agent import generate_user_agent

import func
from wechatsender import WeChatSender

# corpid = '企业微信-企业ID'
# corpsecret = '企业微信-应用管理-Secret'
# agentid = '企业微信-应用管理-AgentId'


corpid = 'ww1138f50c28e38452'
corpsecret = 'iCXiWY9OGQl1sQAwYEI0AqeuvjFkrbSL1FGWedzPglQ'
agentid = '1000002'


def shrink_price(str_price):
    new_price = str_price.replace('￥', '')
    new_price = new_price.replace(',', '')

    return float(new_price)


def monitor_amazon_china():
    # 需要监测的目标商品 URL 等信息。
    monitor_targets = [
        {'url': 'https://www.amazon.cn/dp/B07G364YHX', 'ideal_price': 1200.00, 'lowst_price_history': 0.00,
         'keyword': '10TB', 'last_notify_date': ''}]

    session = requests.session()

    for monitor_target in monitor_targets:

        func.random_sleep_seconds(1, 3)

        target_url = monitor_target.get('url')
        ideal_price = monitor_target.get('ideal_price')
        lowst_price_history = monitor_target.get('lowst_price_history')
        last_notify__date = monitor_target.get('last_notify_date')
        keyword = monitor_target.get('keyword')

        o = urlparse(target_url)
        ref = o.scheme + '://' + o.hostname
        ua = generate_user_agent(device_type='desktop')
        session.headers[
            'User-Agent'] = ua
        session.headers[
            "Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        session.headers['Accept-Encoding'] = "gzip, deflate, br"
        session.headers['Accept-Language'] = "zh-CN,zh;q=0.9,en;q=0.8"
        session.headers['Cache-Control'] = "no-cache"
        session.headers['Connection'] = "keep-alive"
        session.headers['Pragma'] = "no-cache"
        session.headers['Sec-Fetch-Dest'] = "document"
        session.headers['Sec-Fetch-Mode'] = "navigate"
        session.headers['Sec-Fetch-Site'] = "none"
        session.headers['referer'] = ref

        response = session.get(target_url)

        response.raise_for_status()

        html_source = response.text

        logging.debug("html source:" + html_source)

        selector = etree.HTML(html_source)

        # 获取商品信息。
        title = (selector.xpath('//span[@id="productTitle"]/text()')[0]).strip()
        current_prices = selector.xpath('//span[@id="priceblock_ourprice"]/text()')

        if len(current_prices) == 0:
            logging.debug(title + ',' + '无货' + ',url:' + target_url)
            continue

        current_float_price = shrink_price(current_prices[0])

        logging.debug(title + ',' + current_prices[0] + ',url:' + target_url)

        # 设定商品标题中必须包含指定关键字。
        if keyword.strip('') != '' and keyword.strip('') not in title:
            continue

        if current_float_price <= ideal_price:
            current_date = time.strftime("%Y-%m-%d", time.localtime())

            if current_date != last_notify__date:
                monitor_target['last_notify_date'] = current_date

                # 组装发送消息。
                message = 'Item name:{0} \nurl:{1}\nreached your ideal price:\n{2}\ncurrent price:\n{3}\n'.format(title,
                                                                                                                  target_url,
                                                                                                                  ideal_price,
                                                                                                                  current_float_price)

                if lowst_price_history == 0.00 or current_float_price <= lowst_price_history:
                    monitor_target['lowst_price_history'] = current_prices[0]
                    message += 'This price is the lowst price in the history'

                logging.debug(message)

                wechat_sender = WeChatSender(corpid, corpsecret, agentid)

                wechat_sender.send_text_msg(message)


if __name__ == '__main__':
    func.init_ssl()

    func.init_log('price_monitor.log')

    wechat_sender = WeChatSender(corpid, corpsecret, agentid)

    wechat_sender.send_text_msg('Start to monitor amazon china bug price')

    retryCount = 0

    while True:
        error_occured = False
        try:
            monitor_amazon_china()
        except Exception as e:
            logging.exception(e)
            logging.error('Something wrong,retry count:' + str(retryCount))
            wechat_sender.send_text_msg('Something wrong,retry count:' + str(retryCount))
            retryCount += 1
            error_occured = True

        if not error_occured:
            retryCount = 0
        elif retryCount >= 15:
            wechat_sender.send_text_msg('Something wrong,quit job')
            break

        func.random_sleep_seconds(1, 2)

    exit(0)
