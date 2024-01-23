import scrapy

from typing import List
from icecream import ic
from time import strftime, time

from scrapy.http import Response
from scrapy.http import Request
from scrapy.selector import Selector
from scrapy.http import request
from uptodown.items import UptodownItem
from uptodown.items import DetailItem

class ServiceSpider(scrapy.Spider):
    name = "service"
    start_urls = ["https://id.uptodown.com"]
    
    _platforms = ['andorid', 'windows', 'mac']

# https://miui-security.id.uptodown.com/mng/v2/app/732541/comments

    def parse(self, response: Response):
        url_platforms = response.css('#platform-item > a ::attr(href)').getall()

        self.items = UptodownItem()

        for url in url_platforms:
            yield Request(url=url, callback=self.__collect_types)

    ...

    def __collect_types(self, response: Response) -> List[str]:
        for type in response.css('#main-left-panel-ul-id > div:nth-child(3) div[class="li"] > a ::attr(href)').getall():
            yield Request(url=type, callback=self.__collect_apps, cb_kwargs=dict(type=type))
        ...
    
    
    def __collect_apps(self, response: Response, type) -> List[str]:
        for app in response.css('div[class="name"] > a ::attr(href)').getall():
            yield Request(url=app, callback=self.__parser_app, cb_kwargs=dict(type=type))
        ...


    def __extract_url(self, url: str) -> dict:
        pieces = url.split('/')
        return {
            "platform": pieces.pop(),
            "url": '/'.join(pieces)
        }
    

    def __strip(self, text: str) -> str:
        try:
            return text.strip().replace('\n', '')
        except Exception:
            return text
        ...
    

    def __parser_app(self, response: Response, type) -> dict:
        body: Response = response.css('div.c1')

        ic(response.url)

        header = {
            "id": body.css('#detail-app-name ::attr(code)').get(),
            "title": self.__strip(body.css('#detail-app-name ::text').get()),
            "information": body.css('div.detail > h2 ::text').get(),
            "url": self.__extract_url(response.url)["url"],
            "type": type.split('/')[-1],
            "platform": self.__extract_url(response.url)["platform"],
            "version": body.css('div.version ::text').get(),
            "author": self.__strip(body.css('div.autor a ::text').get()),
            "descriptions": body.css('div.text-description p::text').extract(),
            "total_reviews": body.css('#more-comments-rate-section ::text').extract()[-1].strip() if body.css('#more-comments-rate-section') else None,
            "ratings": float(body.css('#rating ::text').get().strip()) if body.css('#rating') else None,
            "technical-information": {
                key.css('td:nth-child(2) ::text').get().strip(): key.css('td:last-child ::text').get().strip() for key in body.css('#technical-information tr')
            },
            "previous_version": [
                {
                    "version": prev.css('span.version ::text').get(),
                    "date": prev.css('span.date ::text').get(),
                    "sdk": prev.css('span.sdkVersion ::text').get()
                } for prev in body.css('#versions-items-list > div')
            ]
        }

        yield Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments', callback=self.__extract_review, cb_kwargs=header)

    def __extract_review(self, response: Response, **header) -> List[dict]:
        reviews = Selector(text=response.json()['content'])

        offset = 10
        reviews_temp: List[dict] = []

        for review in reviews.css('div.comment'):
            reviews_temp.append({
                "username": self.__strip(review.css('span.user ::text').get()),
                "avatar": review.css('img')[0].attrib['src'],
                "posted": self.__strip(review.css('span:nth-child(3) ::text').get()),
                "ratings": len(review.css('img.active')),
                "likes": review.css('div[name="favs-icon"] span::text').get() if not "Like" else None,
                "comment": review.css('p ::text').get()
            })

        request = Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments/unixtime?offset={offset}', 
                          callback=self.__exctract_review_api, 
                          errback=self.__finally,
                          cb_kwargs={
                              "header": header,
                              "reviews": reviews_temp
                          })

        yield request
        ...

    def __exctract_review_api(self, response: Response, header, reviews, offset=20):
        reviews_temp = response.json()
        offset +=10

        ic(offset)
        ic(len(reviews))

        ic({
            "len reviws": len(reviews),
            "link": header["url"]
        })
        if reviews_temp["success"]:
            for review in reviews_temp["data"]:
                reviews.append({
                    "username": review["userName"],
                    "avatar": review["icon"],
                    "posted": review["timeAgo"],
                    "ratings": review["rating"],
                    "likes": review["likes"],
                    "comment": review["text"]
                })

            request = Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments/unixtime?offset={offset}', 
                              callback=self.__exctract_review_api, 
                              errback=self.__finally,
                              cb_kwargs={
                                  "header": header,
                                  "reviews": reviews,
                                  "offset": offset
                                  })

            yield request
        ...

    def __finally(self, failure):
        ic('masuk finaly')

        ic({
            "total finaly": len(failure.request.cb_kwargs["reviews"]),
            "title": failure.request.cb_kwargs["header"]["title"],
            "link": failure.request.cb_kwargs["header"]["url"]
        })

        details = DetailItem()
        details["link"] = failure.request.cb_kwargs["header"]["url"]
        details["id"] = failure.request.cb_kwargs["header"]["id"]
        details["type"] = failure.request.cb_kwargs["header"]["type"]
        details["tag"] = ["id.uptodown.com"]
        details["crawling_time"] = strftime('%Y-%m-%d %H:%M:%S')
        details["crawling_time_epoch"] = int(time())
        details["path_data_raw"] = ""
        details["path_data_clean"] = ""
        details["reviews_name"] = failure.request.cb_kwargs["header"]["title"]
        details["location_reviews"] = None
        details["category_reviews"] = "" # Bro?
        details["detail_application"] = {
            "title": failure.request.cb_kwargs["header"]["title"],
            "information": failure.request.cb_kwargs["header"]["information"],
            "platform": failure.request.cb_kwargs["header"]["platform"],
            "version": failure.request.cb_kwargs["header"]["version"],
            "author": failure.request.cb_kwargs["header"]["author"],
            "descriptions": failure.request.cb_kwargs["header"]["descriptions"],
            "technical-information": failure.request.cb_kwargs["header"]["technical-information"],
            "previous_version": failure.request.cb_kwargs["header"]["previous_version"]
        }
    
        if failure.request.cb_kwargs["reviews"]:
            for result in failure.request.cb_kwargs["reviews"]:
                items = UptodownItem()

                items["link"] = failure.request.cb_kwargs["header"]["url"]
                items["id"] = failure.request.cb_kwargs["header"]["id"]
                items["type"] = failure.request.cb_kwargs["header"]["type"]
                items["tag"] = ["id.uptodown.com"]
                items["crawling_time"] = strftime('%Y-%m-%d %H:%M:%S')
                items["crawling_time_epoch"] = int(time())
                items["path_data_raw"] = ""
                items["path_data_clean"] = ""
                items["reviews_name"] = failure.request.cb_kwargs["header"]["title"]
                items["location_reviews"] = None
                items["category_reviews"] = "" # Bro?
                items["total_reviews"] = failure.request.cb_kwargs["header"]["total_reviews"]
                items["reviews_rating"] = {
                    "total_rating": failure.request.cb_kwargs["header"]["ratings"],
                    "detail_total_rating": None
                }
                items["detail_reviews"] = {
                    "username_reviews": result["username"],
                    "image_reviews": result["avatar"],
                    "created_time": result["posted"],
                    "created_time_epoch": None,
                    "email_reviews": None,
                    "company_name": None,
                    "location_reviews": None,
                    "title_detail_reviews": None,
                    "rating_given": len(failure.request.cb_kwargs["reviews"]),
                    "reviews_rating": result["ratings"],
                    "detail_reviews_rating": None,
                    "total_likes_reviews": result["likes"],
                    "total_dislikes_reviews": None,
                    "total_reply_reviews": "", # Bro?
                    "content_reviews": result["comment"],
                    "reply_content_reviews": "",
                    "date_of_experience": result["posted"],
                    "date_of_experience_epoch": None
                }
                items["detail_application"] = {
                    "title": failure.request.cb_kwargs["header"]["title"],
                    "information": failure.request.cb_kwargs["header"]["information"],
                    "platform": failure.request.cb_kwargs["header"]["platform"],
                    "version": failure.request.cb_kwargs["header"]["version"],
                    "author": failure.request.cb_kwargs["header"]["author"],
                    "descriptions": failure.request.cb_kwargs["header"]["descriptions"],
                    "technical-information": failure.request.cb_kwargs["header"]["technical-information"],
                    "previous_version": failure.request.cb_kwargs["header"]["previous_version"]
                }


                yield items

                yield details

            else:
                yield details
