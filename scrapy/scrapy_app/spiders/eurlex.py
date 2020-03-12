# -*- coding: UTF-8 -*-
import logging
import re
from datetime import datetime
from enum import Enum
from urllib.parse import urlparse

import bs4
import scrapy


class EurLexType(Enum):
    DECISIONS = 'https://eur-lex.europa.eu/search.html?qid=1583164503757&DB_TYPE_OF_ACT=decision&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=DECISION&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'
    DIRECTIVES = 'https://eur-lex.europa.eu/search.html?qid=1583164454907&DB_TYPE_OF_ACT=directive&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=DIRECTIVE&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'
    REGULATIONS = 'https://eur-lex.europa.eu/search.html?qid=1582550896987&DB_TYPE_OF_ACT=regulation&CASE_LAW_SUMMARY=false&DTS_DOM=ALL&excConsLeg=true&typeOfActStatus=REGULATION&type=advanced&CASE_LAW_JURE_SUMMARY=false&SUBDOM_INIT=ALL_ALL&DTS_SUBDOM=ALL_ALL'


class EurLexSpider(scrapy.Spider):
    download_delay = 10.0
    name = 'eurlex'
    date_format = '%d/%m/%Y'

    def __init__(self, spider_type=None, *args, **kwargs):
        super(EurLexSpider, self).__init__(*args, **kwargs)
        if not spider_type:
            logging.log(logging.WARNING, 'EurLex spider_type not given, default to DECISIONS')
            spider_type = EurLexType.DECISIONS
        else:
            spider_type_arg = spider_type.upper()
            # this can throw a KeyError if spider_type_arg is not known in the enum
            spider_type = EurLexType[spider_type_arg]
            logging.log(logging.INFO, 'EurLex spider_type: ' + spider_type.name)
        self.start_urls = [spider_type.value]

    def get_metadata(self, response):
        soup = bs4.BeautifulSoup(response.text, features="html.parser")
        parsed_uri = urlparse(response.url)
        base_url = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        newdict = {}

        celex = soup.find('h1', {'class': 'DocumentTitle'}).getText()
        celex = str(celex).split()
        newdict.update({'celex': celex[1]})

        body = soup.find('div', {'class': 'panel-body'})
        if body is not None:

            title = body.find('p', {'id': 'englishTitle'})
            if title:
                title = title.getText().replace('\n', ' ')
                newdict.update({"title": title})

            status = body.find('p', {'class': 'forceIndicator'})
            if status:
                status = status.getText().replace('\n', '')
                newdict.update({"status": status})

            various = body.findAll(lambda tag: tag.name == 'p' and not tag.attrs)
            if various:
                for x in various:
                    x = x.find('a')
                    if x:
                        eli = x['href']
                        newdict.update({'ELI': eli})

            uniq_code = various[0].getText().replace('\n', '')
            pages_etc = various[1].getText().replace('\n', '')
            newdict.update({'various': str(uniq_code + ', ' + pages_etc)})

        oj = soup.find('div', {'id': 'PP2Contents'})
        # only store english pdf doc url(s)
        if oj is not None:
            pdf_docs = []
            pdfs = oj.findAll('li')
            for pdf in pdfs:
                pdf = pdf.find('a')['href'].replace('./../../../', base_url)
                if 'EN/TXT/PDF/' in pdf:
                    pdf_docs.append(pdf)
            newdict.update({"pdf_docs": pdf_docs})

        dates = soup.find('div', {'id': 'PPDates_Contents'})
        if dates is not None:
            all_dates = []
            all_dates_type = []
            all_dates_info = []
            date_texts = dates.findAll('dd')
            date_types = dates.findAll('dt')
            for (x, y) in zip(date_types, date_texts):
                date_type = x.getText().split(':')[0].lower()
                value = y.getText().split(';')
                date_value = datetime.strptime(value[0], self.date_format)
                date_info = value[1].replace('\n', ' ').strip() if len(value) > 1 else 'n/a'
                # date of document is our main "date"
                if date_type == 'date of document':
                    newdict.update({"date": date_value})
                # handle other date_types to be appended to "dates"
                all_dates_type.append(date_type)
                all_dates.append(date_value)
                all_dates_info.append(date_info)
            newdict.update({"dates": all_dates})
            newdict.update({"dates_type": all_dates_type})
            newdict.update({"dates_info": all_dates_info})

        classifications = soup.find('div', {'id': 'PPClass_Contents'})
        if classifications is not None:
            classifications_data = classifications.findAll('dd')
            classifications_types = classifications.findAll('dt')
            all_classifications_type = []
            all_classifications_label = []
            all_classifications_code = []
            for (x, y) in zip(classifications_types, classifications_data):
                ref_codes = y.findAll('a')
                for ref_code in ref_codes:
                    all_classifications_type.append(x.getText().split(':')[0].lower())
                    element_name = ref_code.getText().replace('\n', '')
                    ref_code = str(ref_code['href']).replace('./../../../', base_url)
                    element_code = re.search('CODED=(.*)&', ref_code)
                    element_code = element_code.group(1)
                    all_classifications_label.append(element_name)
                    all_classifications_code.append(element_code if element_code else 'n/a')

            newdict.update({"classifications_label": all_classifications_label})
            newdict.update({"classifications_type": all_classifications_type})
            newdict.update({"classifications_code": all_classifications_code})

        miscellaneous = soup.find('div', {'id': 'PPMisc_Contents'})
        if miscellaneous is not None:
            misc_texts = miscellaneous.findAll('dd')
            misc_types = miscellaneous.findAll('dt')
            for (x, y) in zip(misc_types, misc_texts):
                misc_type = x.getText().split(':')[0].lower()
                value = y.getText().replace('\n', ' ').strip()
                misc_value = value
                # save 'form' value also as general document type value
                if misc_type == 'form':
                    newdict.update({"type": value})
                newdict.update({'misc_' + misc_type: value})

        procedure = soup.find('div', {'id': 'PPProc_Contents'})
        if procedure is not None:
            all_procedures_links_url = []
            all_procedures_links_name = []
            all_procedures_number = []
            procedure_types = procedure.findAll('dt')
            procedure_data = procedure.findAll('dd')
            for (x, y) in zip(procedure_types, procedure_data):
                procedure_type = x.getText().split(':')[0].lower().replace('\n', '')
                if procedure_type == 'procedure number':
                    for number in y.getText().split('\n'):
                        if number.strip():
                            all_procedures_number.append(number.strip())

                elif procedure_type == 'link':
                    procedure_links = y.findAll('a')
                    if procedure_links is not None:
                        name = procedure_links[0].getText().replace('\n', '').strip()
                        link = procedure_links[0]['href']
                        all_procedures_links_name.append(name)
                        all_procedures_links_url.append(link)
                else:
                    value = y.getText().replace('\n', ' ').strip()
                    newdict.update({'procedure_' + procedure_type: value})

            newdict.update({"procedures_number": all_procedures_number})
            newdict.update({"procedures_links_name": all_procedures_links_name})
            newdict.update({"procedures_links_url": all_procedures_links_url})

        relationships = soup.find('div', {'id': 'PPLinked_Contents'})
        if relationships is not None:
            date_types = relationships.findAll('dt', attrs={'class': None})
            date_texts = relationships.findAll('dd', attrs={'class': None})
            all_relationships_legal_basis = []
            all_relationships_proposal = []
            for element in date_texts[1:]:
                common_index = date_texts.index(element)
                rel_category = date_types[common_index].getText().split(':')[0].replace('\n', '').lower()
                redirect_link_value = ''
                redirect_links = element.findAll('a')
                for redirect_link in redirect_links:
                    redirect_link_text = redirect_link.getText()
                    redirect_link_url = redirect_link['href'].replace('./../../../', base_url)
                    if 'CELEX' in redirect_link_url:
                        redirect_link_value = redirect_link_text
                    else:
                        redirect_link_value = redirect_link_url
                    if rel_category == 'legal basis':
                        all_relationships_legal_basis.append(redirect_link_value)
                    elif rel_category == 'proposal':
                        all_relationships_proposal.append(redirect_link_value)
            # treaty is always the first
            newdict.update({'relationships_treaty': date_texts[0].getText().replace('\n', '')})
            # oj link is always the last
            newdict.update({'relationships_oj_link': redirect_link_value})

            newdict.update({"relationships_legal_basis": all_relationships_legal_basis})
            newdict.update({"relationships_proposal": all_relationships_proposal})

            amendment_to = relationships.find('tbody')
            all_amendments_relation = []
            all_amendments_act = []
            all_amendments_comment = []
            all_amendments_subdivision = []
            all_amendments_from = []
            all_amendments_to = []
            if amendment_to is not None:
                rows = amendment_to.findAll('tr')
                if rows is not None:
                    n = 0
                    for tr in rows:
                        td = tr.findAll('td')
                        relation = td[0].getText().replace('\n', '')
                        act = td[1].getText().replace('\n', '')
                        comment = td[2].getText().replace('\n', '')
                        subdivision_concerned = td[3].getText().replace('\n', '')
                        as_from = td[4].getText().replace('\n', '')
                        to = td[5].getText().replace('\n', '')
                        n += 1
                        all_amendments_relation.append(relation if relation else 'n/a')
                        all_amendments_act.append(act if act else 'n/a')
                        all_amendments_comment.append(comment if comment else 'n/a')
                        all_amendments_subdivision.append(subdivision_concerned if subdivision_concerned else 'n/a')
                        all_amendments_from.append(datetime.strptime(as_from, self.date_format) if as_from else 'n/a')
                        all_amendments_to.append(datetime.strptime(to, self.date_format) if to else 'n/a')
                    newdict.update({'amendments_relation': all_amendments_relation})
                    newdict.update({'amendments_act': all_amendments_act})
                    newdict.update({'amendments_comment': all_amendments_comment})
                    newdict.update({'amendments_subdivision': all_amendments_subdivision})
                    newdict.update({'amendments_from': all_amendments_from})
                    newdict.update({'amendments_to': all_amendments_to})

        newdict.update({'url': response.url})
        return newdict

    def parse(self, response):
        for h2 in response.css("div.EurlexContent div.SearchResult"):
            meta = {
                'doc_link': h2.css("::attr(name)").extract_first().replace('/AUTO/', '/EN/ALL/')
            }
            yield scrapy.Request(meta['doc_link'], callback=self.parse_single, meta=meta)

        next_page_url = response.css("a[title='Next Page']::attr(href)").extract_first()
        if next_page_url is not None:
            yield scrapy.Request(response.urljoin(next_page_url))

    def parse_single(self, response):
        data = self.get_metadata(response)
        return data
