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

class Shop1Scraper:
    def __init__(self, url=None, headless=True):
        self.url = url
        self.productos = []
        self.headless = headless
        self.driver = None

    # Configura Chrome como webdriver-manager
    def configure_driver(self):
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    #Espera que los productos se carguen
    def Wait(self, timeout=30):
        print("Esperando carga de productos.....")
        time.sleep(3)

        wait = WebDriverWait(self.driver, timeout)

        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.css-g5oay9, a[href*='/precios_stock_detallado/']")))
            print(" Productos detectados en la página")
            time.sleep(2)
            
            # Hacer múltiples scrolls para cargar todos los productos lazy-loaded
            print("Haciendo scroll para cargar todos los productos...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scrolls = 10

            while scroll_attempts < max_scrolls:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                if new_height == last_height:
                    # Si no hay más contenido para cargar, hacer un intento más
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # Resetear si encontramos nuevo contenido
                
                last_height = new_height
                
                # Contar productos cargados
                current_products = len(self.driver.find_elements(By.CSS_SELECTOR, "a.css-g5oay9, a[href*='/precios_stock_detallado/']"))
            
            # Scroll de vuelta arriba
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
        except Exception as e:
            print(f"Timeout esperando productos: {e}")


    import re

    def extraer_precio(self, texto: str) -> int | None:
        match = re.search(r'Q\s*([\d,]+)', texto, re.IGNORECASE)
        if not match:
            return None
        numero_str = match.group(1).replace(',', '')
        try:
            return int(numero_str)
        except ValueError:
            return None

    def find_product(self, elemento, index):
        product = {
            'id': index,
            'marca': '',
            'nombre': '',
            'precio_normal': None,
            'precio_efectivo': None,
            'capacidad': '',
            'frecuencia': '',
            'url': ''
        }
        
        try:
            # Si el elemento es un enlace, obtener su URL
            if elemento.tag_name == 'a':
                product['url'] = elemento.get_attribute('href')
            
            # Extraer MARCA (span.css-ynol38)
            try:
                marca_elem = elemento.find_element(By.CSS_SELECTOR, "span.css-ynol38")
                product['marca'] = marca_elem.text.strip()
            except:
                # Intentar selector alternativo
                try:
                    marca_elem = elemento.find_element(By.CSS_SELECTOR, "span[class*='ynol']")
                    product['marca'] = marca_elem.text.strip()
                except:
                    pass
            
            # Extraer NOMBRE (span.css-5xrf24)
            try:
                nombre_elem = elemento.find_element(By.CSS_SELECTOR, "span.css-5xrf24")
                product['nombre'] = nombre_elem.text.strip()
            except:
                # Intentar selector alternativo
                try:
                    nombre_elem = elemento.find_element(By.CSS_SELECTOR, "span[class*='5xrf']")
                    product['nombre'] = nombre_elem.text.strip()
                except:
                    # Usar todo el texto del elemento
                    product['nombre'] = elemento.text.strip().split('\n')[0] if elemento.text else ""
            
            # Extraer precio_normal (span.css-185b4xi)
            try:
                # Buscamos el elemento que contiene el texto "Precio normal"
                precio_elem = elemento.find_element(By.XPATH, ".//span[contains(text(), 'Precio normal')]/..")
                texto_completo = precio_elem.get_attribute('innerText')
                product['precio_normal'] = self.extraer_precio(texto_completo)
            except:
                pass
            # Extraer PRECIO BENEFICIO (span.css-15acwd8)
            try:
                precio_beneficio_elem = elemento.find_element(By.CSS_SELECTOR, "span.css-15acwd8")
                texto_completo = precio_beneficio_elem.text.strip()
                product['precio_efectivo'] = self.extraer_precio(texto_completo)
            except:
                try:
                    precio_beneficio_elem = elemento.find_element(By.CSS_SELECTOR, "span[class*='15acwd']")
                    texto_completo = precio_beneficio_elem.text.strip()
                    product['precio_efectivo'] = self.extraer_precio(texto_completo)
                except:
                    pass
            
            precios_disponibles = []
            

            # Extraer CAPACIDAD del nombre
            if product['nombre']:
                cap_match = re.search(r'\b(\d+\s*GB)\b', product['nombre'], re.IGNORECASE)
                if cap_match:
                    product['capacidad'] = cap_match.group(1)
            
            # Extraer FRECUENCIA del nombre
            if product['nombre']:
                freq_match = None
                
                match_mhz = re.search(r'\b(\d{4}\s*MHz)\b', product['nombre'], re.IGNORECASE)
                if match_mhz:
                    freq_match = match_mhz
                
                if not freq_match:
                    match_mts = re.search(r'\b(\d{4}\s*MT/s)\b', product['nombre'], re.IGNORECASE)
                    if match_mts:
                        freq_match = match_mts
                
                if freq_match:
                    product['frecuencia'] = freq_match.group(1).replace(' ', '')
        except Exception as e:
            print(f"Error procesando producto {index}: {e}")
        
        return product
    
    #Ejecuta el scraping
    def scrape(self):
        try:
            print("=" * 70)
            print("WEB SCRAPER RAM DDR4 NOTEBOOK - INTELAF.COM")
            print("=" * 70)
            
            print("\n 1.) Configurando navegador...")
            self.configure_driver()
            print("** ChromeDriver instalado y configurado **")
            
            print(f"\n 2.) Navegando a pagina")
            self.driver.get(self.url)
            print("** Página cargada **")
            
            print("\n3.) Esperando carga de contenido dinámico...")
            self.Wait()
            
            
            print("\n4.)  Extrayendo productos...")
            
            elementos = self.driver.find_elements(By.CSS_SELECTOR, "a.css-g5oay9")
            
            if not elementos:
                print("   No se encontraron productos con a.css-g5oay9")
                print("   Intentando selectores alternativos...")
                
                # Intentar otros selectores basados en la estructura
                selectores_alternativos = [
                    "a[class*='css-g5']",  # Selector parcial
                    "div.css-1v6lj4c",     # Contenedor individual del producto
                    "div.css-lekt0u",      # Otro posible contenedor
                    "a[href*='/precios_stock_detallado/']",  # Por URL
                ]
                
                for selector in selectores_alternativos:
                    elementos = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elementos:
                        print(f"** Encontrados {len(elementos)} con: {selector} **")
                        break
            else:
                print(f"** Encontrados {len(elementos)} productos **")
            
            if not elementos:
                print("\n** No se pudieron encontrar productos **")
                return False
            
            print(f"\n 5.) Procesando {len(elementos)} productos...")
            
            for i, elemento in enumerate(elementos, 1):
                producto = self.find_product(elemento, i)
                
                # Solo guardar si tiene nombre o precio
                if producto['nombre'] or producto['precio_final']:
                    self.productos.append(producto)
                    
                    
            print(f"\n*** Total extraído: {len(self.productos)} productos ***")
            j=1
            if self.productos:
                print("\n 6.) Guardando resultados...")
                for producto in self.productos:
                    today = date.today().isoformat()
                    rows = []
                    rows.append({
                        "store": "Intelaf",
                        "marca": producto['marca'],
                        "product_name": producto['nombre'],
                        "price_normal": producto['precio_normal'],
                        "price_cash": producto['precio_efectivo'],
                        "capacity": producto['capacidad'],
                        "frequency": producto['frecuencia'],
                        "scraped_at": today
                    })


                    supabase.table("ram_prices").upsert(rows).execute()
                    
                return True
            else:
                print("\n** No se extrajeron productos **")
                return False
            
        except Exception as e:
            print(f"\n ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            if self.driver:
                print("\n 7.) Cerrando navegador...")
                self.driver.quit()
                print("** Cerrado **")