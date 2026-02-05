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


class Shop9Scraper:
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

    def es_notebook(self, texto: str):
        palabras_clave = ["notebook", "laptop", "sodimm", "so-dimm"]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_clave)
    
    def parse_brand(self, texto:str):
        marcas_conocidas = ["XPG", "Kingston", "Corsair", "Crucial", "Samsung", "ADATA", "Hiksemi", "Mushkin", "DELL", "kingspec", "PNY", "KVR"]
        texto_upper = texto.upper()
        
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return None
    def extraer_precios(self, soup_item):
        precio_normal = None
        precio_efectivo = None
        contenedor_precio = soup_item.find("span", class_="price")
        
        if contenedor_precio:
            oferta = contenedor_precio.find("ins")
            if oferta:
                precio_normal = oferta.get_text(strip=True)
            else:
                precio_normal = contenedor_precio.get_text(strip=True).split(' ')[0]

        div_efectivo = soup_item.find("div", class_="beneficio-efectivo-catalogo")
        if div_efectivo:
            texto_efectivo = div_efectivo.get_text(strip=True)
            if "Q" in texto_efectivo:
                precio_efectivo = "Q" + texto_efectivo.split("Q")[-1].strip()
        else:
            precio_efectivo = precio_normal

        return precio_normal, precio_efectivo

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("h3.wd-entities-title")
        stock_container = p.select_one("p.wd-product-stock")
        
        stock_text = stock_container.get_text(strip=True)
        if not name_tag:
            return None

        product_name = name_tag.get_text(strip=True)
        url_tag = name_tag.find('a')
        
        if url_tag:
            url = url_tag.get('href')
        
        
        
        if stock_container:
            if stock_text != "Out of stock":
                available = True
            else:
                available = False
            
        ddr = self.parse_ddr(product_name)
        if(self.es_notebook(product_name) and ddr == "DDR4"):

            capacity = self.parse_capacity(product_name)
            frequency = self.parse_frequency(product_name)
            today = date.today().isoformat()
            brand = self.parse_brand(product_name)

            price, price_normal = self.extraer_precios(p)
            price = self.parse_price(price)
            price_normal = self.parse_price(price_normal)
            # print("  Producto detectado:")
            # print("  Nombre: ", product_name)
            # print("  Marca: ", brand),
            # print("  Capacidad:", capacity)
            # print("  Frecuencia:", frequency)
            # print("  Precio efectivo:", self.parse_price(price))
            # print("  Precio normal: ", self.parse_price(price_normal)       )
            # print("  Disponible: ", available)
            # print("  Url: ", url)
            # print(f"\n")
            
            return {
                "store": "Tera",
                "marca": brand,
                "product_name": product_name,
                "price_normal": price_normal,
                "price_cash": price,
                "capacity": capacity,
                "frequency": frequency,
                "scraped_at": today,
                "available": available,
                "url": url
            }

    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select("div.product-element-bottom")

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