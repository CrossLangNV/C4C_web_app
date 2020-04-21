# -*- coding: UTF-8 -*-

import bs4
import scrapy
from datetime import datetime


class EsmaScraperSpider(scrapy.Spider):
    download_delay = 10.0
    name = 'esma'
    start_urls = [
        'https://www.esma.europa.eu/databases-library/esma-library/?f%5B0%5D=im_field_document_type%3A45',
    ]
    
    def get_metadata(self, element):
        newdict = {}
        publication_date = element.find("td", {"class": "esma_library-date"})
        reference_number = element.find("td", {"class": "esma_library-ref"})
        publication_title = element.find("td", {"class": "esma_library-title"})
        publication_type = element.find("td", {"class": "esma_library-type"})
        publication_section = element.find("td", {"class": "esma_library-section"})
        if publication_date is not None:
            date = publication_date.getText()
            newdict.update({"date": datetime.strptime(date, '%d/%m/%Y')})
        if reference_number is not None:
            reference = reference_number.getText()
            newdict.update({"reference": reference})
        if publication_title is not None:
            title = publication_title.getText()
            newdict.update({"title": title})
        if publication_type is not None:
            type = publication_type.getText()
            newdict.update({"type": type})
        if publication_section is not None:
            section = publication_section.getText()
            newdict.update({"section": section})
        pdf_link = element.find('a')
        if pdf_link is not None:
            pdf_link = pdf_link.get('href')
            newdict.update({"pdf_docs": [pdf_link]})
            # doc url == pdf url for esma
            newdict.update({"url": pdf_link})
        return newdict

    def parse(self, response):
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        all_publications_on_a_page = soup.findAll("tr")
        for element in all_publications_on_a_page:
            yield self.parse_single(element)
        next_page_url = response.css("li.pager-next > a::attr(href)").extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))

    def parse_single(self, element):
        data = self.get_metadata(element)
        return data