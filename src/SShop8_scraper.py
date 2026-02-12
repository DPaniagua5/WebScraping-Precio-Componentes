from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from supabase_client import supabase
import time
import re
from datetime import date


class ShopScraper:

    def __init__(self, url:str, headless=True):
        self.url = url
        self.productos = []
        self.headless = headless
        self.driver = None
        self.store = "Intelaf"

    def configure_driver(self):
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def wait_products(self, timeout=30):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "a.css-g5oay9, a[href*='/precios_stock_detallado/']")
            )
        )

        time.sleep(2)

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0

        while scroll_attempts < 5:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0

            last_height = new_height

        self.driver.execute_script("window.scrollTo(0, 0);")

    def extract_price(self, text):
        if not text:
            return None
        match = re.search(r"Q\s*([\d,]+)", text)
        if match:
            return int(match.group(1).replace(",", ""))
        return None

    def extract_capacity(self, text):
        match = re.search(r"(\d+(?:\.\d+)?)\s*(TB|GB|G)", text, re.I)
        if not match:
            return None

        value = float(match.group(1))
        unit = match.group(2).upper()

        if unit == "TB":
            return f"{int(value * 1000)}GB"
        return f"{int(value)}GB"

    def es_disk(self, texto: str):
        palabras_clave = [
            "tb","gb","ssd","nvme","m.2",
            "unidad de estado solido","estado solido","estado sólido"
        ]
        texto_min = texto.lower()
        return any(clave in texto_min for clave in palabras_clave)

    def es_externo(self, texto: str):
        palabras_excluir = [
            "ddr4","ram","ddr5","hot swap","hot-swap",
            "externo","adaptador","videovigilancia","surveillance",
            "sd","usb","nas","enterprise","servidor","hdd"
        ]

        texto_min = texto.lower()
        for palabra in palabras_excluir:
            if re.search(rf"\b{re.escape(palabra)}\b", texto_min):
                return True
        return False

    def parse_brand(self, texto: str):
        marcas_conocidas = [
            "Kingston","Samsung","HP","Hikvision","Dahua","Sandisk",
            "Adata","MSI","Dell","Patriot","Mushkin",
            "Western Digital","Hiksemi","XPG","Lexar",
            "Kioxia","Crucial","Transcend","Seagate"
        ]

        texto_upper = texto.upper()
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return "Kingston"

    def parse_type(self, text: str):
        text = text.lower()
        if "m.2" in text:
            return "M.2"
        if re.search(r"nvme|gen\s*[345]", text):
            return "NVMe"
        if any(clave in text for clave in ["estado solido", "ssd", "sata"]):
            return "SATA"
        if "hdd" in text or "duro" in text:
            return "HDD"
        return "SATA"

    def parse_product(self, element):
        try:
            today = date.today().isoformat()

            try:
                product_name = element.find_element(By.CSS_SELECTOR, "span.css-5xrf24").text.strip()
            except:
                product_name = element.text.split("\n")[0]

            if not self.es_disk(product_name):
                return None

            if self.es_externo(product_name):
                return None

            try:
                normal_elem = element.find_element(
                    By.XPATH, ".//span[contains(text(),'Precio normal')]/.."
                )
                price_normal = self.extract_price(normal_elem.text)
            except:
                price_normal = None

            try:
                efectivo_elem = element.find_element(By.CSS_SELECTOR, "span.css-15acwd8")
                price_cash = self.extract_price(efectivo_elem.text)
            except:
                price_cash = price_normal

            if price_cash is None:
                price_cash = 0
            if price_normal is None:
                price_normal = 0

            href = element.get_attribute("href")
            if href and href.startswith("http"):
                url = href
            else:
                url = f"https://www.intelaf.com{href}"

            title_stock = element.get_attribute("title")
            available = not (title_stock and "No hay existencias" in title_stock)

            capacity = self.extract_capacity(product_name)
            tipo = self.parse_type(product_name)
            brand = self.parse_brand(product_name)

            # print("Producto válido:", product_name)

            return {
                "store": self.store,
                "marca": brand,
                "product_name": product_name,
                "capacity": capacity,
                "type": tipo,
                "price_cash": price_cash,
                "price_normal": price_normal,
                "scraped_at": today,
                "available": available,
                "url": url,
            }

        except Exception as e:
            print("Error procesando producto:", e)
            return None

    def deduplicate_rows(self, rows: list[dict]) -> list[dict]:
        unique = {}
        for row in rows:
            key = (
                row["store"],
                row["product_name"],
                row["scraped_at"],
            )
            unique[key] = row
        return list(unique.values())

    def save_to_supabase(self, rows: list[dict]):
        if not rows:
            print("No hay datos para guardar")
            return

        rows = self.deduplicate_rows(rows)

        supabase.table("ssd_prices").upsert(
            rows,
            on_conflict="store,product_name,scraped_at"
        ).execute()

        print("\n" + "=" * 70)
        print(f"*** Insertados {len(rows)} datos SSD de {self.store}. ***")
        print("=" * 70)

    def scrape(self):
        try:
            self.configure_driver()
            self.driver.get(self.url)
            self.wait_products()

            elementos = self.driver.find_elements(By.CSS_SELECTOR, "a.css-g5oay9")

            for element in elementos:
                product = self.parse_product(element)
                if product:
                    self.productos.append(product)

            if self.productos:
                self.save_to_supabase(self.productos)
            return self.productos

        finally:
            if self.driver:
                self.driver.quit()
