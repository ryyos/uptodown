import scrapy

from typing import Any, List, Optional
from icecream import ic
from pprint import pprint
from time import strftime, time, sleep
from twisted.python.failure import Failure

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.http import Response
from scrapy.http import Request
from scrapy.selector import Selector

from uptodown.items import UptodownItem
from uptodown.items import DetailItem
from uptodown.utils import Logs
from uptodown.utils import logger

from scrapy.spiders import Spider

class ServiceSpider(Spider):
    name = "service"
    start_urls = ["https://id.uptodown.com"]
  
  # kode spider selanjutnya
    
    _platforms = ['andorid', 'windows', 'mac']

    def spider_opened(self, spider):
      self.crawler.signals.connect(self.__finally, signal=signals.spider_error)

    def parse(self, response: Response):
        url_platforms = response.css('#platform-item > a ::attr(href)').getall()

        self.items = UptodownItem()

        for url in url_platforms:
            ic("URLLL TYPEEEEE" + url)
            yield Request(url=url, callback=self.__collect_types)

        ...

    def __collect_types(self, response: Response) -> List[str]:
        
        for type in response.css('#main-left-panel-ul-id > div:nth-child(3) div[class="li"] > a ::attr(href)').getall():
            
            yield Request(url=type, callback=self.__collect_apps, cb_kwargs=dict(type=type))
        ...
    
    
    def __collect_apps(self, response: Response, type) -> List[str]:
        for index, app in enumerate(response.css('div[class="name"] > a ::attr(href)').getall()):
            pprint({
                "url_type": response.url,
                "total_apps": len(response.css('div[class="name"] > a ::attr(href)')),
                "app to": index
            })
            yield Request(url=app, callback=self.__parser_app, cb_kwargs=dict(type=type))
        ...


    def __extract_url(self, url: str) -> dict:
        pieces = url.split('/')
        return {
            "platform": pieces.pop(),
            "url": '/'.join(pieces)
        }
        ...
    

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

        yield Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments', 
                      callback=self.__extract_review, 
                      cb_kwargs={
                          "header": header
                          })

    def __extract_review(self, response: Response, header) -> List[dict]:
        reviews = Selector(text=response.json()['content'])

        offset = 10
        total_reviews = 0

        reviews_temp: List[dict] = []
        review_have_reply: List[dict] = []

        for review in reviews.css('div.comment'):
            temp = {
                "id": int(review.css('span.user ::attr(id)').get()),
                "username": self.__strip(review.css('span.user ::text').get()),
                "avatar": review.css('img')[0].attrib['src'],
                "posted": self.__strip(review.css('span:nth-child(3) ::text').get()),
                "ratings": len(review.css('img.active')),
                "likes": review.css('div[name="favs-icon"] span::text').get() if not "Like" else None,
                "comment": review.css('p ::text').get(),
                "reply":  review.css('div[name="response-icon"] span ::text').get() if not "Balas" else None,
                "reply_content": []
            }

            total_reviews+=1
            # temp.update

            if temp["reply"]:
                review_have_reply.append(temp)
            else:
                reviews_temp.append(temp)


        if review_have_reply:
            ic("extract api")
            ic(len(review_have_reply))
            errback = self.__extract_reply
        else:
            ic("terminal")
            errback = self.__finally
            
        request = Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments/unixtime?offset={offset}', 
                          callback=self.__exctract_review_api,
                          errback=errback,
                          cb_kwargs={
                              "header": header,
                              "reviews": reviews_temp,
                              "review_have_reply": review_have_reply,
                              "total_reviews": total_reviews
                          })

        yield request
        ...

    def __exctract_review_api(self, response: Response, header, reviews, review_have_reply, total_reviews, offset=20):
        reviews_temp = response.json()

        logger.info({
            "len reviws": len(reviews),
            "link": header["url"]
        })

        if reviews_temp["success"]:

            for review in reviews_temp["data"]:
                temp = {
                    "id": review["id"],
                    "username": review["userName"],
                    "avatar": review["icon"],
                    "posted": review["timeAgo"],
                    "ratings": review["rating"],
                    "likes": review["likes"],
                    "comment": review["text"],
                    "reply": review["totalAnswers"],
                    "reply_content": []
                }

                total_reviews+=1

                if temp["reply"]:
                    review_have_reply.append(temp)

                else:
                    reviews.append(temp)
                ...

            if review_have_reply:
                ic("extract api")
                ic(len(review_have_reply))
                errback = self.__extract_reply
            else:
                ic("terminal")
                errback = self.__finally

            request = Request(url=f'{header["url"]}/mng/v2/app/{header["id"]}/comments/unixtime?offset={offset}', 
                              callback=self.__exctract_review_api, 
                              errback=errback,
                              cb_kwargs={
                                  "header": header,
                                  "reviews": reviews,
                                  "offset": offset,
                                  "review_have_reply": review_have_reply,
                                  "total_reviews": total_reviews
                                  })

            offset +=10
            yield request
        ...

    def __extract_reply(self, failure: Failure):
        data = {
            "header": failure.request.cb_kwargs["header"],
            "reviews": failure.request.cb_kwargs["reviews"],
            "total_reviews": failure.request.cb_kwargs["total_reviews"],
            "review_have_reply": failure.request.cb_kwargs["review_have_reply"]
        }

        url = f'{failure.request.cb_kwargs["header"]["url"]}/v2/comment/{data["review_have_reply"][-1]["id"]}'

        ic(url)

        yield Request(url=url, 
                      callback=self.__collection, 
                      cb_kwargs={
                        "header": failure.request.cb_kwargs["header"],
                        "reviews": failure.request.cb_kwargs["reviews"],
                        "total_reviews": failure.request.cb_kwargs["total_reviews"]+1,
                        "review_have_reply": data["review_have_reply"],
                        })

        ...

    def __collection(self, response, header, reviews, total_reviews, review_have_reply):
        replies = Selector(text=response.json()['content'])
        review_update = review_have_reply.pop()

        ic(review_update)
        for reply in replies.css('div[class="comment answer"]'):
            review_update["reply_content"].append({
                "username_reply_reviews": reply.css('a.user ::text').get(),
                "content_reviews": reply.css('div > p ::text').get()
            })
            total_reviews+=1
            reviews.append(review_update)

        # if not review_have_reply: review_have_reply.append({"id": 0}):
        if not review_have_reply: 
            yield Request(url=' https://emoji-keyboard-color.id.uptodown.com/mng/v2/pp/303/comments',callback=self.__collection, errback=self.__finally, cb_kwargs={
                          "header": header,
                          "reviews": reviews,
                          "total_reviews": total_reviews,
                          "review_have_reply": review_have_reply,
                      })
        
        else:
            yield Request(url=f'{header["url"]}/v2/comment/{review_have_reply[-1]["id"]}',
                          callback=self.__collection,
                          errback=self.__finally,
                          cb_kwargs={
                              "header": header,
                              "reviews": reviews,
                              "total_reviews": total_reviews,
                              "review_have_reply": review_have_reply,
                          })

        ...

    def __finally(self, failure: Failure):
        ic("==============masuk finalyyy==============")
        """
        {
          "header": header,
          "reviews": reviews,
          "total_reviews": total_reviews,
        }
        """

        logger.info({
            "total finaly": failure.request.cb_kwargs["total_reviews"],
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
        details["category_reviews"] = "application"
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

        try:
            if failure.request.cb_kwargs["total_reviews"] == int(failure.request.cb_kwargs["header"]["total_reviews"].split(' ')[0]):
                ... # jika semua review berhasil di ambil
                Logs.succes(status='Done',
                            failed=0,
                            total=int(failure.request.cb_kwargs["header"]["total_reviews"].split(' ')[0]),
                            success=failure.request.cb_kwargs["total_reviews"],
                            id=int(failure.request.cb_kwargs["header"]["id"]),
                            source='id.uptodown.com')
            else:
                ... # jika ada request review tidak berhasil
                Logs.error(status="Comment Not Found",
                           total= int(failure.request.cb_kwargs["header"]["total_reviews"].split(' ')[0]),
                           success=failure.request.cb_kwargs["total_reviews"],
                           failed= int(failure.request.cb_kwargs["header"]["total_reviews"].split(' ')[0]) - len(failure.request.cb_kwargs["reviews"]),
                           id=int(failure.request.cb_kwargs["header"]["id"]),
                           source='id.uptodown.com',
                           message="failure.getErrorMessage()")
        except Exception:
            ... # jika tidak ada review
            Logs.succes(status='Done',
                        failed=0,
                        total=len(failure.request.cb_kwargs["reviews"]),
                        success=failure.request.cb_kwargs["total_reviews"],
                        id=int(failure.request.cb_kwargs["header"]["id"]),
                        source='id.uptodown.com')
            
    
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
                items["category_reviews"] = "application"
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
                    "reviews_rating": result["ratings"],
                    "detail_reviews_rating": None,
                    "total_likes_reviews": result["likes"],
                    "total_dislikes_reviews": None,
                    "total_reply_reviews": "", # Bro?
                    "content_reviews": result["comment"],
                    "reply_content_reviews": result["reply_content"],
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

