# -*- coding: UTF-8 -*-

import logging
import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import lxml.html
from langdetect import detect
from lxml.html.clean import Cleaner
from scrapy.exceptions import NotConfigured
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class FullSiteSpider(CrawlSpider):
    pwd = os.getcwd()
    name = "fullsite"
    logger = logging.getLogger('FullSiteSpider')

    def __init__(self, *args, **kwargs):
        super(FullSiteSpider, self).__init__(*args, **kwargs)
        self.url = kwargs.get('url')
        if not self.url:
            raise NotConfigured(
                "Expecting a 'url' property to be configured, pointing to the first page on the site")
        parsed_uri = urlparse(self.url)
        self.allowed_domains = ['{uri.netloc}/'.format(uri=parsed_uri)]
        self.start_urls = ['{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)]

        self.website = kwargs.get('website')
        if not self.website:
            raise NotConfigured(
                "Expecting a 'website' property to be configured, declaring the name of the website to be scraped"
            )

        self.cleaner = Cleaner(style=True, links=True, add_nofollow=True,
                               page_structure=False, safe_attrs_only=False)

        self.rules = (
            Rule(
                LinkExtractor(
                    tags='a',
                    attrs='href',
                    unique=True
                ),
                callback='parse',
                follow=True
            ),
        )

    def parse(self, response):
        title = response.xpath('//head/title/text()').get()
        cleaned_html = self.cleaner.clean_html(response.body)
        document = lxml.html.document_fromstring(cleaned_html)
        document_txt = document.text_content()
        detected_lang = detect(document_txt)
        self.logger.debug("Detected language '%s' for: %s",
                          detected_lang, response.url)

        yield {
            'url': response.url,
            'title': title,
            'website': self.website,
            'content_html': cleaned_html.decode('utf-8'),
            'date': datetime.now(timezone.utc).isoformat()[:-6] + 'Z',
            'language': detected_lang,
            'pdf_docs': []
        }
