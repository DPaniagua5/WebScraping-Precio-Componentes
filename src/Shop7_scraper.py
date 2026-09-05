from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from supabase_client import supabase
import time
import re
from datetime import date


class Shop7Scraper:
    def __init__(self, url: str, headless: bool = True):
        self.url = url
        self.today = date.today().isoformat()
        self.headless = headless
        self.driver = None

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
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def wait_bypass_verification(self, timeout=20):
        """
        Espera a que la página de verificación (bxVerify) redirija
        automáticamente a la página real de productos.
        """
        wait = WebDriverWait(self.driver, timeout)

        # Si seguimos en bxVerify.html, esperamos a que la URL cambie
        if "bxVerify" in self.driver.current_url:
            print("  [INFO] Verificación anti-bot detectada, esperando redirección...")
            wait.until(lambda d: "bxVerify" not in d.current_url)
            time.sleep(2)  # margen extra para que cargue el contenido real

    def wait_products(self, timeout=30):
        wait = WebDriverWait(self.driver, timeout)
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.box-text-products"))
        )
        time.sleep(1)

    def parse_capacity(self, text: str) -> str | None:
        match = re.search(r'(\d{1,2})\s*GB', text, re.I)
        return match.group(1) + "GB" if match else None

    def parse_price(self, text: str) -> int | None:
        if not text:
            return None
        match = re.search(r'([\d,]+)(?:\.\d+)?', text)
        if not match:
            return None
        number = match.group(1).replace(",", "")
        return int(number)

    def obtener_marca(self, texto: str):
        marcas_conocidas = ["XPG", "Kingston", "Corsair", "Crucial", "Samsung", "ADATA", "Hiksemi", "Mushkin"]
        texto_upper = texto.upper()
        for marca in marcas_conocidas:
            if marca.upper() in texto_upper:
                return marca
        return None

    def es_notebook(self, *texts: str) -> bool:
        full = " ".join(t for t in texts if t).lower()
        return any(k in full for k in ["sodimm", "so-dimm", "notebook", "laptop"])

    def parse_frequency(self, text: str) -> str | None:
        match = re.search(r"\b(\d{4})\s*(MHz|MT/s)\b", text, re.I)
        return match.group(1) + "MHz" if match else "3200MHz"

    def parse_ddr(self, text: str) -> str | None:
        match = re.search(r"\bDDR\s*([3-5])\b", text, re.I)
        if match:
            return f"DDR{match.group(1)}"
        # Fallback por frecuencia si no dice "DDR" explícitamente
        freq_match = re.search(r"\b(\d{4})\b", text)
        if freq_match:
            freq = int(freq_match.group(1))
            if freq in (2133, 2400, 2666, 2933, 3200, 3600):
                return "DDR4"
            if freq in (4800, 5200, 5600, 6000, 6400):
                return "DDR5"
            if freq in (1600, 1866):
                return "DDR3"
        return None

    def parse_product(self, p) -> dict | None:
        name_tag = p.select_one("p.product-title")
        price_container = p.select_one('span.woocommerce-Price-amount')

        if not name_tag or not price_container:
            return None

        url_tag = name_tag.select_one("a")
        url = url_tag.get("href") if url_tag else None
        if url and not url.startswith('http'):
            url = "https://www.acosa.com.gt" + url

        price_text = price_container.get_text(strip=True)
        product_name = name_tag.get_text(strip=True)

        ddr = self.parse_ddr(product_name)
        if self.es_notebook(product_name) and ddr == "DDR4":
            capacity = self.parse_capacity(product_name)
            frequency = self.parse_frequency(product_name)
            price = self.parse_price(price_text)
            today = date.today().isoformat()

            return {
                "store": "Acosa",
                "marca": self.obtener_marca(product_name),
                "product_name": product_name,
                "price_normal": price,
                "price_cash": price,
                "capacity": capacity,
                "frequency": frequency,
                "scraped_at": today,
                "available": True,
                "url": url
            }
        return None

    def scrape(self) -> list[dict]:
        rows = []
        try:
            self.configure_driver()
            self.driver.get(self.url)

            self.wait_bypass_verification()
            self.wait_products()

            html = self.driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            products = soup.select("div.box-text-products")

            print(f"  -> Encontrados {len(products)} productos en el HTML tras pasar verificación")

            for p in products:
                product = self.parse_product(p)
                if product:
                    rows.append(product)

        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            if self.driver:
                self.driver.quit()

        return rows

    def save_to_supabase(self):
        try:
            rows = self.scrape()

            if not rows:
                print(" No hay datos para guardar")
                return

            res = supabase.table("ram_prices").upsert(rows).execute()

            print(f"***    Insertados {len(rows)} datos de tienda 7.    ***")
            print("\n" + "=" * 70)

            return True
        except Exception as e:
            print(f"Error: {e}")
            return False