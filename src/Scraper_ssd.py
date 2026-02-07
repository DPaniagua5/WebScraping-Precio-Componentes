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


class ShopScraper:
    def __init__(self, url:str, store:str, tag_padre:str, tag_producto: str, tag_price:str, tipo_price:str, tag_price_cash:str, tipo_price_cash:str):
        self.url = url
        self.store = store
        self.tag_padre = tag_padre
        self.tag_producto = tag_producto
        self.tag_price = tag_price
        self.tag_price_cash = tag_price_cash
        self.tipo_price = tipo_price
        self.tipo_price_cash = tipo_price_cash
        self.today = date.today().isoformat()
    
    def fetch(self) -> BeautifulSoup:
        r = requests.get(self.url, headers = HEADERS, timeout = 20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    
    def parse_capacity(self, text: str) -> str | None:
        matchgb = re.search(r'(\d{1,3})\s*GB', text, re.I)
        matchtb = re.search(r'(\d{1,2})\s*TB', text, re.I)
        if matchtb:
            valor_tb = int(matchtb.group(1))
            return f"{valor_tb * 1000}GB"
        if matchgb:
            return f"{matchgb.group(1)}GB"
        return None

    def parse_price(self, text: str) -> int | None:
        if not text:
            return None
        text = str(text)
        match = re.search(r'([\d,]+)(?:\.\d+)?', text)
        if not match:
            return None

        number = match.group(1).replace(",", "")
        return int(number)

    def es_disk(self, texto: str):
        palabras_clave = ["nvme","unidad de estado solido","estado solido","ssd", "m.2", "nv3"]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_clave)
    
    def es_externo(self, texto:str):
        palabras_excluir = ["externo"]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_excluir)

    def parse_brand(self, texto:str):
        marcas_conocidas = ["Kingston"]
        texto_upper = texto.upper()
        
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return "Kingston"
    

    def parse_type(self, text: str) -> str:
        text = text.lower()   
        if re.search(r'nvme|nv3|gen\s*[345]', text):
            return "NVMe" 
        if "m.2" in text:
            return "M.2"
        if any(clave in text for clave in ["estado solido", "ssd", "sata"]):
            return "SATA"
        if "hdd" in text or "duro" in text:
            return "HDD"
        
        return "SATA"

    def def_available(self, p):
        contenedor_disponibilidad = p.select_one("div.disponible")
        if contenedor_disponibilidad:
            return False
        else:
            return True

    def extraer_precios(self, p):
        precio_normal = None
        precio_efectivo = None
        contenedor_efectivo = p.select_one(f"{self.tipo_price}.{self.tag_price}")
        contenedor_precio = p.select_one(f"{self.tipo_price_cash}.{self.tag_price_cash}")
        
        if contenedor_precio:
            oferta = contenedor_precio.find("ins")
            if oferta:
                precio_normal = oferta.get_text(strip=True)
            else:
                precio_normal = contenedor_precio.get_text(strip=True)
        if contenedor_efectivo:
            precio_efectivo = contenedor_efectivo.get_text(strip=True)
        else:
            precio_efectivo = precio_normal

        return precio_normal, precio_efectivo

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one(self.tag_producto)
        
        if not name_tag:
            return None

        product_name = name_tag.get_text(strip=True)
        url_tag = name_tag.find('a')
        
        if url_tag:
            url = url_tag.get('href')
        
        if(self.es_disk(product_name) and not(self.es_externo(product_name))):

            capacity = self.parse_capacity(product_name)
            today = date.today().isoformat()
            brand = self.parse_brand(product_name)
            tipo = self.parse_type(product_name)
            price_normal, price = self.extraer_precios(p)
            price = self.parse_price(price)
            price_normal = self.parse_price(price_normal)
            available = self.def_available(p)

            if price == None:
                price = 0
            if price_normal == None:
                price_normal = 0    
            # print("  Producto detectado:")
            # print("  Nombre: ", product_name)
            # print("  Marca: ", brand),
            # print("  Capacidad:", capacity)
            # print("  Tipo: ", tipo)
            # print("  Precio efectivo:", price)
            # print("  Precio normal: ",  price_normal)
            # print("  Url: ", url)
            # print("  Disponible: ", available)
            # print(f"\n")
            
            return {
                "store": self.store,
                "marca": brand,
                "product_name": product_name,
                "capacity":capacity,
                "type":tipo,
                "price_cash": price_normal,
                "price_normal": price,
                "capacity": capacity,
                "scraped_at": today,
                "available": available,
                "url": url
            }

    def scrape(self) -> list[dict]:
        soup = self.fetch()
        products = soup.select(self.tag_padre)
        rows = []
        for p in products:
            product = self.parse_product(p)
            if product:
                rows.append(product)

        return rows
    
    def deduplicate_rows(self, rows: list[dict]) -> list[dict]:
        unique = {}

        for row in rows:
            key = (
                row["store"],
                row["product_name"],
                row["scraped_at"]
            )
            unique[key] = row  # si se repite, se queda el último

        return list(unique.values())


    def save_to_supabase(self, rows: list[dict]):
        if not rows:
            return

        rows = self.deduplicate_rows(rows)

        response = (
            supabase
            .table("ssd_prices")
            .upsert(
                rows,
                on_conflict="store,product_name,scraped_at"
            )
            .execute()
        )
        print("\n" + "=" * 70)
        print(f"***    Insertados {len(rows)} datos de tienda {self.store}.    ***")
        print("\n" + "=" * 70)