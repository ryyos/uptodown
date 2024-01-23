# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UptodownItem(scrapy.Item):
    # define the fields for your item here like:
    link = scrapy.Field()
    tag = scrapy.Field()
    id = scrapy.Field()
    crawling_time = scrapy.Field()
    crawling_time_epoch = scrapy.Field()
    path_data_raw = scrapy.Field()
    path_data_clean = scrapy.Field()
    reviews_name = scrapy.Field()
    location_reviews = scrapy.Field()
    category_reviews = scrapy.Field()
    total_reviews = scrapy.Field()
    detail_reviews = scrapy.Field()
    reviews_rating = scrapy.Field()
    detail_application = scrapy.Field()
    ...
