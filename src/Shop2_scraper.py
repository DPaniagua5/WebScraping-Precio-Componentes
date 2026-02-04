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


class Shop2Scraper:
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

    
    def obtener_marca(self, texto:str):
        marcas_conocidas = ["XPG", "Kingston", "Corsair", "Crucial", "Samsung", "ADATA", "Hiksemi"]
        texto_upper = texto.upper()
        
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return None

    def es_notebook(self, texto: str):
        return "notebook" in texto.lower()

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("h2.product-title")
        price_normal_container = p.select_one('span.product-price-normal')
        price_container = p.select_one("span.product-price:not(.product-price-normal)")     

        price_text_normal = price_normal_container.get_text(strip=True)    
        price_text = price_container.get_text(strip=True)

        if not name_tag:
            return None

        product_name = name_tag.get_text(strip=True)
        if(self.es_notebook(product_name)):

            capacity = self.parse_capacity(product_name)
            frequency = self.parse_frequency(product_name)
            price = self.parse_price(price_text)
            price_normal = self.parse_price(price_text_normal)
            today = date.today().isoformat()

            # print("  Producto detectado:")
            # print("  Nombre:", product_name)
            # print("  Marca: ", self.obtener_marca(product_name))
            # print("  Capacidad:", capacity)
            # print("  Frecuencia:", frequency)
            # print("  Precio efectivo:", price)
            # print("  Precio normal: ", price_normal)
            # print(f"\n")
            
            return {
                "store": "Rech",
                "marca": self.obtener_marca(product_name),
                "product_name": product_name,
                "price_normal": price,
                "price_cash": price,
                "capacity": capacity,
                "frequency": frequency,
                "scraped_at": today,
                "available": True
            }

    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select("div.product-details")

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

            print(f"***    Insertados {len(rows)} datos de tienda 2.    ***")
            print("\n" + "=" * 70)

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False