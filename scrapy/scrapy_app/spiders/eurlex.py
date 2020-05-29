# -*- coding: UTF-8 -*-
import logging
import re
from datetime import datetime, MAXYEAR
from enum import Enum
from urllib.parse import urlparse

import scrapy


class EurLexType(Enum):
    DECISIONS = 'https://eur-lex.europa.eu/search.html?qid=1583164503757&DB_TYPE_OF_ACT=decision&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=DECISION&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'
    DIRECTIVES = 'https://eur-lex.europa.eu/search.html?qid=1583164454907&DB_TYPE_OF_ACT=directive&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=DIRECTIVE&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'
    REGULATIONS = 'https://eur-lex.europa.eu/search.html?qid=1582550896987&DB_TYPE_OF_ACT=regulation&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=REGULATION&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'


class EurLexSpider(scrapy.Spider):
    download_delay = 0.1
    name = 'eurlex'
    date_format = '%d/%m/%Y'

    def __init__(self, spider_type=None, year=None, *args, **kwargs):
        super(EurLexSpider, self).__init__(*args, **kwargs)
        if not spider_type:
            logging.log(logging.WARNING,
                        'EurLex spider_type not given, default to DECISIONS')
            spider_type = EurLexType.DECISIONS
        else:
            spider_type_arg = spider_type.upper()
            # this can throw a KeyError if spider_type_arg is not known in the enum
            spider_type = EurLexType[spider_type_arg]
            logging.log(logging.INFO, 'EurLex spider_type: ' + spider_type.name)

        if not year:
            logging.log(logging.WARNING, 'No year given, fetching all years')
            start_url = spider_type.value
        else:
            logging.log(logging.INFO, 'Fetching year: ' + year)
            start_url = spider_type.value + "&DD_YEAR=" + year

        self.start_urls = [start_url]

    def date_safe(self, date_string):
        try:
            return datetime.strptime(date_string, self.date_format)
        except:
            return "n/a"

    def parse(self, response):
        for h2 in response.css("div.EurlexContent div.SearchResult"):
            meta = {
                'doc_link': h2.css("::attr(name)").extract_first().replace('/AUTO/', '/EN/ALL/')
            }
            yield scrapy.Request(meta['doc_link'], callback=self.parse_document, meta=meta)

        next_page_url = response.css("a[title='Next Page']::attr(href)").extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))

    def parse_document(self, response):
        parsed_uri = urlparse(response.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        result_dict = {}

        celex = response.url.split(':')[-1]
        result_dict['celex'] = celex

        body = response.css('div.panel-body')
        if body:
            title = body.xpath('.//p[@id="englishTitle"]')
            if title:
                title = title.xpath('.//text()').get().replace('\n', ' ').strip()
                result_dict['title'] = title

            status = body.css('p.forceIndicator')
            if status:
                status = ''.join(status.xpath('.//text()').getall()).replace('\n', ' ').strip().split(':')[0]
                result_dict['status'] = status

            various = body.xpath('.//p[not(@*)]')
            if various:
                links = various.xpath('.//a/@href').getall()
                for link in links:
                    if 'eli' in link:
                        result_dict['ELI'] = link
                        break

                various_text = ''.join(various.xpath('.//em//text()').getall()).replace('\n', ' ').strip()
                result_dict['various'] = various_text

        self.parse_dates(response, result_dict)
        self.parse_classifications(response, result_dict)
        self.parse_misc(response, result_dict)
        self.parse_procedures(response, result_dict)
        self.parse_relationships(response, result_dict)
        # self.parse_content(response, result_dict)

        result_dict.update({'url': response.url})

        summary_link = response.xpath("//li[@class='legissumTab']/a/@href").get()
        if summary_link:
            summary_link_abs = summary_link.replace('./../../../', base_url)
            yield scrapy.Request(summary_link_abs, callback=self.parse_document_summary)
        yield result_dict

    def parse_document_summary(self, response):
        result_dict = {}
        result_dict['doc_summary'] = True
        # check if multiple summaries are listed
        if response.xpath("//div[@id='documentView']//table//tr/th[text()='Summary reference']").get():
            pass
        else:
            result_dict['url'] = response.url
            celex = response.url.split(':')[-1]
            result_dict['celex'] = celex
            title = response.xpath('//div[@id="PP1Contents"]//p/text()').get()
            result_dict['title'] = title
            self.parse_classifications(response, result_dict)
            self.parse_dates(response, result_dict)
            self.parse_misc(response, result_dict)
            result_dict['html_content'] = response.xpath('//div[@id="text"]').get()
            return result_dict

    def parse_dates(self, response, result_dict):
        dates = response.xpath('//div[@id="PPDates_Contents"]')
        if dates:
            all_dates = []
            all_dates_type = []
            all_dates_info = []
            date_types = dates.xpath('.//dt')
            date_texts = dates.xpath('.//dd')
            for (t, d) in zip(date_types, date_texts):
                date_type = t.xpath('.//text()').get().split(':')[0].lower()
                date_value_all = ''.join(d.xpath('.//text()').getall()).split(';')
                if '/' in date_value_all[0]:
                    date_value = datetime.strptime(date_value_all[0], self.date_format)
                else:
                    date_value = datetime(MAXYEAR, 1, 1)
                date_info = date_value_all[1].replace('\n', ' ').strip() if len(date_value_all) > 1 else 'n/a'
                # date of document is our main "date"
                if date_type == 'date of document':
                    result_dict['date'] = date_value
                # handle other date_types to be appended to "dates"
                all_dates_type.append(date_type)
                all_dates.append(date_value)
                all_dates_info.append(date_info)
            result_dict.update({"dates": all_dates})
            result_dict.update({"dates_type": all_dates_type})
            result_dict.update({"dates_info": all_dates_info})

    def parse_classifications(self, response, result_dict):
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url))
        classifications = response.xpath('//div[@id="PPClass_Contents"]')
        if classifications:
            classifications_types = classifications.xpath('.//dt')
            classifications_data = classifications.xpath('.//dd')
            all_classifications_type = []
            all_classifications_label = []
            all_classifications_code = []
            for (t, d) in zip(classifications_types, classifications_data):
                ref_codes = d.xpath('.//a')
                for ref_code in ref_codes:
                    all_classifications_type.append(t.xpath('.//text()').get().split(':')[0].lower())
                    element_name = ''.join(ref_code.xpath('.//text()').getall()).replace('\n', ' ').strip()
                    ref_code = str(ref_code.xpath('.//@href').get()).replace('./../../../', base_url)
                    element_code = re.search('CODED=(.*)&', ref_code)
                    element_code = element_code.group(1)
                    all_classifications_label.append(element_name)
                    all_classifications_code.append(element_code if element_code else 'n/a')

            result_dict.update(
                {"classifications_label": all_classifications_label})
            result_dict.update({"classifications_type": all_classifications_type})
            result_dict.update({"classifications_code": all_classifications_code})

    def parse_misc(self, response, result_dict):
        misc = response.xpath('//div[@id="PPMisc_Contents"]')
        if misc:
            misc_types = misc.xpath('.//dt')
            misc_data = misc.xpath('.//dd')
            for (t, d) in zip(misc_types, misc_data):
                misc_type = t.xpath('.//text()').get().split(':')[0].lower()
                misc_value = d.xpath('.//text()').get().replace('\n', '').strip()
                # save 'form' value also as general document type value
                if misc_type == 'form' and not result_dict.get('doc_summary'):
                    result_dict['type'] = misc_value
                result_dict.update({'misc_' + misc_type: misc_value})

    def parse_procedures(self, response, result_dict):
        procedures = response.xpath('//div[@id="PPProc_Contents"]')
        if procedures:
            all_procedures_links_url = []
            all_procedures_links_name = []
            all_procedures_number = []
            procedure_types = procedures.xpath('.//dt')
            procedure_data = procedures.xpath('.//dd')
            for (t, d) in zip(procedure_types, procedure_data):
                procedure_type = t.xpath('.//text()').get().split(':')[0].lower().replace('\n', '')
                if procedure_type == 'procedure number':
                    for number in d.xpath('.//text()').get().split('\n'):
                        if number.strip():
                            all_procedures_number.append(number.strip())

                elif procedure_type == 'link':
                    procedure_link = d.xpath('.//a')
                    if procedure_link:
                        name = procedure_link.xpath('.//text()').get().replace('\n', '').strip()
                        link = procedure_link.xpath('./@href').get()
                        all_procedures_links_name.append(name)
                        all_procedures_links_url.append(link)
                else:
                    proc_misc_value = d.xpath('.//text()').get().replace('\n', ' ').strip()
                    result_dict.update({'procedure_' + procedure_type: proc_misc_value})

            result_dict.update({"procedures_number": all_procedures_number})
            result_dict.update(
                {"procedures_links_name": all_procedures_links_name})
            result_dict.update({"procedures_links_url": all_procedures_links_url})

    def parse_relationships(self, response, result_dict):
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url))
        relationships = response.xpath('//div[@id="PPLinked_Contents"]')
        if relationships:
            rel_types = relationships.xpath('.//dt[not(@class)]')
            rel_texts = relationships.xpath('.//dd[not(@class)]')
            all_relationships_legal_basis = []
            all_relationships_proposal = []
            redirect_link_value = ''
            # treaty is always the first
            result_dict.update(
                {'relationships_treaty': ''.join(rel_texts[0].xpath('.//text()').getall()).replace('\n', ' ').strip()})
            # iterate over next relationships
            for rel_text in rel_texts[1:]:
                common_index = rel_texts.index(rel_text)
                rel_category = rel_types[common_index].xpath('.//text()').get().split(':')[0].replace('\n', '').lower()
                redirect_link_value = ''
                redirect_links = rel_text.xpath('.//a')
                for redirect_link in redirect_links:
                    redirect_link_text = redirect_link.xpath('.//text()').get()
                    redirect_link_url = redirect_link.xpath('./@href').get().replace('./../../../', base_url)
                    if 'CELEX' in redirect_link_url:
                        redirect_link_value = redirect_link_text
                    else:
                        redirect_link_value = redirect_link_url
                    if rel_category == 'legal basis':
                        all_relationships_legal_basis.append(redirect_link_value)
                    elif rel_category == 'proposal':
                        all_relationships_proposal.append(redirect_link_value)
            # oj link is always the last
            result_dict.update({'relationships_oj_link': redirect_link_value})

            result_dict.update({"relationships_legal_basis": all_relationships_legal_basis})
            result_dict.update({"relationships_proposal": all_relationships_proposal})

            amendments = relationships.xpath('.//tbody')
            all_amendments_relation = []
            all_amendments_act = []
            all_amendments_comment = []
            all_amendments_subdivision = []
            all_amendments_from = []
            all_amendments_to = []
            if amendments:
                rows = amendments.xpath('.//tr')
                if rows:
                    n = 0
                    for tr in rows:
                        td = tr.xpath('.//td')
                        relation = td[0].xpath('.//text()').get(default='').replace('\n', ' ').strip()
                        act = td[1].xpath('.//a//text()').get(default='').replace('\n', ' ').strip()
                        comment = td[2].xpath('.//text()').get(default='').replace('\n', ' ').strip()
                        subdivision_concerned = td[3].xpath('.//text()').get(default='').replace('\n', ' ').strip()
                        as_from = td[4].xpath('.//text()').get(default='').replace('\n', ' ').strip()
                        to = td[5].xpath('.//text()').get(default='').replace('\n', ' ').strip()
                        n += 1
                        all_amendments_relation.append(relation if relation else 'n/a')
                        all_amendments_act.append(act if act else 'n/a')
                        all_amendments_comment.append(comment if comment else 'n/a')
                        all_amendments_subdivision.append(subdivision_concerned if subdivision_concerned else 'n/a')
                        all_amendments_from.append(self.date_safe(as_from) if as_from else 'n/a')
                        all_amendments_to.append(self.date_safe(to) if to else 'n/a')
                    result_dict.update({'amendments_relation': all_amendments_relation})
                    result_dict.update({'amendments_act': all_amendments_act})
                    result_dict.update({'amendments_comment': all_amendments_comment})
                    result_dict.update({'amendments_subdivision': all_amendments_subdivision})
                    result_dict.update({'amendments_from': all_amendments_from})
                    result_dict.update({'amendments_to': all_amendments_to})

    def parse_content(self, response, result_dict):
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(response.url))
        oj = response.xpath('//div[@id="PP2Contents"]')
        # only store english pdf doc url(s)
        if oj is not None:
            pdf_docs = []
            pdfs = oj.xpath('.//li')
            for pdf in pdfs:
                pdf = pdf.xpath('.//a/@href').get().replace('./../../../', base_url)
                if 'EN/TXT/PDF/' in pdf:
                    pdf_docs.append(pdf)
            result_dict.update({"pdf_docs": pdf_docs})
