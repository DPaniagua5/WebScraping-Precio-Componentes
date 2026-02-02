import os
import sys
from dotenv import load_dotenv
from Shop1_scraper import Shop1Scraper
from Shop2_scraper import Shop2Scraper
from Shop3_scraper import Shop3Scraper

def main():
    load_dotenv()

    url1 = os.getenv('R_Shop1')
    url2 = os.getenv('R_Shop2')
    url3 = os.getenv('R_Shop3')

    try:
        scraper1 = Shop1Scraper(url1)
        scraper2 = Shop2Scraper(url2)
        scraper3 = Shop3Scraper(url3)
        

        exito1 = scraper1.scrape()
        exito2 = scraper2.save_to_supabase()
        exito3 = scraper3.save_to_supabase()
        
        if exito1 and exito2 and exito3:
        #if exito2:
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



