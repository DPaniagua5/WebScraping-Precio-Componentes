import requests
from bs4 import BeautifulSoup
from supabase_client import supabase
import re
from datetime import date

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-GT,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

class Shop5Scraper:
    def __init__(self, url:str):
        self.url = url
        self.today = date.today().isoformat()
    
    def fetch(self) -> BeautifulSoup:
        r = requests.get(self.url, headers = HEADERS, timeout = 20)
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
        
        match = re.search(r'([\d,]+)(?:\.\d+)?', text)
        if not match:
            return None

        number = match.group(1).replace(",", "")
        return int(number)
    
    def es_notebook(self, *texts: str) -> bool:
        full = " ".join(t for t in texts if t).lower()
        return any(k in full for k in ["notebook", "laptop", "sodimm", "dram"])

    
    def is_ram_product(self, text: str) -> bool:
        RAM_KEYWORDS = ["ram", "memoria", "ddr4", "ddr5", "sodimm", "dram"]
        EXCLUDE = ["ssd", "disco", "cargador", "charger", "mouse", "teclado"]

        t = text.lower()

        if not any(k in t for k in RAM_KEYWORDS):
            return False
        if any(k in t for k in EXCLUDE):
            return False

        return True

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("h4 a")
        price_container = p.select_one("span.price-new")
        desc_tag = p.select_one("div.description")
        
        url = name_tag.get("href")
        if url and not url.startswith('http'):
            url = "https://www.pacifiko.com" + url

        if not name_tag or not price_container:
            return None

        product_name = name_tag.get_text(strip=True)
        description = desc_tag.get_text(" ", strip=True) if desc_tag else ""
        price_text = price_container.get_text(strip=True)

        full_text = f"{product_name} {description}"

        if not self.is_ram_product(full_text):
            return None

        if not self.es_notebook(product_name, description):
            return None

        capacity = self.parse_capacity(full_text)
        frequency = self.parse_frequency(full_text)
        price = self.parse_price(price_text)

        # print("  Producto detectado:")
        # print("  Nombre:", product_name)
        # print("  Marca:", product_name.split()[0])
        # print("  Capacidad:", capacity)
        # print("  Frecuencia:", frequency)
        # print("  Precio:", price)
        # print("  Url: ", url)
        # print("\n")

        return {
            "store": "Pacifiko",
            "marca": product_name.split()[0],
            "product_name": product_name,
            "price_normal": price,
            "price_cash": price,
            "capacity": capacity,
            "frequency": frequency,
            "scraped_at": self.today,
            "available": True,
            "url": url
        }


    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select("div.product-item-container")

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

            res = supabase.table("ram_prices").upsert(rows).execute()

            print(f"***    Insertados {len(rows)} datos de tienda 5.    ***")
            print("\n" + "=" * 70)

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False