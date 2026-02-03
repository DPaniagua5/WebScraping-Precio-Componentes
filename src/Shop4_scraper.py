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


class Shop4Scraper:
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
        return match.group(1) + "MHz" if match else "3200MHz"

    def parse_ddr(self, text: str) -> str | None:
        match = re.search(r"\bDDR\s*([3-5])\b", text, re.I)
        return f"DDR{match.group(1)}" if match else None

    def parse_price(self, text: str) -> int | None:
        if not text:
            return None
        
        match = re.search(r'([\d,]+)(?:\.\d+)?', text)
        if not match:
            return None

        number = match.group(1).replace(",", "")
        return int(number)

    
    def is_ram_product(self, name: str) -> bool:
        RAM_KEYWORDS = [
        "ram", "memoria", "ddr4", "ddr5", "sodimm", "udimm", "ddr3"
        ]

        EXCLUDE_KEYWORDS = [
            "cargador", "charger", "game", "juego", "ps5",
            "mouse", "teclado", "adaptador"
        ]
        name = name.lower()

        if not any(k in name for k in RAM_KEYWORDS):
            return False

        if any(k in name for k in EXCLUDE_KEYWORDS):
            return False

        return True

    def es_notebook(self, texto: str):
        palabras_clave = ["notebook", "laptop"]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_clave)
    
    def parse_brand(self, text: str) -> str:
        return re.sub(r"[^\w]", "", text.split()[0])


    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("h2.woocommerce-loop-product__title")
        price_normal_container = p.select_one("span.price span.woocommerce-Price-amount")
        price_container = p.select_one("div.footerCardItemProduct div.precio-efectivo")     

        price_normal = self.parse_price(price_normal_container.get_text(strip=True))
        price = self.parse_price(price_container.get_text(strip=True))

        if not name_tag:
            return None

        product_name = name_tag.get_text(strip=True)

        if not self.is_ram_product(product_name):
            return None
        
        ddr = self.parse_ddr(product_name)
        if(self.es_notebook(product_name) and ddr == "DDR4"):

            capacity = self.parse_capacity(product_name)
            frequency = self.parse_frequency(product_name)
            today = date.today().isoformat()
            brand = self.parse_brand(product_name)
            # print("  Producto detectado:")
            # print("  Nombre: ", product_name)
            # print("  Marca: ", brand),
            # print("  Capacidad:", capacity)
            # print("  Frecuencia:", frequency)
            # print("  Precio efectivo:", price)
            # print("  Precio normal: ", price_normal)
            # print(f"\n")
            
            return {
                "store": "MacrosSistemas",
                "marca": brand,
                "product_name": product_name,
                "price_normal": price_normal,
                "price_cash": price,
                "capacity": capacity,
                "frequency": frequency,
                "scraped_at": today
            }

    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select("div.av-product-class-")

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

            print(f"***    Insertados {len(rows)} datos de tienda 4.    ***")
            print("\n" + "=" * 70)

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False