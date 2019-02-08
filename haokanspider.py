# coding: utf-8
import re
import os
import logging
from threading import Thread
import http.cookiejar
from json import loads
from urllib import  request, parse, error
from bs4 import BeautifulSoup
from time import time

class Spider():
    def __init__(self):
        self.main_url = 'http://sv.baidu.com'
        self.tab_url = 'http://sv.baidu.com/videoui/list/tab'
        self.header = {
            'Referer': 'http://sv.baidu.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36'
        }
        self.log_dir = self.mkdir(os.path.join(os.path.dirname(__file__), 'log'))
        self.video_dir = self.mkdir(os.path.join(os.path.dirname(__file__), 'video'))
        self.opener = self.build_opener()
        self.logger = self.__build_logger()

    # 创建目录
    def mkdir(self, dir):
        if not os.path.isdir(dir):
            os.mkdir(dir)
        return dir

    # 构建日志输出函数
    def __build_logger(self):
        filename = os.path.join(self.log_dir, 'spider.log')
        logger = logging.getLogger(__name__)
        logger.setLevel(level = logging.INFO)
        handler = logging.FileHandler(filename)
        handler.setLevel(level = logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        console = logging.StreamHandler()
        console.setLevel(level = logging.INFO)
        logger.addHandler(console)
        return logger

    # 构建带cookie的url opener
    def build_opener(self):
        cookie_name = os.path.join(self.log_dir, 'cookie.log')
        cookie = http.cookiejar.MozillaCookieJar(cookie_name)
        if os.path.isfile(cookie_name):
            cookie.load(cookie_name, ignore_discard=True, ignore_expires=True)
            handler = request.HTTPCookieProcessor(cookie)
            opener = request.build_opener(handler)
        else:
            handler = request.HTTPCookieProcessor(cookie)
            opener = request.build_opener(handler)
            req = request.Request(self.main_url, headers=self.header)
            try:
                respone = opener.open(req)
            except Exception as e:
                print(e)
            cookie.save(filename=cookie_name, ignore_discard=True, ignore_expires=True)
        return opener

    # 获取指定url内容
    def urlopen(self, url, data = None, is_redecode = False, is_format = True):
        if data is not None:
            data = parse.urlencode(data).encode(encoding='UTF-8')
        req = request.Request(url, data=data, headers=self.header)
        respone = self.opener.open(req)
        if is_format:
            respone = BeautifulSoup(respone, 'lxml')
        # unicode编码转中文
        if is_redecode:
            respone = BeautifulSoup(self.redecode(respone), 'lxml')
        return respone

    # 获取分类信息
    def get_index(self):
        html = self.urlopen(self.main_url)
        data_list = html.find_all(name='li', attrs={'tid': True})
        url_list = {}
        for data in data_list:
            name_url = data.find('a')['href']
            name = data.find('a').string
            url_list[name] = name_url
        
        return url_list

    # unicode编码转中文
    def redecode(self, content):
        content = content.encode('utf-8').decode('unicode_escape')
        return content
    
    # 获取指定页视频内容
    def expand(self, item, page = 1):
        data = parse.urlencode({
            'source': 'wise-channel',
            'pd': '',
            'subTab': item,
            'direction': 'down',
            'refreshType': 1,
            'ua': 'Mozilla%2F5.0%20(Windows%20NT%2010.0%3B%20Win64%3B%20x64)%20AppleWebKit%2F537.36%20(KHTML%2C%20like%20Gecko)%20Chrome%2F72.0.3626.81%20Safari%2F537.36',
            'bt': '1549533482',
            'caller': 'bdwise',
            '_': int(time()),
            'cb': 'jsonp%d' % (page),
        })

        url = self.tab_url + '?' + data
        respone = self.urlopen(url = url, is_redecode=True)
        video_list = respone.find_all('div', attrs={'data-authorid': True})
        items = []
        for video in video_list:
            pattern = r'(\\)|(")'
            url = re.sub(pattern, '', video['data-vsrc'])
            title = re.sub(pattern, '', video['data-title'])
            items.append({'title': title, 'url': url})
        return items

    # 保存视频
    def save_video(self, page = 1):
        items = self.expand('qiongying', page)
        for item in items:
            respone = self.urlopen(item['url'], is_format=False)
            filename = os.path.join(self.video_dir, item['title'].strip() + '.mp4')
            if not os.path.isfile(filename):
                with open(filename, 'wb') as f:
                    f.write(respone.read())
                if os.path.isfile(filename):
                    self.logger.info(filename)

    # 执行视频采集
    def run(self, total_page = 1):
        for i in range(1, total_page+1):
            self.save_video(i) 

# 视频采集示例
if __name__ == "__main__":
    spider = Spider()
    spider.run(total_page=10)
