import os, json
import sys
from dotenv import load_dotenv
from Shop1_scraper import Shop1Scraper
from Shop2_scraper import Shop2Scraper
from Shop3_scraper import Shop3Scraper
from Shop4_scraper import Shop4Scraper
from Shop6_scraper import Shop6Scraper
from Shop7_scraper import Shop7Scraper
from Shop8_scraper import Shop8Scraper
from Shop9_scraper import Shop9Scraper
from Scraper_ssd import ShopScraper

def main():
    load_dotenv()

    url1 = os.getenv('R_Shop1')
    url2 = os.getenv('R_Shop2')
    url3 = os.getenv('R_Shop3')
    url4 = os.getenv('R_Shop4')
    url5 = os.getenv('R_Shop5')
    url6 = os.getenv('R_Shop6')
    url7 = os.getenv('R_Shop7')
    url8 = os.getenv('R_Shop8')
    url9_1 = os.getenv('R_Shop9_1')
    url9_2 = os.getenv('R_Shop9_2')

    try:
        # scraper1 = Shop1Scraper(url1)
        # scraper2 = Shop2Scraper(url2)
        # scraper3 = Shop3Scraper(url3)
        # scraper4 = Shop4Scraper(url4)
        # scraper6 = Shop6Scraper(url6)
        # scraper7 = Shop7Scraper(url7)
        # scraper8 = Shop8Scraper(url8)
        # scraper9_1 = Shop9Scraper(url9_1)
        # scraper9_2 = Shop9Scraper(url9_2)

        # exito1 = scraper1.scrape()
        # exito2 = scraper2.save_to_supabase()
        # exito3 = scraper3.save_to_supabase()
        # exito4 = scraper4.save_to_supabase()
        # exito6 = scraper6.save_to_supabase()
        # exito7 = scraper7.save_to_supabase()
        # exito8 = scraper8.save_to_supabase()
        # exito9_1 = scraper9_1.save_to_supabase()
        # exito9_2 = scraper9_2.save_to_supabase()

        scraping_ssd()

        # if exito1 and exito2 and exito3 and exito4 and exito6 and exito7 and exito8 and exito9_1 and exito9_2:
        # if exito_ssd:
        #     print("***    PROCESO RAM COMPLETADO EXITOSAMENTE    ***")
        #     return 0
        # else:
        #     print("***    PROCESO RAM COMPLETADO CON ADVERTENCIAS    ***")
        #     return 1
        
            
    except KeyboardInterrupt:
        print("\n\n ***    Proceso interrumpido por el usuario    ***")
        return 130
    except Exception as e:
        print(f"\n ***    ERROR FATAL: {e}    ***")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("=" * 70 + "\n")

import os

def load_shop_config(shop_index: int) -> dict | None:
    raw = os.getenv(f"Conf_Shop{shop_index}")
    if not raw:
        return None
    return json.loads(raw)

def scraping_ssd():
    shop_index = 1

    while True:
        config = load_shop_config(shop_index)
        if not config:
            print(f"No más configuraciones encontradas. Finalizando en tienda {shop_index - 1}.")
            break
        
        base_url = os.getenv(f"S_Shop{shop_index}")
        if base_url:
            process_shop(base_url, config)
        
        tab = 1
        while True:
            tab_url = os.getenv(f"S_Shop{shop_index}_{tab}")
            if not tab_url:
                break  # No hay más pestañas para esta tienda
            
            process_shop(tab_url, config)
            tab += 1

        shop_index += 1

def process_shop(url: str, cfg: dict):
    scraper = ShopScraper(
        url=url,
        store=cfg["store"],
        tag_padre=cfg["tag_padre"],
        tag_producto=cfg["tag_producto"],
        tag_price=cfg["tag_price"],
        tipo_price=cfg["tipo_price"],
        tag_price_cash=cfg["tag_price_cash"],
        tipo_price_cash=cfg["tipo_price_cash"],
        dominio=cfg["dominio"],
        available_tag=cfg["available_tag"]
    )

    rows = scraper.scrape()
    # scraper.save_to_supabase(rows)


if __name__ == "__main__":
    sys.exit(main())