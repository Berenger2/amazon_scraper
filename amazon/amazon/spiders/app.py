import scrapy
from scrapy.crawler import CrawlerProcess
import json

class AmazonSpider(scrapy.Spider):
    name = "amazon"

    def __init__(self, category='', *args, **kwargs):
        super(AmazonSpider, self).__init__(*args, **kwargs)
        if not category:
            raise ValueError("Veuillez fournir une catégorie avec -a category=<votre_categorie>.")
        self.start_urls = [f"https://www.amazon.fr/s?k={category}"]
        self.results = []

    def parse(self, response):
        for product in response.css("div.s-main-slot div.s-result-item"):
            name = product.css("h2.a-size-base-plus span::text").get()
            price_whole = product.css("span.a-price-whole::text").get()
            price_fraction = product.css("span.a-price-fraction::text").get()
            rating = product.css("span.a-icon-alt::text").get()
            badge = product.css("span.a-badge-text::text").get()

            price = None
            if price_whole and price_fraction:
                price = f"{price_whole}.{price_fraction}"

            if name and price and rating:
                self.results.append({
                    "name": name.strip(),
                    "price": price.strip(),
                    "rating": rating.split(" ")[0],
                    "badge": badge.strip() if badge else None,
                })

        # Pagination
        next_page = response.css("ul.a-pagination li.a-last a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def closed(self, reason):
        # Sauvegarde 
        with open(f"{self.name}_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)

# spider
if __name__ == "__main__":
    category = input("Entrez la catégorie que vous voulez scraper : ")

    process = CrawlerProcess(settings={
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "LOG_LEVEL": "INFO",
    })

    process.crawl(AmazonSpider, category=category)
    process.start()