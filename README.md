# Análisis de Precios de Memoria RAM (Guatemala)

Este proyecto es un **scraper web educativo** desarrollado en **Python**, cuyo objetivo es recolectar y analizar la evolución de precios de **memorias RAM para laptops (DDR4)** en el mercado de Guatemala.

La información recolectada se almacena en una base de datos y permite visualizar tendencias de precios a lo largo del tiempo mediante un dashboard web.

---

## Objetivo del proyecto

- Practicar **web scraping con Python**
- Automatizar la recolección diaria de datos con **github actions**
- Analizar la variación de precios en el tiempo
- Construir un flujo completo **backend + base de datos + frontend**
- Aplicar buenas prácticas de automatización y análisis de datos

> Este proyecto tiene **fines exclusivamente educativos**.

---

## Tecnologías utilizadas

### Backend / Scraping

- Python 3
- Requests
- BeautifulSoup
- Selenium (para contenido dinámico)
- Expresiones regulares (regex)

### Base de datos

- Supabase (PostgreSQL)

### Automatización

- GitHub Actions (ejecución programada)

### Frontend

- HTML / CSS / JavaScript
- Dashboard estático desplegado en GitHub Pages

---

## Estructura general del proyecto

```text
.
├── src/
│   ├── Server/
│   │   ├── scrapers/
│   │   ├── main.py
│   │   └── supabase_client.py
│   └── Frontend/
│       └── dashboard
├── .github/
│   └── workflows/
│       └── scraper.yml
├── requirements.txt
└── README.md
```
