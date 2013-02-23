#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
from urllib import urlopen
import csv
from StringIO import StringIO
import simplejson as json
from lxml import etree
from urlparse import urljoin
from lxml.html import fromstring
from BeautifulSoup import UnicodeDammit

def decode_html(html_string):
    converted = UnicodeDammit(html_string, isHTML=True)
    if not converted.unicode:
        raise UnicodeDecodeError("Failed to detect encoding, tried [%s]", ', '.join(converted.triedEncodings))
    return converted.unicode

class UniParser:
    def __init__(self):
        pass

    def get_page(self, url):
        f = urlopen(url)
        data = f.read()
        rurl = f.geturl()
        f.close()
        data = decode_html(data)
        root = fromstring(data)
        return root, rurl

    def process_row(self,row):
        cells = []
        for cell in row.xpath('./td'):
            inner_tables = cell.xpath('./table')
            if len(inner_tables) < 1:
                cells.append(cell.text_content().replace('\r',' ').replace('\n', ' ').encode('utf8'))
            else:
                cells.append([self.process_table(t) for t in inner_tables])
        return cells

    def process_table(self, table):
        return [self.process_row(row) for row in table.xpath('./tr')]


    def parseList(self, url, xpath, absolutize=True):
        root, rurl = self.get_page(url)
        results = []
        links = root.xpath(xpath)
        for l in links:
            href = l.attrib['href']
            text = l.text
            item = [text.encode('utf8'), urljoin(rurl, href.encode('utf8')) if absolutize else href.encode('utf8')]
            results.append(item)
        return results

    def parseOptionsList(self, url, xpath, absolutize=True):
        root, rurl = self.get_page(url)
        results = []
        links = root.xpath(xpath)
        for l in links:
            href = l.attrib['value'] if l.attrib.has_key('value') else None
            if href:
                href = urljoin(rurl, href.encode('utf8')) if absolutize else href.encode('utf8')
            text = l.text
            if text:
                text = text.encode('utf8')
            item = [text, href]
            results.append(item)
        return results

    def parseTable(self, url, xpath):
        root, rurl = self.get_page(url)
        results = []
        objects = root.xpath(xpath)
        if len(objects) > 0:
            results = self.process_table(objects[0])
        return results

    def parseTables(self, url, xpath):
        root, rurl = self.get_page(url)
        results = []
        objects = root.xpath(xpath)
        for o in objects:
            results.extend(self.process_table(o))
        return results

    def getBlock(self, url, xpath):
        root, rurl = self.get_page(url)
        results = []
        objects = root.xpath(xpath)
        if len(objects) > 0:
            return etree.tostring(objects[0], pretty_print=True)
        return None

    def getTextList(self, url, xpath, clean_empty=True, stop_on=None):
        root, rurl = self.get_page(url)
        results = []
        objects = root.xpath(xpath)
        if len(objects) > 0:
            for o in objects:
                if stop_on is not None and stop_on == o.tag:
                #                    print stop_on, o.tag
                    break
                for item in o.itertext():
                    t = item.strip()
                    if len(t) > 0:
                        results.append(t)
        return results

