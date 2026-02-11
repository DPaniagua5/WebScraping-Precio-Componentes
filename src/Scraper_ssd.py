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
    def __init__(self, url:str, store:str, tag_padre:str, tag_producto: str, tag_price:str, tipo_price:str, tag_price_cash:str, tipo_price_cash:str, dominio:str, available_tag:str):
        self.url = url
        self.store = store
        self.tag_padre = tag_padre
        self.tag_producto = tag_producto
        self.tag_price = tag_price
        self.tag_price_cash = tag_price_cash
        self.tipo_price = tipo_price
        self.tipo_price_cash = tipo_price_cash
        self.dominio = dominio
        self.available_tag = available_tag
        self.today = date.today().isoformat()
    
    def fetch(self) -> BeautifulSoup:
        r = requests.get(self.url, headers = HEADERS, timeout = 150)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    
    def parse_capacity(self, text: str) -> str | None:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(TB|GB|G)', text, re.I)
        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2).upper()

        if unit == "TB":
            return f"{int(value * 1000)}GB"

        return f"{int(value)}GB"

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
        palabras_clave = ["tb","gb","ssd","nvme","m.2","nv3","unidad de estado solido","estado solido","unidad de estado sólido","estado sólido"]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_clave)
    
    def es_externo(self, texto:str):
        palabras_excluir = [
            "ddr4","ram","ddr5","wd","512e","hot swap","hot-swap",
            "externo","adaptador","videovigilancia","surveillance","sd"
            "portátil","enterprise","servidor","servidores",
            "hdd","portable","video","externa","vigilancia","usb",
            "firmware","nas"
        ]

        texto_min = texto.lower()

        for palabra in palabras_excluir:
            if re.search(rf'\b{re.escape(palabra)}\b', texto_min):
                return True

        return False


    def parse_brand(self, texto:str):
        marcas_conocidas = ["Kingston","samsung","hp","hikvision","brocs","dahua","sandisk","adata","msi","dell","patriot","mushkin","western digital","hiksimi","hiksemi","startech.com","xpg","lexar","kioxia","crucial","transcend","seagate","quimera"]
        texto_upper = texto.upper()
        
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return "Kingston"
    

    def parse_type(self, text: str) -> str:
        text = text.lower()   
        if "m.2" in text:
            return "M.2"
        if re.search(r'nvme|nv3|gen\s*[345]', text):
            return "NVMe"
        if any(clave in text for clave in ["estado solido", "ssd", "sata"]):
            return "SATA"
        if "hdd" in text or "duro" in text:
            return "HDD"
        
        return "SATA"

    def def_available(self, p):
        available_container = p.select_one(f"{self.available_tag}")
        if available_container != None:
            if not(self.available_tag == ""):
                available_ = p.select_one(f'{self.available_tag}') 
                available_text = available_.get_text(strip=True)
                if available_text == "Agotado" or available_text == "cartshop-whiteLeer más" or available_text == "Out of stock":
                    return False
                else:
                    return True
            else:
                return True
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
        url_tag_option = p.get('href')
        url_tag_option1 = p.select_one('a')

        if url_tag:
            url = url_tag.get('href')
        elif url_tag_option:
            url = url_tag_option
        elif url_tag_option1:
            url = url_tag_option1.get('href')
        else:
            url = ""

        if not(url.startswith(self.dominio)):
            url = self.dominio + url
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
        
        # print(f"***    Encontrados {len(rows)} datos de tienda {self.store}.    ***")

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