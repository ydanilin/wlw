# -*- coding: utf-8 -*-
import logging
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.shell import inspect_response
from scrapy.selector import Selector
from ..items import WlwItem

logger = logging.getLogger(__name__)


class WlwBaseSpider(CrawlSpider):
    name = 'wlw_base'
    allowed_domains = ['wlw.de']
    start_urls = ['Druckereien']#,
                  # 'Werbetechnik']

    def huj(value):
        t1 = -2  # value.find('blaudruck')
        t2 = -2  # value.find('golddruck')
        t3 = -2  # value.find('kranzschleifendruck')
        t4 = -2  # value.find('lithographie-steindruck')
        t5 = value.find('tiefdruck')
        if t1 >= 0 or t2 >= 0 or t3 >= 0 or t4 >= 0 or t5 >= 0:
            return value
        else:
            return None

    rules = (
        # 0. to go from start urls keyword synonym list to specific tifedruck
        Rule(LinkExtractor(restrict_css='a.list-group-item', process_value=huj)),
        # 1. from firms list to specific firm
        Rule(LinkExtractor(
            restrict_xpaths='//a[@data-track-type="click_serp_company_name"]'),
            callback='parse_group'),
        # 2. from a firm list page to the next one
        Rule(LinkExtractor(restrict_xpaths=('//ul[@class="pagination"]/'
                                            'li[not(@class)]/'
                                            'a[text()[contains(.,"chste")]]')))
    )

    def start_requests(self):
        for url in self.start_urls:
            fullUrl = ('https://www.wlw.de/de/kategorien?utf8=%E2%9C%93'
                       '&entered_search=1&q=') + url
            req = self.make_requests_from_url(fullUrl)
            req.meta['process_data'] = dict(initial_term=url,
                                            firms_pulled=0)
            yield req

    def parse_group(self, response):
        firmaId = response.xpath(
            '(.//*[@data-company-id]/@data-company-id)[1]').extract_first().strip()
        container = WlwItem(query=response.meta['process_data']['initial_term'],
                            category=response.meta['process_data']['classified_term'],
                            total_firms=response.meta['process_data']['firms_total'],
                            firmaId=firmaId)

        vcardDiv = response.css('div.profile-vcard')
        if vcardDiv:
            nameAddrDiv = vcardDiv.css('div.vcard-details')
            if nameAddrDiv:
                self.parseNameAddress(nameAddrDiv, container)
                # HFS Verpackungen GmbH
            else:
                logger.error('no name/address data for {0}'.format(firmaId))
            self.parsePhoneEmail(vcardDiv, container)

        else:
            logger.error('no visitcard section for {0}'.format(firmaId))

        angebotDiv = response.xpath('//div[@id="products-content"]')
        if angebotDiv:
            angebots = angebotDiv.xpath('.//article')
            angebotList = ''
            for angebot in angebots:
                sta = ''
                statuses = angebot.xpath('.//*[@title]')
                t2 = self.parseStatus(statuses, firmaId)
                angeName = statuses[0].xpath('.//ancestor::div[2]//text()').extract_first().strip()
                for key, value in t2.items():
                    if value == 'Yes':
                        if sta:
                            sta += ', ' + key
                        else:
                            sta = key
                if angebotList:
                    angebotList += ', ' + angeName + ' (' + sta + ')'
                else:
                    angebotList = angeName + ' (' + sta + ')'
            container['angebots'] = angebotList
            print(container)
            # details = angebot.xpath('./child::div')
            # t3 = self.parseAngebotDetails(details, firmaId)
            # print(angeName, t3)
        else:
            logger.error('no angebot section for {0}'.format(firmaId))
        # inspect_response(response, self)
        return container

    def parseNameAddress(self, nameAddrDiv, container):
        firmaId = container['firmaId']
        nameAddrLst = nameAddrDiv.xpath('.//text()').extract()
        if len(nameAddrLst) == 2:
            container['name'] = nameAddrLst[0].strip()
            addrFull = nameAddrLst[1].strip()
            container['full_addr'] = addrFull
            addrSplitted = re.split(r',\s+', addrFull)
            if len(addrSplitted) == 2:
                stHaus, indStadt = addrSplitted
                indSplitted = re.split(r'(DE-\d+)\s?', indStadt)
                if len(indSplitted) == 3:
                    dummy, index, stadt = indSplitted
                    container['zip'] = index
                    container['city'] = stadt
                else:
                    logger.error('when re.split index, city for {0}'.format(firmaId))
                streetSplitted = re.split(r'\s+(\d+)', stHaus)
                if len(streetSplitted) == 3:
                    street, house, dummy = streetSplitted
                    container['street'] = street
                    container['building'] = house
                else:
                    logger.error('when re.split street, for {0}'.format(firmaId))
            else:
                logger.error('when re.split full address for {0}'.format(firmaId))
        else:
            logger.error('parsing nameAddrDiv for {0}'.format(firmaId))
        return

    def parsePhoneEmail(self, vcardDiv, container):
        firmaId = container['firmaId']
        phone = ''
        email = ''
        site = ''
        svgs = vcardDiv.xpath('.//svg')
        for svg in svgs:
            t = svg.extract()
            if t.find('"#svg-icon-earphone"') >= 0:
                aTagTxt = svg.xpath('./ancestor::a[1]/@data-content').extract_first()
                sel = Selector(text=aTagTxt).xpath('.//text()')
                if len(sel) == 2:
                    phone = sel[1].extract().strip()
                else:
                    logger.error('no phone found for {0}'.format(firmaId))
            elif t.find('"#svg-icon-email"') >= 0:
                email = svg.xpath('./ancestor::a[1]//text()').extract_first().strip()[::-1]
            elif t.find('"#svg-icon-website"') >= 0:
                site = svg.xpath('./ancestor::a[1]/@href').extract_first().strip()
        container['phone'] = phone
        container['email'] = email
        container['site'] = site

    def parseStatus(self, statuses, firmaId):
        out = dict(producer='No', service='No', distrib='No', wholesaler='No')
        if len(statuses) == 4:
            for status in statuses:

                if status.xpath('./@title').extract_first().strip() == 'Hersteller':
                    t = status.xpath('./@class').extract_first().strip()
                    if t.find('disabled') < 0:
                        out['producer'] = 'Yes'
                elif status.xpath('./@title').extract_first().strip() == 'Dienstleister':
                    t = status.xpath('./@class').extract_first().strip()
                    if t.find('disabled') < 0:
                        out['service'] = 'Yes'
                elif status.xpath('./@title').extract_first().strip() == 'Händler':
                    t = status.xpath('./@class').extract_first().strip()
                    if t.find('disabled') < 0:
                        out['distrib'] = 'Yes'
                elif status.xpath('./@title').extract_first().strip() == 'Großhändler':
                    t = status.xpath('./@class').extract_first().strip()
                    if t.find('disabled') < 0:
                        out['wholesaler'] = 'Yes'
        else:
            logger.error('no Hersteller statuses got for {0}'.format(firmaId))
        return out

    def parseAngebotDetails(self, section, firmaId):
        person = ''
        phone = ''
        email = ''
        svgs = section.xpath('.//svg')
        for svg in svgs:
            t = svg.extract()
            if t.find('"#svg-icon-user"') >= 0:
                person = svg.xpath('./ancestor::li[1]//text()').extract_first().strip()
            elif t.find('"#svg-icon-earphone"') >= 0:
                aTagTxt = svg.xpath(
                    './ancestor::a[1]/@data-content').extract_first()
                sel = Selector(text=aTagTxt).xpath('.//text()')
                if len(sel) == 2:
                    phone = sel[1].extract().strip()
                else:
                    logger.error('no phone found for {0}'.format(firmaId))
            elif t.find('"#svg-icon-email"') >= 0:
                email = svg.xpath('./ancestor::a[1]//text()').extract_first().strip()[::-1]
        return dict(person=person, phone=phone, email=email)
