# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join, Identity


def siteBasedOnSvg(svg):
    if svg.extract().find('"#svg-icon-website"') >= 0:
        return svg.xpath('./ancestor::a[1]/@href').extract_first()


def emailBasedOnSvg(svg):
    if svg.extract().find('"#svg-icon-email"') >= 0:
        return svg.xpath('./ancestor::a[1]//text()').extract_first()


def phoneBasedOnSvg(svg):
    if svg.extract().find('"#svg-icon-earphone"') >= 0:
        return svg.xpath('./ancestor::a[1]/@data-content').extract_first()


def angebot(ang):
    statuses = ang.xpath('.//*[@title]')
    a = statuses[0].xpath('.//ancestor::div[2]//text()').extract_first().strip()
    s = StatusItemLoader(item=StatusItem(), selector=ang)
    st = s.nested_xpath('.//*[@title]')
    st.add_value('status', st.selector)
    stt = s.load_item()
    return '{0} ({1})'.format(a, stt['status'])


class WlwItem(scrapy.Item):
    # define the fields for your item here like:
    query = scrapy.Field()
    category = scrapy.Field()
    total_firms = scrapy.Field()
    firmaId = scrapy.Field()
    name = scrapy.Field()
    full_addr = scrapy.Field()
    street = scrapy.Field()
    building = scrapy.Field()
    zip = scrapy.Field()
    city = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    site = scrapy.Field()
    angebots = scrapy.Field()


class StatusItem(scrapy.Item):
    status = scrapy.Field()


class WlwLoader(ItemLoader):
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    total_firms_in = Identity()
    site_in = MapCompose(siteBasedOnSvg, str.strip)
    email_in = MapCompose(emailBasedOnSvg, str.strip, lambda x: x[::-1])
    phone_in = MapCompose(phoneBasedOnSvg, str.strip)
    angebots_in = MapCompose(angebot, str.strip)
    angebots_out = Join(', ')


def huj(t):
    if t.xpath('./@class').extract_first().find('disabled') < 0:
        type_ = t.xpath('./@title').extract_first().strip()
        if type_ == 'Hersteller':
            return 'producer'
        elif type_ == 'Dienstleister':
            return 'service'
        elif type_ == 'Händler':
            return 'distrib'
        elif type_ == 'Großhändler':
            return 'wholesaler'


class StatusItemLoader(ItemLoader):
    status_in = MapCompose(huj)
    status_out = Join(', ')


