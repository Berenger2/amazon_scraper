import scrapy
from scrapy.crawler import CrawlerProcess
import json
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
            link = product.css("a::attr(href)").get()
            
            if link:
                link = f"https://www.amazon.fr{link}"

            price = None
            if price_whole and price_fraction:
                try:
                    price = float(f"{price_whole.replace(',', '')}.{price_fraction}")
                except ValueError:
                    price = None

            rating_value = None
            if rating:
                try:
                    rating_value = float(rating.split(" ")[0].replace(",", "."))
                except ValueError:
                    rating_value = None

            if name and price is not None and rating_value is not None:
                self.results.append({
                    "name": name.strip(),
                    "price": price,  
                    "rating": rating_value, 
                    "badge": badge.strip() if badge else None,
                    "link": link, 
                })

        # Pagination
        next_page = response.css("ul.a-pagination li.a-last a::attr(href)").get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def closed(self, reason):
        # Sauvegarde 
        with open(f"{self.name}_results.json", "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=4)

def run_spider(category):
    process = CrawlerProcess(settings={
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0",
        "LOG_LEVEL": "DEBUG",
    })

    process.crawl(AmazonSpider, category=category)
    process.start()

    # Affichage des résultats
    try:
        with open('amazon_results.json', 'r', encoding="utf-8") as f:
            results = json.load(f)

        if results:
            col1, col2 = st.columns(2)

            with col1:
                st.success("Scraping terminé ! Voici les résultats :")
                st.json(results)

                # btn de téléchargement
                with open("amazon_results.json", "r", encoding="utf-8") as file:
                    json_data = file.read()
                st.download_button(
                    label="Télécharger les résultats en JSON",
                    data=json_data,
                    file_name="amazon_results.json",
                    mime="application/json",
                )

            #  Affichage graphique
            with col2:
                st.subheader("Top 10 des produits les moins chers")

                # création du DataFrame
                df = pd.DataFrame(results)
                df['short_name'] = df['name'].apply(lambda x: x.split(',')[0] if ',' in x else x)

                ###### produits les moins chers ######
                cheapest = df.sort_values(by="price", ascending=True).head(10)

                # graphique
                fig1, ax1 = plt.subplots()
                ax1.barh(cheapest['short_name'], cheapest['price'], color='skyblue')
                ax1.set_xlabel("Prix (€)")
                ax1.set_ylabel("Produits")
                ax1.set_title("Top 10 des produits les moins chers")
                st.pyplot(fig1)

                ###### produits les plus chers ######
                st.subheader("Top 10 des produits les plus chers")
                most_expensive = df.sort_values(by="price", ascending=False).head(10)

                # graphique 
                fig2, ax2 = plt.subplots()
                ax2.barh(most_expensive['short_name'], most_expensive['price'], color='salmon')
                ax2.set_xlabel("Prix (€)")
                ax2.set_ylabel("Produits")
                ax2.set_title("Top 10 des produits les plus chers")
                st.pyplot(fig2)

                ###### produits les mieux notés ######
                st.subheader("Top 10 des produits les mieux notés")
                best_rated = df.sort_values(by="rating", ascending=False).head(10)

                # graphique
                fig3, ax3 = plt.subplots()
                ax3.barh(best_rated['short_name'], best_rated['rating'], color='lightgreen')
                ax3.set_xlabel("Note")
                ax3.set_ylabel("Produits")
                ax3.set_title("Top 10 des produits les mieux notés")
                st.pyplot(fig3)

                ###### produits les moins bien notés ######
                st.subheader("Top 10 des produits les moins bien notés")
                worst_rated = df.sort_values(by="rating", ascending=True).head(10)

                # graphique
                fig4, ax4 = plt.subplots()
                ax4.barh(worst_rated['short_name'], worst_rated['rating'], color='orange')
                ax4.set_xlabel("Note")
                ax4.set_ylabel("Produits")
                ax4.set_title("Top 10 des produits les moins bien notés")
                st.pyplot(fig4)

        else:
            st.warning("Aucun résultat trouvé. Essayez une autre catégorie.")
    except FileNotFoundError:
        st.warning("Le fichier des résultats n'a pas pu être trouvé. Essayez de relancer le scraping.")

# Interface Streamlit
st.title("Web Scraping || amazon.fr")

category_input = st.text_input("Entrez la catégorie à rechercher", "")
if st.button("Démarrer le scraping"):
    if category_input:
        st.write(f"Recherche dans la catégorie : {category_input}")
        run_spider(category_input)
    else:
        st.warning("Veuillez entrer une catégorie avant de lancer le scraping.")
