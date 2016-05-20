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

# 日志级别格式设置
logger.basicConfig(
    level=logger.INFO,
    format="[%(asctime)s] %(name)s:%(levelname)s: %(message)s"
)


def get_url(url):
    """获取URL对应的内容。Http Response!

    Args:
        url: http请求地址

    Returns:
        返回页面内容

    Raises:
        IOError: http请求IO异常
    """
    try:
        f = urllib.urlopen(url)  # http请求url
        status = f.getcode()  # 获取http请求响应码(200,400,500 etc.)
        logger.info("请求url = %s, status:%s", url, status)
        return f.read()
    except IOError, _e:
        logger.warn(_e)
    else:
        f.close if f else None


def get_blog_list_url(str_html):
    """获取文章列表所在的页面地址

    Args:
        str_html: 页面HTML内容字符串
    """
    _reg = r'href="(\S*)">博文目录</a>'
    _search = re.search(_reg, str_html, re.I | re.S)
    if _search:
        logger.info("博客目录url=%s", _search.group(1))
        return _search.group(1)


def get_next_page_url(html):
    """获取文章类表分页地址

    Args:
        html: 页面HTML内容字符串
    Returns:
        url地址
    """
    _reg = r'<a href="(\S*)" title="跳转至第 \d+ 页">下一页'
    _search = re.search(_reg, html, re.I | re.S)
    if _search:
        logger.info("下一页url=%s", _search.group(1))
        return _search.group(1)


_blog_list = []  # 博客信息[title, url, post, date] : [标题，链接地址，链接名，发布时间]


def get_blog_list(html):
    """ 获取所有的博客地址信息
    """
    _reg = r'title="(\S*)" target="_blank" href="(\S*)">(\S*)</a>.*?class="atc\_tm SG\_txtc">(\d{4,}-\d\d-\d\d \d\d:\d\d)'

    blog_list = re.findall(_reg, html, re.I | re.S)

    global _blog_list

    for blog in blog_list:
        _blog_list.append(blog)

    logger.info("当前页博客数量=%s", len(blog_list))

    _next_url = get_next_page_url(html)  # 获取下一页

    return get_blog_list(get_url(_next_url)) if _next_url else blog_list


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
    """获取保存的博客文件名称
    Args:
        title: 标题
        blog_date: 创建时间
    Returns:
        博客保存文件名
    """

    return r'【%s】%s' % (blog_date, title)


def is_exist_blog(blog_name, path):
    """判断待保存博客文件是否存在

    Args：
        blog_name: 博客文件名
        path: 所在路径
    Returns:
        存在返回True，否则返回False
    """

    return os.path.exists((path + blog_name).decode("utf-8") + '.txt')


def store_blog(filename, content, path):
    """保存博客文件

    Args:
        filename: 文件名
        content: 文件内容
        path: 保存路径

    Raises:
        IOError: 读写文件异常
    """
    try:
        f = file((path + filename).decode("utf-8") + '.txt', 'wb+')
        f.write(content.strip())
        f.flush()
    except IOError, _e:
        logger.error(_e)
    else:
        f.close() if f else None


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

    for (_title, _url, _post, _date) in _blog_list:

        try:

            if _title == '':
                _title = _post

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

    print("博客总数量：%d，实际保存 %d，共耗时 %ss" % (len(_blog_list), nums, round(_end - _start, 3)))

