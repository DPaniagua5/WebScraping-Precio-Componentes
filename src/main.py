import os
import sys
from dotenv import load_dotenv
from scraper import Shop1Scraper

def main():
    load_dotenv()

    url = os.getenv('R_Shop1')

    try:
        scraper = Shop1Scraper(
            url
        )

        exito = scraper.scrape()

        print("\n" + "=" * 70)
        if exito:
            print("** PROCESO COMPLETADO EXITOSAMENTE **")
            return 0
        else:
            print("**  PROCESO COMPLETADO CON ADVERTENCIAS **")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n *** Proceso interrumpido por el usuario ***")
        return 130
    except Exception as e:
        print(f"\n*** ERROR FATAL: {e} ***")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        print("=" * 70 + "\n")


if __name__ == "__main__":
    sys.exit(main())



