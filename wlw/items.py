# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, MapCompose, Compose, Join, Identity


def puk(svg):
    print('puk called')
    if svg.find('"#svg-icon-website"') >= 0:
        return svg.xpath('./ancestor::a[1]/@href').extract_first().strip()


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


class WlwLoader(ItemLoader):
    default_input_processor = MapCompose(str.strip)
    default_output_processor = TakeFirst()

    total_firms_in = Identity()

    site_in = MapCompose(puk)
