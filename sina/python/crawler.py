#! /usr/bin/env python
# -*- coding: UTF-8-*-
__author__ = 'leeyee.li'

import os
import urllib
import re
import time
from xml.sax import saxutils
from HTMLParser import HTMLParser

import logging as logger


config = {
    'blog_name': 'u/2909466917',
    'store_path': '../blogs/2909466917',
    'blog_site': 'http://blog.sina.com.cn'
}

logger.basicConfig(
    level=logger.INFO,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)


def get_url(url):
    try:
        f = urllib.urlopen(url)

        status = f.getcode()

        logger.info("请求url = %s, status:%s", url, status)

        return f.read()

    except IOError, e:
        logger.warn(e)
    else:
        if f:
            f.close()


def get_blog_list_url(html_string):
    _reg = r'href="(\S*)">博文目录</a>'
    _search = re.search(_reg, html_string, re.I | re.S)
    if _search:
        logger.info("博客目录url=%s", _search.group(1))
        return _search.group(1)


def get_next_page_url(html):
    _reg = r'<a href="(\S*)" title="跳转至第 \d+ 页">下一页'
    _search = re.search(_reg, html, re.I | re.S)
    if _search:
        logger.info("下一页url=%s", _search.group(1))
        return _search.group(1)


_blog_list = []


def get_blog_list(html):
    _reg = r'title="(\S*)" target="_blank" href="(\S*)".*?class="atc\_tm SG\_txtc">(\d{4,}-\d\d-\d\d \d\d:\d\d)'

    blog_list = re.findall(_reg, html, re.I | re.S)

    global _blog_list

    for blog in blog_list:
        _blog_list.append(blog)

    logger.info("当前页博客数量=%s", len(blog_list))

    _next_url = get_next_page_url(html)

    if _next_url:
        get_blog_list(get_url(_next_url))
    else:
        return blog_list


# html 文章内容解析类
class BlogContentParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.blog = ''

    def handle_data(self, data):
        self.blog += data


def get_blog(url):
    blog_html = get_url(url)
    _len = len(blog_html)
    start_pos = blog_html.find('<!-- 正文开始 -->', 0, _len)
    end_pos = blog_html.rfind('<!-- 正文结束 -->', 0, _len)
    blog_html_sub = blog_html[start_pos + 22:end_pos]
    parser = BlogContentParser()
    parser.blog = ''
    parser.reset()
    parser.feed(blog_html_sub)
    parser.close()

    _blog = "原文链接：" + url + "\n" + parser.blog

    return _blog


def get_blog_filename(title, blog_date):
    return r'【%s】%s' % (blog_date, title)


def is_exist_blog(blog_name, path):
    return os.path.exists((path + blog_name).decode("utf-8") + '.txt')


def store_blog(filename, content, path):
    try:

        f = file((path + filename).decode("utf-8") + '.txt', 'wb+')
        f.write(content.strip())
        f.flush()

    except IOError, e:

        logger.error(e)

    else:
        if f:
            f.close()


if __name__ == '__main__':

    html_string = get_url(config['blog_site'] + "/" + config['blog_name'])

    match_list_url = get_blog_list_url(html_string)

    blog_list_html = get_url(match_list_url)

    match = get_blog_list(blog_list_html)

    _store_path = config['store_path']

    if not _store_path:
        _store_path = "../" + config['blog_name'] + "/"

        logger.debug("博客保存路径未设置，使用默认路径：%s", _store_path)

    elif not _store_path.endswith("/"):
        _store_path += "/"

    if not os.path.exists(_store_path.decode("utf-8")):
        os.makedirs(_store_path.decode("utf-8"))

    nums = 0

    _start = time.time()

    for (_title, _url, _date) in _blog_list:

        try:
            _title = saxutils.unescape(_title, {'&nbsp;': ' ', '&#039;': "'"})

            _title = re.sub(r'[/\\:"*?<>|]', '', _title)

            logger.info("博客 %s, %s, %s", _title, _url, _date)

            _date = _date.replace("-", "").replace(" ", "").replace(":", "")

            _blog_filename = get_blog_filename(_title, _date)

            if is_exist_blog(_blog_filename, _store_path):
                logger.warn("博客《%s》已经存在. 连接地址：%s", _blog_filename, _url)

            else:
                blog_content = get_blog(_url)
                store_blog(_blog_filename, blog_content, _store_path)
                nums += 1

        except Exception, e:
            logger.error(e)

    _end = time.time()

    print("博客总数量：%d，实际保存 %d，共耗时 %ss" % ( len(_blog_list), nums, round(_end - _start, 3)))

