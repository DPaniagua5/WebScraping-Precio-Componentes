import os
import sys
from dotenv import load_dotenv
from Shop1_scraper import Shop1Scraper
from Shop2_scraper import Shop2Scraper
from Shop3_scraper import Shop3Scraper
from Shop4_scraper import Shop4Scraper
from Shop5_scraper import Shop5Scraper
from Shop6_scraper import Shop6Scraper
from Shop7_scraper import Shop7Scraper

def main():
    load_dotenv()

    url1 = os.getenv('R_Shop1')
    url2 = os.getenv('R_Shop2')
    url3 = os.getenv('R_Shop3')
    url4 = os.getenv('R_Shop4')
    url5 = os.getenv('R_Shop5')
    url6 = os.getenv('R_Shop6')
    url7 = os.getenv('R_Shop7')
    try:
        scraper1 = Shop1Scraper(url1)
        scraper2 = Shop2Scraper(url2)
        scraper3 = Shop3Scraper(url3)
        scraper4 = Shop4Scraper(url4)
        scraper5 = Shop5Scraper(url5)
        scraper6 = Shop6Scraper(url6)
        scraper7 = Shop7Scraper(url7)

        exito1 = scraper1.scrape()
        exito2 = scraper2.save_to_supabase()
        exito3 = scraper3.save_to_supabase()
        exito4 = scraper4.save_to_supabase()
        exito5 = scraper5.save_to_supabase()
        exito6 = scraper6.save_to_supabase()
        exito7 = scraper7.scrape()
        if exito1 and exito2 and exito3 and exito4 and exito5 and exito6:
        #if exito7:
            print("***    PROCESO COMPLETADO EXITOSAMENTE    ***")
            return 0
        else:
            print("***    PROCESO COMPLETADO CON ADVERTENCIAS    ***")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n ***    Proceso interrumpido por el usuario    ***")
        return 130
    except Exception as e:
        print(f"\n***    ERROR FATAL: {e}    ***")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("=" * 70 + "\n")


if __name__ == "__main__":
    sys.exit(main())



