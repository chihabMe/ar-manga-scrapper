from lekmanga.items import MangaImageItem
import scrapy

class MangasspiderSpider(scrapy.Spider):
    name = "mangasSpider"
    allowed_domains = ["lekmanga.net"]
    manga_name = "absolute-sword-sense"
    start_urls = [f"https://lekmanga.net/manga/{manga_name}/"]
    limit = 10

    def parse(self, response):
        pages = response.css("body > div.wrap > div > div > div > div.c-page-content.style-1 > div > div > div > div > div > div.c-page > div > div.page-content-listing.single-page > div > ul > li")
        pages = pages[:self.limit]
        #pages.reverse()
        for p in pages:
            link = p.css("a::attr(href)").get()
            if link:
                yield response.follow(link, callback=self.parse_details)

    def parse_details(self, response):
        images = response.css(".reading-content > div img::attr(src)").getall()
        
        # Create a MangaImageItem, not a raw dict
        yield MangaImageItem(
            image_urls=images,
            chapter=response.url.split("/")[-2],
            manga_name=self.manga_name

        )
