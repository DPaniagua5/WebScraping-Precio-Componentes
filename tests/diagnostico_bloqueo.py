import requests

URL = "https://acosa.com.gt/product-category/tecnologia/almacenamiento/tecnologia-almacenamiento-memorias-ram/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-GT,es;q=0.9",
}

session = requests.Session()
r = session.get(URL, headers=HEADERS, timeout=20, allow_redirects=True)

print("=" * 70)
print("DIAGNÓSTICO DE RESPUESTA")
print("=" * 70)

# 1) ¿La URL final es distinta a la que pediste? -> Te redirigió
print(f"\n1) URL solicitada:  {URL}")
print(f"   URL final:       {r.url}")
if r.url != URL:
    print("   HUBO REDIRECCIÓN - esto es una señal fuerte de bloqueo/verificación")
else:
    print("   No hubo redirección")

# 2) ¿El status code es sospechoso?
print(f"\n2) Status code: {r.status_code}")

# 3) ¿El HTML contiene palabras clave de verificación/bloqueo?
texto = r.text.lower()
señales_bloqueo = [
    "bxverify", "verificando", "checking your browser", "cloudflare",
    "just a moment", "please wait", "ddos-guard", "cargando",
    "captcha", "attention required", "access denied", "bot detected"
]
encontradas = [s for s in señales_bloqueo if s in texto]

print(f"\n3) Tamaño del HTML recibido: {len(r.text)} caracteres")
if encontradas:
    print(f"  Se encontraron palabras de verificación/bloqueo: {encontradas}")
else:
    print("   No se encontraron palabras típicas de bloqueo")

# 4) ¿El selector que usas normalmente aparece en el HTML?
if "box-text-products" in r.text:
    print("\n4) El selector 'box-text-products' SÍ aparece en el HTML")
    print("   -> Si aun así no se extraen productos, el problema es de SELECTOR/PARSEO, no de bloqueo")
else:
    print("\n4) El selector 'box-text-products' NO aparece en el HTML recibido")
    print("   -> Esto confirma que no estás recibiendo la página real de productos")

# 5) Mostrar los primeros 800 caracteres para inspección visual
print("\n" + "=" * 70)
print("PRIMEROS 800 CARACTERES DEL HTML RECIBIDO:")
print("=" * 70)
print(r.text[:800])
print("\n" + "=" * 70)