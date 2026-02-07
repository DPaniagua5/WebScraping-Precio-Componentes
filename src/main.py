import os
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
        scraper1 = Shop1Scraper(url1)
        scraper2 = Shop2Scraper(url2)
        scraper3 = Shop3Scraper(url3)
        scraper4 = Shop4Scraper(url4)
        scraper6 = Shop6Scraper(url6)
        scraper7 = Shop7Scraper(url7)
        scraper8 = Shop8Scraper(url8)
        scraper9_1 = Shop9Scraper(url9_1)
        scraper9_2 = Shop9Scraper(url9_2)

        exito1 = scraper1.scrape()
        exito2 = scraper2.save_to_supabase()
        exito3 = scraper3.save_to_supabase()
        exito4 = scraper4.save_to_supabase()
        exito6 = scraper6.save_to_supabase()
        exito7 = scraper7.save_to_supabase()
        exito8 = scraper8.save_to_supabase()
        exito9_1 = scraper9_1.save_to_supabase()
        exito9_2 = scraper9_2.save_to_supabase()

        scraping_ssd()

        if exito1 and exito2 and exito3 and exito4 and exito6 and exito7 and exito8 and exito9_1 and exito9_2:
        #if exito9:
            print("***    PROCESO RAM COMPLETADO EXITOSAMENTE    ***")
            return 0
        else:
            print("***    PROCESO RAM COMPLETADO CON ADVERTENCIAS    ***")
            return 1
        
            
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

def scraping_ssd():
    for i in range(2,5):
        url = os.getenv(f"S_Shop{i}")   
        if url:
            scraper = ShopScraper(url,"Rech", "div.product-details","h2.product-title", "product-price-normal","span","product-price:not(.product-price-normal)", "span")
            rows = scraper.scrape()
            scraper.save_to_supabase(rows)


if __name__ == "__main__":
    sys.exit(main())