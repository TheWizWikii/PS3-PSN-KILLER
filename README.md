# 🎮 PS3 PSN Killer (Turbo Pro)

Una aplicación de escritorio moderna desarrollada en **Python** con **CustomTkinter** diseñada para buscar, filtrar y descargar contenido oficial de PS3 de forma masiva y a alta velocidad (juegos, actualizaciones, demos, temas, avatares, DLCs y licencias RAP).

> **💡 Nota importante:** Ideal para respaldar y preservar todo tu contenido digital ante un hipotético cierre de los servidores oficiales de la tienda de PS3. ¡Guarda tus juegos antes de que sea tarde! Xd

---

## ✨ Características Principales

* **🚀 Motor de Descarga Turbo Multihilo:** Soporta hasta 16 hilos concurrentes con peticiones HTTP por rangos (`Range`) para exprimir al máximo tu conexión de fibra óptica.
* **🔍 Búsqueda y Filtros Avanzados:** Filtra por nombre, Title ID o región (`US`, `EU`, `JP`, `ASIA`) al instante.
* **📂 Organización Automática:** Clasifica y guarda cada tipo de contenido en su carpeta correspondiente (`Juegos_PS3`, `PS2_Classics`, `Actualizaciones_PS3`, etc.).
* **🔑 Soporte para Licencias:** Botón de acceso directo para descargar paquetes de licencias RAP universales.
* **🎨 Interfaz Oscura Minimalista:** Desarrollada con CustomTkinter para una experiencia visual limpia y moderna.
* **📦 Autoinstalación de Dependencias:** El script verifica e instala automáticamente las librerías necesarias (`customtkinter`, `requests`, `beautifulsoup4`) al primer inicio.

---

## 🛠️ Cómo Funciona en General

La aplicación opera mediante los siguientes componentes lógicos:

1. **Lectura de Bases de Datos Locales:** El script procesa archivos en formato TSV (`PS3_GAMES.tsv`, `PS3_UPDATES.tsv`, etc.) que contienen los catálogos oficiales con los metadatos y las URLs directas de los servidores.
2. **Detección de Regiones:** Analiza automáticamente el prefijo del *Title ID* (por ejemplo, `BLUS`, `BLES`, `NPUB`) para clasificar la región del juego de forma inteligente.
3. **Segmentación de Archivos (Multihilo):** 
   * Primero realiza una petición HTTP `HEAD` para comprobar el tamaño exacto del archivo `.pkg` y si el servidor admite descargas por rangos (`Accept-Ranges`).
   * Si es compatible, divide el archivo en partes iguales y lanza múltiples hilos en paralelo que escriben de manera concurrente en el disco duro, acelerando drásticamente el proceso frente a una descarga lineal tradicional.

---

## ⚙️ Requisitos Previos

* Tener instalado **Python 3.8** o superior en tu sistema.

---

## 🚀 Instalación y Uso

1. Clona este repositorio o descarga los archivos fuente:
   ```bash
   git clone [https://github.com/tu-usuario/tu-repositorio.git](https://github.com/tu-usuario/tu-repositorio.git)
   cd tu-repositorio
