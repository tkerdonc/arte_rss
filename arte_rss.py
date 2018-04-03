#!/usr/bin/python
"""
    Due to disapperead RSS support, this tool parses the content of the ARTE+7
    streaming website and converts it to RSS.
"""
import sys
from datetime import datetime
from io import BytesIO
from bs4 import BeautifulSoup
from lxml import etree

import pycurl

BASE_URL = "https://www.arte.tv/fr/guide"

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
        for vid_xml in xml.findAll("article", {"class":"tvguide-program"}):
            self.videos.append(Video(vid_xml, date))


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
        return xml.find('a', {"class":"tvguide-program__link"})['href']

    def extract_description(self, xml):
        """ Parses the xml and returns the object's description"""
        return xml.find('div', {"class":"tvguide-program__description"}).text.encode('utf-8')

    def extract_title(self, xml):
        """ Parses the xml and returns the object's title"""
        return xml.find('h3', {"class":"tvguide-program__title"}).text.encode('utf-8')

    def extract_timestamp(self, day, xml):
        """
            Parses the xml and returns the object's date of broadcast
            Unfotunately, only the hours and minutes are available in the xml,
            for this reason, we combine them with the date information from the URL
            and end up with a fill timestamp
        """
        time_of_day_str = xml.find('span', {"class":"tvguide-program__hour"}).text
        hour_str, minute_str = time_of_day_str.split(':')

        date = datetime(
            year=day.year,
            month=day.month,
            day=day.day,
            hour=int(hour_str),
            minute=int(minute_str)
        )

        return date.strftime('%s')

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

        description = etree.Element('description')
        description.text = self.description.decode('utf-8')
        root.append(description)

        author = etree.Element('author')
        author.text = self.author_name
        root.append(author)

        return root


TODAY = ArteDay(datetime.today())
sys.stdout.write("<?xml version='1.0' encoding='UTF-8'?>")
sys.stdout.write(str(etree.tostring(TODAY.to_rss(), encoding="unicode")))
