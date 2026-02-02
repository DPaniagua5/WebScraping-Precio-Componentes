import requests
from bs4 import BeautifulSoup
from supabase_client import supabase
import re
from datetime import date


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-GT,es;q=0.9",
}


class Shop3Scraper:
    def __init__(self, url: str):
        self.url = url
        self.today = date.today().isoformat()

    def fetch(self) -> BeautifulSoup:
        r = requests.get(self.url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    def parse_capacity(self, text: str) -> str | None:
        match = re.search(r'(\d{1,2})\s*GB', text, re.I)
        return match.group(1) + "GB" if match else None

    def parse_frequency(self, text: str) -> str | None:
        match = re.search(r"\b(\d{4})\s*(MHz|MT/s)\b", text, re.I)
        return match.group(1) + "MHz" if match else None

    def parse_price(self, text: str) -> int | None:
        if not text:
            return None
        clean = re.sub(r"[^\d]", "", text)
        return int(clean) if clean else None

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("h3")
        price_container = p.select_one('[data-component="Price"]')
        if price_container:
            integer_div = price_container.find("div")
            price_text = integer_div.get_text(strip=True)

        if not name_tag:
            return None

        product_name = name_tag.get_text(strip=True)

        capacity = self.parse_capacity(product_name)
        frequency = self.parse_frequency(product_name)
        price = int(re.sub(r"[^\d]", "", price_text))
        today = date.today().isoformat()


        # print("  Producto detectado:")
        # print("  Nombre:", product_name)
        # print("  Marca: ", product_name.split()[0])
        # print("  Capacidad:", capacity)
        # print("  Frecuencia:", frequency)
        # print("  Precio:", price)
        # print(f"\n")
        
        return {
            "store": "Kemik",
            "marca": product_name.split()[0],
            "product_name": product_name,
            "price_normal": price,
            "price_cash": price,
            "capacity": capacity,
            "frequency": frequency,
            "scraped_at": today
        }

    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select("a.group")

        rows = []

        for p in products:
            product = self.parse_product(p)
            if product:
                rows.append(product)

        return rows
    
    def save_to_supabase(self):
        try:
            rows = self.scrape()

            if not rows:
                print(" No hay datos para guardar")
                return

            print(" Enviando a Supabase...")
            res = supabase.table("ram_prices").upsert(rows).execute()

            print(f" Insertados/actualizados: {len(rows)}")
            
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False