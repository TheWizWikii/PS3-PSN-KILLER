import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

# ==========================================
# 0. VERIFICACIÓN E INSTALACIÓN DE DEPENDENCIAS
# ==========================================
def verificar_e_instalar_dependencias():
    librerias_requeridas = {
        "customtkinter": "customtkinter",
        "bs4": "beautifulsoup4",
        "requests": "requests"
    }
    
    faltantes = []
    for mod, pip_name in librerias_requeridas.items():
        try:
            __import__(mod)
        except ImportError:
            faltantes.append(pip_name)

    if faltantes:
        root = tk.Tk()
        root.withdraw()
        
        mensaje = (
            f"Para ejecutar esta aplicación se necesitan las siguientes librerías:\n\n"
            f"• {', '.join(faltantes)}\n\n"
            f"¿Deseas instalarlas automáticamente ahora mismo?"
        )
        
        respuesta = messagebox.askyesno("Librerías Faltantes", mensaje)
        
        if respuesta:
            root.destroy()
            print("⏳ Instalando dependencias, por favor espera...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", *faltantes])
                messagebox.showinfo("Éxito", "¡Librerías instaladas correctamente! Iniciando la app...")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron instalar las librerías automáticamente:\n{e}")
                sys.exit(1)
        else:
            messagebox.showwarning("Cancelado", "La aplicación no puede continuar sin estas librerías.")
            root.destroy()
            sys.exit(0)

verificar_e_instalar_dependencias()

# ==========================================
# IMPORTACIONES PRINCIPALES DE LA APLICACIÓN
# ==========================================
import os
import csv
import re
import time
import requests
import threading
from tkinter import ttk
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# URL directa al pack de licencias
GITHUB_RAP_URL = "https://github.com/TheWizWikii/PS3-Stuff-Repository/releases/download/3/License_Pack_31.153.pkg"

CARPETAS = {
    "PS3": "Juegos_PS3",
    "PS2": "PS2_Classics",
    "PS1": "PS1_Classics",
    "Updates": "Actualizaciones_PS3",
    "Demos": "Demos_PS3",
    "Temas": "Temas_PS3",
    "Avatares": "Avatares_PS3",
    "DLCs": "DLCs_PS3",
    "RAP": "Keys_RAP"
}

# Crear carpetas de destino automáticamente
for folder in CARPETAS.values():
    os.makedirs(folder, exist_ok=True)


def sanitize_filename(filename):
    r"""
    Limpia el nombre del archivo para que sea válido en Windows/Linux/macOS.
    Elimina caracteres no permitidos como : \ / * ? " < > |
    """
    filename = re.sub(r'[:\\/|]', ' -', filename)
    filename = re.sub(r'[?*"<>]', '', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename


def auto_detect_region(tid):
    """ Detecta la región del juego basándose en el prefijo del Title ID """
    tid = tid.upper()
    if len(tid) >= 4:
        code = tid[:4]
        if code.startswith(('BCUS', 'BLUS', 'NPUA', 'NPUB', 'NPUG', 'NPUZ', 'UP')):
            return 'US'
        elif code.startswith(('BCES', 'BLES', 'NPEA', 'NPEB', 'NPEG', 'NPEZ', 'EP')):
            return 'EU'
        elif code.startswith(('BCJS', 'BLJS', 'NPJA', 'NPJB', 'NPJH', 'JP')):
            return 'ASIA'
        elif code.startswith(('BCAS', 'BLAS', 'NPHA', 'NPHB', 'HP')):
            return 'ASIA'
    return 'ALL'


def split_name_and_version(raw_name, default_ver="Base"):
    """ Separa versiones adosadas al nombre """
    if not raw_name:
        return "", default_ver

    match = re.search(r'(.*?)(?:\[?v?(\d{1,2}\.\d{2})\]?)$', raw_name.strip(), re.IGNORECASE)
    if match and match.group(2):
        clean_name = match.group(1).strip()
        version_str = f"v{match.group(2)}"
        return clean_name, version_str

    return raw_name.strip(), default_ver


def format_bytes(bytes_num):
    """ Convierte un número de bytes en formato MB/GB legible """
    try:
        b = float(bytes_num)
        if b <= 0:
            return "N/A"
        if b >= 1024**3:
            return f"{b / (1024**3):.2f} GB"
        elif b >= 1024**2:
            return f"{b / (1024**2):.1f} MB"
        elif b >= 1024:
            return f"{b / 1024:.0f} KB"
        return f"{b:.0f} B"
    except (ValueError, TypeError):
        return "N/A"


def format_speed(bytes_per_sec):
    """ Da formato a la velocidad en MB/s y Mbps """
    if bytes_per_sec <= 0:
        return "0 KB/s"
    mb_s = bytes_per_sec / (1024 * 1024)
    mbps = (bytes_per_sec * 8) / (1024 * 1024)
    if mb_s >= 1:
        return f"{mb_s:.1f} MB/s | {mbps:.1f} Mbps"
    else:
        kb_s = bytes_per_sec / 1024
        return f"{kb_s:.0f} KB/s"


class PS3DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PS3 PSN KILLER")
        self.geometry("1180x740")

        self.setup_dark_theme()

        self.data_store = {
            "PS3": [], "PS2": [], "PS1": [], "Updates": [],
            "Demos": [], "Temas": [], "Avatares": [], "DLCs": []
        }

        self.create_ui()
        self.load_all_data()

    def setup_dark_theme(self):
        """ Configura el estilo oscuro minimalista para los Treeview de Tkinter """
        style = ttk.Style()
        style.theme_use("default")

        bg_dark = "#1a1a1a"
        fg_white = "#e1e1e1"
        header_bg = "#2b2b2b"
        select_bg = "#1f6aa5"

        style.configure(
            "Treeview",
            background=bg_dark,
            foreground=fg_white,
            fieldbackground=bg_dark,
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10)
        )
        
        style.configure(
            "Treeview.Heading",
            background=header_bg,
            foreground=fg_white,
            relief="flat",
            font=("Segoe UI", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", select_bg)],
            foreground=[("selected", "#ffffff")]
        )

        style.map(
            "Treeview.Heading",
            background=[("active", "#3a3a3a")]
        )

    def create_ui(self):
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(fill="x", padx=10, pady=5)

        title_label = ctk.CTkLabel(
            top_frame, 
            text="🎮 PS3 PSN KILLER (Downloader)", 
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=15)

        rap_btn = ctk.CTkButton(
            top_frame, 
            text="🔑 Descargar Licencias (31.153)", 
            fg_color="#1f77b4", 
            hover_color="#135d96", 
            command=self.download_rap
        )
        rap_btn.pack(side="right", padx=15, pady=5)

        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=5)

        search_label = ctk.CTkLabel(search_frame, text="🔍 Buscar:", font=ctk.CTkFont(weight="bold"))
        search_label.pack(side="left", padx=10)

        self.search_entry = ctk.CTkEntry(
            search_frame, 
            placeholder_text="Escribe el nombre del juego (ej: Call of Duty) o Title ID..."
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.search_entry.bind("<KeyRelease>", self.filter_tables)

        region_label = ctk.CTkLabel(search_frame, text="🌍 Región:", font=ctk.CTkFont(weight="bold"))
        region_label.pack(side="left", padx=(15, 5))

        self.region_combo = ctk.CTkComboBox(
            search_frame,
            values=["TODAS", "EU", "US", "JP", "ASIA"],
            width=100,
            command=self.filter_tables
        )
        self.region_combo.set("TODAS")
        self.region_combo.pack(side="left", padx=10)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        self.tabs = {}
        self.trees = {}

        categorias = ["PS3", "PS2", "PS1", "Updates", "Demos", "Temas", "Avatares", "DLCs"]
        
        for cat in categorias:
            tab = self.tabview.add(cat)
            self.tabs[cat] = tab
            self._build_tree_view(tab, cat)

        self.count_frame = ctk.CTkFrame(self, height=30, fg_color="#1e1e1e")
        self.count_frame.pack(fill="x", padx=10, pady=(2, 2))

        self.count_label = ctk.CTkLabel(
            self.count_frame, 
            text="📊 Cargando resumen de contenido...", 
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color="#b0b0b0"
        )
        self.count_label.pack(side="left", padx=15, pady=2)

        # Barra de estado inferior con la marca de agua integrada de forma sutil
        self.status_frame = ctk.CTkFrame(self, height=35)
        self.status_frame.pack(fill="x", side="bottom", padx=10, pady=5)

        self.status_label = ctk.CTkLabel(self.status_frame, text="Estado: Listo", font=ctk.CTkFont(size=12))
        self.status_label.pack(side="left", padx=10)

        # MARCA DE AGUA: Creado por TheWizWiki (Discreta a la derecha de la barra de estado)
        watermark_label = ctk.CTkLabel(
            self.status_frame, 
            text="✨ Creado por TheWizWiki", 
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#888888"
        )
        watermark_label.pack(side="right", padx=15)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame)
        self.progress_bar.pack(side="right", padx=10, pady=8)
        self.progress_bar.set(0)

    def _build_tree_view(self, parent, category):
        columns = ("title_id", "region", "name", "version", "size")
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="extended")

        tree.heading("title_id", text="ID / Código")
        tree.heading("region", text="Región")
        tree.heading("name", text="Nombre del Contenido / Juego")
        tree.heading("version", text="Versión")
        tree.heading("size", text="Tamaño")

        tree.column("title_id", width=110, anchor="center")
        tree.column("region", width=70, anchor="center")
        tree.column("name", width=550, anchor="w")
        tree.column("version", width=90, anchor="center")
        tree.column("size", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

        tree.bind("<Double-1>", lambda event: self.start_download(tree, category))
        
        btn = ctk.CTkButton(
            parent, 
            text=f"⬇️ Descargar Elemento(s) Seleccionado(s) ({category})", 
            command=lambda: self.start_download(tree, category)
        )
        btn.pack(side="bottom", fill="x", padx=5, pady=5)

        self.trees[category] = tree

    def _parse_tsv_row(self, row):
        if not row:
            return None

        if row[0].strip().lower() in ["title id", "id", "title_id"]:
            return None

        tid = row[0].strip()
        region = ""
        name = ""
        url = ""
        size_str = "N/A"

        if len(row) >= 4 and not row[1].startswith("http"):
            possible_region = row[1].strip()
            if possible_region in ["US", "EU", "JP", "ASIA", "FREE", "ALL"]:
                region = possible_region
                name = row[2].strip()
                url = row[3].strip()
            else:
                name = row[1].strip()
                url = row[3].strip() if row[3].startswith("http") else row[2].strip()
        elif len(row) >= 3:
            name = row[1].strip()
            url = row[2].strip()

        if len(row) >= 9 and row[8].strip().isdigit():
            size_str = format_bytes(row[8].strip())

        if not url.startswith("http"):
            return None

        if not region:
            region = auto_detect_region(tid)

        if not name or re.match(r'^[a-fA-F0-9]{15,}', name):
            name = f"Contenido ({tid})"

        return tid, region, name, url, size_str

    def load_all_data(self):
        if os.path.exists("PS3_GAMES.tsv"):
            with open("PS3_GAMES.tsv", "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter="\t")
                for row in reader:
                    parsed = self._parse_tsv_row(row)
                    if parsed:
                        tid, region, name, url, size_str = parsed
                        clean_name, ver = split_name_and_version(name, "Base")
                        
                        if "PS2" in clean_name.upper() or ("CLASSIC" in clean_name.upper() and "PS2" in tid):
                            self.data_store["PS2"].append((tid, region, clean_name, ver, size_str, url))
                        elif "PS1" in clean_name.upper() or "PSX" in clean_name.upper() or tid.startswith(("SLUS", "SLES")):
                            self.data_store["PS1"].append((tid, region, clean_name, ver, size_str, url))
                        else:
                            self.data_store["PS3"].append((tid, region, clean_name, ver, size_str, url))

        if os.path.exists("PS3_UPDATES.tsv"):
            with open("PS3_UPDATES.tsv", "r", encoding="utf-8", errors="ignore") as f:
                reader = csv.reader(f, delimiter="\t")
                for row in reader:
                    url = ""
                    name = ""
                    tid = ""

                    if len(row) >= 4:
                        tid = row[0].strip()[:9] if len(row[0].strip()) >= 9 else row[0].strip()
                        name = row[1].strip()
                        url = row[3].strip()
                    elif len(row) >= 3:
                        tid = row[0].strip()[:9] if len(row[0].strip()) >= 9 else row[0].strip()
                        name = row[1].strip()
                        url = row[2].strip()

                    if url.startswith("http"):
                        region = auto_detect_region(tid)
                        clean_name, extracted_ver = split_name_and_version(name, "v01.00")

                        if extracted_ver.lower() in ["update", "base"] or not extracted_ver:
                            url_ver_match = re.search(r'-A(\d{2})(\d{2})-', url, re.IGNORECASE)
                            if url_ver_match:
                                extracted_ver = f"v{url_ver_match.group(1)}.{url_ver_match.group(2)}"

                        size_match = re.search(r'\.pkg(\d+)$', url, re.IGNORECASE)
                        size_str = format_bytes(size_match.group(1)) if size_match else "N/A"

                        self.data_store["Updates"].append((tid, region, clean_name, extracted_ver, size_str, url))

        tsv_mappings = {
            "PS3_DEMOS.tsv": "Demos",
            "PS3_THEMES.tsv": "Temas",
            "PS3_AVATARS.tsv": "Avatares",
            "PS3_DLCS.tsv": "DLCs"
        }

        for file_name, cat in tsv_mappings.items():
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.reader(f, delimiter="\t")
                    for row in reader:
                        parsed = self._parse_tsv_row(row)
                        if parsed:
                            tid, region, name, url, size_str = parsed
                            clean_name, ver = split_name_and_version(name, "Base")
                            self.data_store[cat].append((tid, region, clean_name, ver, size_str, url))

        self.populate_trees()

    def update_summary_count(self):
        counts = {cat: len(self.trees[cat].get_children()) for cat in self.data_store.keys()}
        total = sum(counts.values())

        summary_text = (
            f"📦 PS3: {counts['PS3']:,}  |  "
            f"📦 PS2: {counts['PS2']:,}  |  "
            f"📦 PS1: {counts['PS1']:,}  |  "
            f"🔄 Updates: {counts['Updates']:,}  |  "
            f"🎮 Demos: {counts['Demos']:,}  |  "
            f"🎨 Temas: {counts['Temas']:,}  |  "
            f"👤 Avatares: {counts['Avatares']:,}  |  "
            f"📦 DLCs: {counts['DLCs']:,}  |  "
            f"🌐 TOTAL: {total:,} elementos"
        ).replace(",", ".")

        self.count_label.configure(text=summary_text)

    def populate_trees(self):
        for cat, items in self.data_store.items():
            tree = self.trees[cat]
            tree.delete(*tree.get_children())
            for item in items:
                tree.insert("", "end", values=(item[0], item[1], item[2], item[3], item[4]), tags=(item[5],))
        
        self.update_summary_count()

    def filter_tables(self, event=None):
        query = self.search_entry.get().strip().lower()
        selected_region = self.region_combo.get()

        for cat, items in self.data_store.items():
            tree = self.trees[cat]
            tree.delete(*tree.get_children())
            
            for item in items:
                title_id = item[0].lower()
                region = item[1]
                game_name = item[2].lower()

                match_text = (query in title_id) or (query in game_name)
                match_region = (selected_region == "TODAS") or (region == selected_region)

                if match_text and match_region:
                    tree.insert("", "end", values=(item[0], item[1], item[2], item[3], item[4]), tags=(item[5],))

        self.update_summary_count()

    def start_download(self, tree, category):
        selected_items = tree.selection()
        if not selected_items:
            messagebox.showwarning("Atención", "Por favor selecciona uno o varios elementos para descargar.")
            return

        target_dir = CARPETAS[category]

        for item_id in selected_items:
            item_values = tree.item(item_id)['values']
            tags = tree.item(item_id)['tags']
            
            name = item_values[2]
            version = item_values[3]
            raw_url = tags[0]

            clean_title = sanitize_filename(name)
            
            if version and version.lower() not in ["base", "n/a", "none"]:
                custom_filename = f"{clean_title} {version}.pkg"
            else:
                custom_filename = f"{clean_title}.pkg"

            dest_path = os.path.join(target_dir, custom_filename)
            counter = 1
            base_name, ext = os.path.splitext(dest_path)
            while os.path.exists(dest_path):
                dest_path = f"{base_name} ({counter}){ext}"
                counter += 1

            clean_url = re.sub(r'(\.pkg)\d+$', r'\1', raw_url, flags=re.IGNORECASE)

            threading.Thread(
                target=self._requests_fast_download, 
                args=(clean_url, dest_path, clean_title), 
                daemon=True
            ).start()

    def download_rap(self):
        filename = os.path.join(CARPETAS["RAP"], "License_Pack_31.153.pkg")
        threading.Thread(
            target=self._requests_fast_download, 
            args=(GITHUB_RAP_URL, filename, "Licencias (31.153 .pkg)"), 
            daemon=True
        ).start()

    def _requests_fast_download(self, url, dest_path, title):
        """
        Motor de descarga Ultra-Turbo con 16 hilos simultáneos y huella de navegador web de alta gama.
        """
        try:
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'identity',
                'Connection': 'keep-alive',
                'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache'
            })

            head_res = session.head(url, allow_redirects=True, timeout=10)
            total_size = int(head_res.headers.get('content-length', 0))
            accept_ranges = head_res.headers.get('accept-ranges', '').lower()

            if total_size <= 0 or 'bytes' not in accept_ranges:
                self._single_thread_download(session, url, dest_path, title, total_size)
                return

            num_threads = 16
            chunk_size = total_size // num_threads
            lock = threading.Lock()
            downloaded_bytes = [0] * num_threads
            
            with open(dest_path, 'wb') as f:
                f.truncate(total_size)

            def download_part(thread_id, start, end):
                nonlocal downloaded_bytes
                headers = {'Range': f'bytes={start}-{end}'}
                try:
                    with session.get(url, headers=headers, stream=True, timeout=20) as r:
                        r.raise_for_status()
                        current_pos = start
                        with open(dest_path, 'r+b') as f:
                            f.seek(current_pos)
                            for chunk in r.iter_content(chunk_size=131072):
                                if chunk:
                                    f.write(chunk)
                                    current_pos += len(chunk)
                                    with lock:
                                        downloaded_bytes[thread_id] = current_pos - start
                except Exception as e:
                    print(f"Error en hilo {thread_id}: {e}")

            start_time = time.time()
            last_time = start_time
            last_total_downloaded = 0

            threads = []
            for i in range(num_threads):
                start = i * chunk_size
                end = (total_size - 1) if i == num_threads - 1 else (start + chunk_size - 1)
                t = threading.Thread(target=download_part, args=(i, start, end), daemon=True)
                threads.append(t)
                t.start()

            while any(t.is_alive() for t in threads):
                time.sleep(0.2)
                with lock:
                    current_total = sum(downloaded_bytes)
                
                now = time.time()
                elapsed = now - last_time
                if elapsed >= 0.2:
                    speed = (current_total - last_total_downloaded) / elapsed
                    speed_str = format_speed(speed)
                    percent = current_total / total_size if total_size > 0 else 0
                    
                    self.progress_bar.set(min(1.0, percent))
                    display_filename = os.path.basename(dest_path)
                    self.status_label.configure(
                        text=f"Descargando (Turbo 16H): {display_filename}... [{speed_str}]"
                    )

                    last_total_downloaded = current_total
                    last_time = now

            for t in threads:
                t.join()

            self.progress_bar.set(1.0)
            self.status_label.configure(text=f"✅ Finalizado: {os.path.basename(dest_path)}")

        except Exception as e:
            self.status_label.configure(text="❌ Error en la descarga")
            messagebox.showerror("Error de Descarga", f"No se pudo descargar {title}:\n{e}")

    def _single_thread_download(self, session, url, dest_path, title, total_size):
        start_time = time.time()
        last_time = start_time
        downloaded_bytes = 0
        last_bytes = 0

        with session.get(url, stream=True, timeout=15) as response:
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)

                        now = time.time()
                        elapsed = now - last_time
                        if elapsed >= 0.2:
                            speed = (downloaded_bytes - last_bytes) / elapsed
                            speed_str = format_speed(speed)
                            
                            if total_size > 0:
                                self.progress_bar.set(min(1.0, downloaded_bytes / total_size))

                            self.status_label.configure(
                                text=f"Descargando: {os.path.basename(dest_path)}... [{speed_str}]"
                            )
                            last_bytes = downloaded_bytes
                            last_time = now

        self.progress_bar.set(1.0)
        self.status_label.configure(text=f"✅ Finalizado: {os.path.basename(dest_path)}")


if __name__ == "__main__":
    app = PS3DownloaderApp()
    app.mainloop()