# -*- coding: UTF-8 -*-

import datetime
import logging
import os
import re
from datetime import date
from urllib.parse import parse_qs, urlparse

import scrapy
from bs4 import BeautifulSoup
from lxml.html.clean import Cleaner
from scrapy.exceptions import NotConfigured
from scrapy.http import HtmlResponse


class FullSiteSpider(scrapy.Spider):
    pwd = os.getcwd()
    name = "fullsite"
    MAX_PATH_DEPTH = 15
    logger = logging.getLogger('FullSiteSpider')

    ignored_extensions = [".jpg", ".mp3", ".mp4", ".wmv", ".avi",
                          ".png", ".gif", ".zip", ".iso", ".exe", ".tif", ".mov"]

    FT_REGEX = r"pdf|doc|docx"
    FILES_EXTENSION = r"\.(" + FT_REGEX + r")(\/[a-zA-Z0-9-]*)?"

    def __init__(self, *args, **kwargs):

        super(FullSiteSpider, self).__init__(*args, **kwargs)
        self.language = kwargs.get('language')
        self.url = kwargs.get('url')
        if not self.url:
            raise NotConfigured(
                "Expecting a 'url' property to be configured, pointing to the first page on the site")

        self.website = kwargs.get('website')
        if not self.website:
            raise NotConfigured(
                "Expecting a 'website' property to be configured, declaring the name of the website to be scraped"
            )

        self.langs = kwargs.get('langs')
        if not self.langs:
            self.langs = []
        else:
            self.langs = self.langs.split(',')

        self.url_forbidden_prefixes = ["#", "javascript"]

        self.search_domains = set()
        parsed_uri = urlparse(self.url)
        self.search_domains.add(
            'http://{uri.netloc}/'.format(uri=parsed_uri))
        self.search_domains.add(
            'https://{uri.netloc}/'.format(uri=parsed_uri))

        self.cleaner = Cleaner(style=True, links=True, add_nofollow=True,
                               page_structure=False, safe_attrs_only=False)

    def start_requests(self):

        request = scrapy.Request(url=self.url, headers={
            'Referer': self.url}, callback=self.parse)
        request.meta['origin'] = ""
        yield request

    def parse(self, response):
        parsed_uri = urlparse(response.url)
        self.search_domains.add(
            'http://{uri.netloc}/'.format(uri=parsed_uri))
        self.search_domains.add(
            'https://{uri.netloc}/'.format(uri=parsed_uri))

        detected_language = ""
        # indicates if it should be processed in items pipeline
        if isinstance(response, HtmlResponse):

            cleaned_html = self.cleaner.clean_html(response.body)

            title = response.xpath('//head/title/text()').get()

            self.logger.debug("Detected language '%s' for: %s",
                              detected_language, response.url)

            pdf_urls = [url for url in response.css('a::attr(href)').extract() if '.pdf'.casefold() in url]
            pdf_docs = []
            for url in pdf_urls:
                if url.startswith('http://') or url.startswith('https://'):
                    pdf_docs.append(url)
                else:
                    pdf_docs.append(response.urljoin(url))

            pdf_docs = [response.urljoin(url) for url in pdf_urls]
            yield {
                'url': response.url,
                'title': title,
                'website': self.website,
                'content_html': cleaned_html.decode('utf-8'),
                'date': datetime.datetime.now().isoformat(),
                'language': self.language,
                'pdf_docs': pdf_docs
            }

            urls = response.css('a::attr(href)').extract()
            loophole = False
            for url in urls:

                today = date.today()
                keyword = re.search("agenda", url)
                match = re.search(r'\d{4}-\d{2}-\d{2}', url)
                if keyword:
                    try:

                        date_time_str = match.group()
                        date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d').date()
                        if date_time_obj > today:
                            self.logger.warn(
                                "Date %s appears to be set in the future. Stopping here!", url)
                    except:
                        date_time_str = None

                if not (url.startswith('http://') or url.startswith('https://')):
                    url = response.urljoin(url)

                parsed_uri = urlparse(url)
                parsed_orig_uri = urlparse(response.url)

                domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

                if all(not url.startswith(x) for x in self.url_forbidden_prefixes):
                    if domain in self.search_domains:

                        if url.count('/') < self.MAX_PATH_DEPTH:

                            if "search" in url.lower():
                                self.logger.warn(
                                    "Path %s appears to be a search field. Stopping here!", url)
                            else:
                                if parsed_uri.path and parsed_uri.path[-4:] in self.ignored_extensions:
                                    self.logger.warn(
                                        "Path %s contains ignored extension. Stopping here!", url)
                                else:
                                    loophole = self.detect_loop_hole(parsed_uri, parsed_orig_uri)
                                    if loophole:
                                        self.logger.warn(
                                            "Path %s looks like a loophole. Stopping here!", url)
                                    else:
                                        request = response.follow(
                                            url, headers={'Referer': response.url}, callback=self.parse)
                                        request.meta['origin'] = response.url
                                        yield request
                        else:
                            self.logger.warn(
                                "Reached maxs path depth for %s. Stopping here!", url)
                    else:
                        self.logger.debug("Not an allowed domain: %s", url)
                else:
                    self.logger.debug("In forbidden prefixes: %s", url)

    def detect_loop_hole(self, new_uri, previous_uri):
        # temporary solution to avoid treating pages on websites as loops, should be improved
        a_previous_uri = str(previous_uri)
        keyword = re.search("page", a_previous_uri)
        if keyword is None:
            if previous_uri.path == new_uri.path:
                if new_uri.query and previous_uri.query:
                    if not self.hasNewKeys(parse_qs(new_uri.query), parse_qs(previous_uri.query)):
                        return True
                    if self.query_parameter_occurences_exceeds(new_uri.query, 4):
                        return True
            else:  # if new url is not a page and not identical to the previous url still check for repeated params
                for param in re.findall('\W(.+?)&', str(previous_uri.query)):
                    if param in str(new_uri.query):
                        print("this " + param + " is being repeated")
                        return True

        else:  # if new url is a page still check for repeated params
            for param in re.findall('\W(.+?)&', str(previous_uri.query)):
                if param in str(new_uri.query):
                    print("this " + param + " is being repeated")
                    return True
        return False

    def hasNewKeys(self, first, second):
        for key in second.keys():
            if not key in first.keys():
                return True
        return False

    def query_parameter_occurences_exceeds(self, uri_query, max_occurences):
        array = parse_qs(uri_query)
        for key in array:
            if len(array[key]) > max_occurences:
                return True
        return False

    def htmlToText(self, html):
        # Whitelist with all tags we want to keep
        whitelist = ['p', 'title', 'h1']
        soup = BeautifulSoup(html, features='lxml')
        text = []
        for tag in soup.find_all(True):
            try:
                if tag.string and not tag.string.isspace():
                    if tag.name in whitelist:
                        text.append(tag.string.strip())
            except RecursionError:
                print(f"Recursion error")
        text = ' '.join(text)
        return text
