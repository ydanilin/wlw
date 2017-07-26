# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


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
    angeb_name = scrapy.Field()
    producer = scrapy.Field()
    service = scrapy.Field()
    distrib = scrapy.Field()
    wholesaler = scrapy.Field()
    a_person = scrapy.Field()
    a_phone = scrapy.Field()
    a_email = scrapy.Field()
