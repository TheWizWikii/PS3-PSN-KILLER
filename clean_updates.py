import os
import re
import csv
from bs4 import BeautifulSoup

def extract_version_from_url_or_text(url, text):
    """ Extrae la versión real (ej: v01.19) desde la URL del PKG o del texto """
    # 1. Buscar en la URL oficial de Sony (patrón -A0119- o -A0109-)
    url_match = re.search(r'-A(\d{2})(\d{2})-', url, re.IGNORECASE)
    if url_match:
        return f"v{url_match.group(1)}.{url_match.group(2)}"

    # 2. Buscar patrón estándar en la URL (ej: v01.09 o 01.09)
    url_match_gen = re.search(r'[vV]?(\d{1,2}\.\d{2})', url)
    if url_match_gen:
        return f"v{url_match_gen.group(1)}"

    # 3. Buscar en el texto original si no se encontró en la URL
    text_match = re.search(r'\[?v?(\d{1,2}\.\d{2})\]?', text, re.IGNORECASE)
    if text_match:
        return f"v{text_match.group(1)}"

    return "v01.00"

def clean_and_convert_updates(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"❌ Error: No se encontró el archivo '{input_path}'")
        return

    print("🔄 Analizando y extrayendo versiones numéricas de las Updates...")

    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    rows = soup.find_all('tr')
    
    clean_records = []

    if rows:
        for row in rows:
            row_str = str(row)
            
            # Filtrar enlaces PKG válidos
            urls = re.findall(r'(http[s]?://[^\s<"\'\t\n\r]+\.pkg)', row_str, re.IGNORECASE)
            valid_urls = [u for u in urls if '/np//_' not in u and ('_T0' in u or '_00' in u)]

            if not valid_urls:
                continue

            clean_url = valid_urls[-1]

            # Extraer Title ID
            tid_match = re.search(r'([A-Z]{4}\d{5})', row_str)
            title_id = tid_match.group(1) if tid_match else "DESCONOCIDO"

            # Extraer texto del juego
            cols = row.find_all(['td', 'th'])
            cells_text = [c.get_text(strip=True) for c in cols]
            
            raw_title = ""
            for text in cells_text:
                if not text.startswith("http") and not re.match(r'^[A-Z]{4}\d{5}$', text):
                    temp_name = re.sub(r'[A-Z]{4}\d{5}', '', text)
                    temp_name = re.sub(r'http[s]?://[^\s]+', '', temp_name).strip()
                    
                    if re.match(r'^[a-fA-F0-9]{15,}', temp_name):
                        continue

                    if len(temp_name) > len(raw_title):
                        raw_title = temp_name

            # Extraer la versión real
            version = extract_version_from_url_or_text(clean_url, raw_title)

            # Limpiar el nombre quitándole el número de versión pegado
            game_name = re.sub(r'\[?v?\d{1,2}\.\d{2}\]?', '', raw_title).strip()

            if not game_name or game_name.isdigit():
                game_name = f"Call of Duty / Update {title_id}" if "BLES" in title_id or "BLUS" in title_id else f"Update {title_id}"

            clean_records.append((title_id, game_name, version, clean_url))

    # Eliminar duplicados exactamente iguales
    unique_records = list(dict.fromkeys(clean_records))
    unique_records.sort(key=lambda x: (x[1].lower(), x[2]))

    # Guardar TSV en orden: Title_ID \t Nombre \t Versión \t URL
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        for item in unique_records:
            writer.writerow([item[0], item[1], item[2], item[3]])

    print(f"✅ Se han procesado {len(unique_records)} actualizaciones con su versión exacta.")
    print(f"📄 Guardado en: '{output_path}'")

if __name__ == "__main__":
    clean_and_convert_updates("PS3_UPDATES.txt", "PS3_UPDATES.tsv")