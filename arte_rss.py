#!/usr/bin/python
"""
    Due to disappeard RSS support, this tool parses the content of the ARTE+7
    streaming website and converts it to RSS.
"""
import sys
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from lxml import etree

import pycurl

BASE_URL = "https://www.arte.tv/fr/guide"

def extract_entry(xml, xType, classKey):
    for u in xml.findAll(xType):
        if len(u['class']) == 2 and u['class'][1] is not None and u['class'][1] == classKey:
            return u.text.encode('utf-8')

class ArteDay:
    """ Object representing the content of an ARTE program for a day"""
    def __init__(self, date):
        """ This constructor performs the http query, parses it, and populates its videos"""

        year = str(date.year)
        month = str(date.month).zfill(2)
        day = str(date.day).zfill(2)

        self.day_url = "%s/%s%s%s/" % (BASE_URL, year, month, day)

        buf = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, self.day_url)
        curl.setopt(pycurl.WRITEFUNCTION, lambda x: None)
        curl.setopt(curl.WRITEDATA, buf)

        curl.perform()
        curl.close()

        body = buf.getvalue()
        xml = BeautifulSoup(body, 'lxml')

        self.videos = []
        for timeline_xml in xml.findAll("div", {"class":"program-timeline"}):
            for vid_xml in timeline_xml.findAll("div"):
                v = Video(vid_xml, date)
                if v.link is not None:
                    self.videos.append(v)


    def to_rss(self):
        """ converts the content of this object to RSS """
        root = etree.Element('rss')
        root.attrib['version'] = '2.0'
        channel = etree.Element('channel')
        root.append(channel)

        title = etree.Element('title')
        title.text = "Arte +7"
        channel.append(title)

        link = etree.Element('link')
        link.text = self.day_url
        channel.append(link)

        for video in self.videos:
            channel.append(video.to_rss())

        return root

class Video:
    """ Object representing an entry in the ARTE daily program"""
    def __init__(self, xml, day):
        """ This contructor analyses the content of the video's xml and populates attributes"""
        self.link = self.extract_link(xml)
        self.description = self.extract_description(xml)
        self.title = self.extract_title(xml)
        self.author_name = "Arte +7"
        self.timestamp = self.extract_timestamp(day, xml)

    def extract_link(self, xml):
        """ Parses the xml and returns the object's url"""
        for u in xml.findAll('a'):
            if u['href'] is not None:
                return u['href']

    def extract_description(self, xml):
        """ Parses the xml and returns the object's description"""
        return extract_entry(xml, "div", "e1p6xx0h3")

    def extract_title(self, xml):
        """ Parses the xml and returns the object's title"""
        return extract_entry(xml, "span", "e1p6xx0h12")

    def extract_timestamp(self, day, xml):
        """
            Parses the xml and returns the object's date of broadcast
            Unfotunately, only the hours and minutes are available in the xml,
            for this reason, we combine them with the date information from the URL
            and end up with a full timestamp
        """
        time_of_day_str = extract_entry(xml, "span", "e1p6xx0h7")

        if time_of_day_str is not None:
            hour_str, minute_str = time_of_day_str.decode().split(':')

            date = datetime(
                year=day.year,
                month=day.month,
                day=day.day,
                hour=int(hour_str),
                minute=int(minute_str)
            )

            return date.strftime('%a, %d %B %Y %H:%M:%S %z')
        return None



    def to_rss(self):
        """ Converts the object to RSS """
        root = etree.Element('item')

        date = etree.Element('pubDate')
        date.text = str(self.timestamp)
        root.append(date)

        link = etree.Element('link')
        link.text = self.link
        root.append(link)

        title = etree.Element('title')
        title.text = self.title.decode('utf-8')
        root.append(title)

        if self.description is not None:
            description = etree.Element('description')
            description.text = self.description.decode('utf-8')
            root.append(description)

        author = etree.Element('author')
        author.text = self.author_name
        root.append(author)

        return root


TODAY = ArteDay(datetime.today())
sys.stdout.write("<?xml version='1.0' encoding='UTF-8'?>")
sys.stdout.write(etree.tostring(TODAY.to_rss()).decode())
