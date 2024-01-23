# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UptodownItem(scrapy.Item):
    # define the fields for your item here like:
    link = scrapy.Field()
    tag = scrapy.Field()
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


"""
{
    "link": "string",
    "domain": "string",
    "tag": ["string"],
    "crawling_time": "yyyy-MM-dd HH:mm:ss",
    "crawling_time_epoch": "epochmillis",
    "path_data_raw": "string",
    "path_data_clean": "string",
    "reviews_name": "string",    
    "location_reviews": "string",
    "category_reviews": "string",
    "total_reviews": "integer",
    "reviews_rating": {
      "total_rating": "integer",
      "detail_total_rating": [{
          "score_rating": "integer",
          "category_rating": "string"
      }]
    },
    "detail_reviews": {
      "username_reviews": "string",
      "image_reviews": "string",
      "created_time": "yyyy-MM-dd HH:mm:ss",
      "created_time_epoch":"epochmillis",
      "email_reviews": "string",
      "company_name": "string",
      "location_reviews": "string",
      "title_detail_reviews": "string",
      "reviews_rating": "integer",
      "detail_reviews_rating": [{
          "score_rating": "integer",
          "category_rating": "string"
      }],
      "total_likes_reviews": "integer",
      "total_dislikes_reviews": "integer",
      "total_reply_reviews": "integer",
      "content_reviews": "string",
      "reply_content_reviews": {
          "username_reply_reviews": "string",
          "content_reviews": "string"
      },
      "date_of_experience":"yyyy-MM-dd HH:mm:ss",
      "date_of_experience_epoch":"epochmillis"
  }
}
"""