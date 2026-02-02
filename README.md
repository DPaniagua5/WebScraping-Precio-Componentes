# Análisis de Precios de Memoria RAM (Guatemala)

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![Web Scraping](https://img.shields.io/badge/Web%20Scraping-Python-orange)
![Status](https://img.shields.io/badge/Status-Educational-success)
![GitHub Actions](https://img.shields.io/github/actions/workflow/status/DPaniagua5/WebScraping-Precio-Componentes/scraper.yml?label=Scraper)
![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?logo=supabase&logoColor=white)
![Region](https://img.shields.io/badge/Region-Guatemala-blue)

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
│   ├── Shop1_scraper.py
│   ├── Shop2_scraper.py
│   ├── Shop3_scraper.py
│   ├── main.py
│   └── supabase_client.py
├── .github/
│   └── workflows/
│       └── scraper.yml
├── requirements.txt
└── README.md
```
