import logging
import re
from enum import Enum
from datetime import datetime

import scrapy


class EbaType(Enum):
    GUIDELINES = 'https://eba.europa.eu/document-library?search_api_views_fulltext=&field_document_type=pdf&field_tags=1&field_doc_display_date%5Bmin%5D%5Bdate%5D=&field_doc_display_date%5Bmax%5D%5Bdate%5D=&items_per_page=75&field_category%5B%5D=388'
    RECOMMENDATIONS = 'https://eba.europa.eu/document-library?search_api_views_fulltext=&field_document_type=pdf&field_tags=1&field_doc_display_date%5Bmin%5D%5Bdate%5D=&field_doc_display_date%5Bmax%5D%5Bdate%5D=&items_per_page=75&field_category%5B%5D=395'


class EbaSpider(scrapy.Spider):
    download_delay = 10.0
    name = 'eba'
    date_format = '%d/%m/%Y'
    date_regex = re.compile(r'\d{2}/\d{2}/\d{4}')
    spider_type = None

    def __init__(self, spider_type=None, *args, **kwargs):
        super(EbaSpider, self).__init__(*args, **kwargs)
        if not spider_type:
            logging.log(logging.WARNING, 'Eba spider_type not given, default to GUIDELINES')
            self.spider_type = EbaType.GUIDELINES
        else:
            spider_type_arg = spider_type.upper()
            # this can throw a KeyError if spider_type_arg is not known in the enum
            self.spider_type = EbaType[spider_type_arg]
            logging.log(logging.INFO, 'Eba spider_type: ' + self.spider_type.name)
        self.start_urls = [self.spider_type.value]

    def parse(self, response):
        # language_tag = response.css("html::attr(lang)").extract_first()
        for td in response.css("td.views-field"):
            date_text = td.css("div.ResultDetails p::text").extract_first()
            dates = self.date_regex.findall(date_text)
            data = {
                'title': td.css("p.ResultTitle a::text").extract_first(),
                'date': datetime.strptime(dates[0], self.date_format),
                'date_last_update': datetime.strptime(dates[1], self.date_format),
                'type': self.spider_type.name.title(),
                'url': td.css("p.ResultTitle a::attr(href)").extract_first(),
                'pdf_docs': td.css("p.ResultTitle a::attr(href)").extract()
            }
            yield data

        nex_page_url = response.css("li.next a::attr(href)").extract_first()
        if nex_page_url is not None:
            yield scrapy.Request(response.urljoin(nex_page_url))
