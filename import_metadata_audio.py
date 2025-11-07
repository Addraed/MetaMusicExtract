import os
import datetime
import pandas as pd
from mutagen import File

import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


AUDIO_EXTS = ('.mp3', '.flac', '.m4a', '.ogg')

# Mapeo de claves de metadatos -> nombre “bonito” para UI/Excel
FRAME_HUMAN_MAP = {
    # ID3 típicos
    "TIT2": "Título",
    "TPE1": "Artista",
    "TALB": "Álbum",
    "TPE2": "Artista del álbum / Banda",
    "TDRC": "Fecha de grabación",
    "TYER": "Año",
    "TRCK": "Nº de pista",
    "TCON": "Género",
    "COMM": "Comentario",
    "WOAS": "URL origen del audio",
    "WXXX": "URL personalizada",
    "APIC": "Carátula",

    # Vorbis/FLAC típicos (lowercase)
    "title": "Título",
    "artist": "Artista",
    "album": "Álbum",
    "albumartist": "Artista del álbum",
    "date": "Fecha",
    "tracknumber": "Nº de pista",
    "genre": "Género",
    "comment": "Comentario",
}

# Algunos ID3 que queremos mostrar aunque no aparezcan en todos los archivos
KNOWN_ID3_KEYS = [
    "TIT2", "TPE1", "TALB", "TPE2",
    "TDRC", "TYER", "TRCK", "TCON",
    "COMM", "WOAS", "WXXX", "APIC",
]


def get_base_tag_key(tag_key: str) -> str:
    """
    Para claves tipo 'APIC:Cover' devolvemos 'APIC'.
    Para otras, se mantiene tal cual.
    """
    if ":" in tag_key:
        return tag_key.split(":", 1)[0]
    return tag_key


def get_friendly_name(tag_key: str) -> str:
    """
    Devuelve el nombre humanizado de una clave de metadato,
    o la propia clave si no tenemos mapeo.
    """
    base = get_base_tag_key(tag_key)
    return FRAME_HUMAN_MAP.get(base, FRAME_HUMAN_MAP.get(tag_key, tag_key))


def header_for_excel(tag_key: str) -> str:
    """
    Nombre de columna final para Excel: 'Título (TIT2)' por ejemplo,
    para no perder la referencia a la clave original.
    Si no hay mapeo, devuelve simplemente la clave.
    """
    friendly = get_friendly_name(tag_key)
    if friendly == tag_key:
        return tag_key
    return f"{friendly} ({tag_key})"


class MetadataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Extractor de metadatos de música")

        # Datos escaneados
        self.data_rows = []
        self.carpeta_origen = None

        # Campos disponibles
        self.basic_fields = ["Archivo", "Ruta", "Tamaño", "Fecha_modificación"]
        self.music_fields = []  # se rellenará tras el escaneo

        # Dict clave_real -> BooleanVar (checkbox)
        self.field_vars = {}

        # UI
        self._build_ui()

    def _build_ui(self):
        frame_top = ttk.Frame(self.root, padding=10)
        frame_top.pack(fill="x")

        btn_sel_carpeta = ttk.Button(
            frame_top,
            text="1) Seleccionar carpeta y escanear",
            command=self.on_seleccionar_carpeta
        )
        btn_sel_carpeta.pack(side="left")

        self.lbl_carpeta = ttk.Label(frame_top, text="Carpeta: (ninguna seleccionada)")
        self.lbl_carpeta.pack(side="left", padx=10)

        # Frame para checkboxes
        self.frame_campos = ttk.Frame(self.root, padding=10)
        self.frame_campos.pack(fill="both", expand=True)

        # Botón exportar
        frame_bottom = ttk.Frame(self.root, padding=10)
        frame_bottom.pack(fill="x")

        btn_exportar = ttk.Button(frame_bottom, text="2) Exportar a Excel", command=self.on_exportar)
        btn_exportar.pack(side="right")

    def on_seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta de música a escanear")
        if not carpeta:
            return

        self.carpeta_origen = carpeta
        self.lbl_carpeta.config(text=f"Carpeta: {ruta_truncada(carpeta)}")

        # Escanear
        self.data_rows, music_fields_set = self.scan_folder(carpeta)

        if not self.data_rows:
            messagebox.showwarning(
                "Sin datos",
                "No se han encontrado archivos de audio compatibles en la carpeta seleccionada."
            )
            return

        # Añadimos los ID3 conocidos aunque no se hayan visto en los archivos
        music_fields_set.update(KNOWN_ID3_KEYS)

        # Actualizar lista de campos musicales detectados
        self.music_fields = sorted(music_fields_set)

        # Reconstruir checkboxes
        self.build_checkboxes()

        messagebox.showinfo(
            "Escaneo completado",
            f"Se han encontrado {len(self.data_rows)} archivos de audio.\n"
            f"Metadatos musicales distintos detectados: {len(self.music_fields)}"
        )

    def scan_folder(self, carpeta):
        """
        Recorre la carpeta y subcarpetas, arma filas con:
        - Campos básicos: Archivo, Ruta, Tamaño, Fecha_modificación
        - Metadatos musicales: todas las claves encontradas en audio.tags
        Devuelve (lista_de_diccionarios, conjunto_de_claves_musicales)
        """
        datos = []
        music_fields = set()

        for root_dir, dirs, files in os.walk(carpeta):
            for f in files:
                if not f.lower().endswith(AUDIO_EXTS):
                    continue

                full = os.path.join(root_dir, f)

                row = {
                    "Archivo": f,
                    "Ruta": full,
                }

                try:
                    st = os.stat(full)
                    row["Tamaño"] = st.st_size
                    row["Fecha_modificación"] = datetime.datetime.fromtimestamp(
                        st.st_mtime
                    ).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    row["Tamaño"] = None
                    row["Fecha_modificación"] = None

                # Extraer metadatos musicales con mutagen
                try:
                    audio = File(full)
                except Exception:
                    audio = None

                if audio is not None and audio.tags:
                    tags = audio.tags
                    try:
                        items_iter = tags.items()
                    except Exception:
                        items_iter = []

                    for key, value in items_iter:
                        key_str = str(key)
                        # Evitar volcar binarios de carátulas: APIC → ponemos una marca simbólica
                        base = get_base_tag_key(key_str)
                        if base == "APIC":
                            row[key_str] = "[Imagen de carátula]"
                        else:
                            text = self._value_to_text(value)
                            row[key_str] = text
                        music_fields.add(key_str)

                datos.append(row)

        return datos, music_fields

    @staticmethod
    def _value_to_text(value):
        """
        Convierte un valor de tag (ID3Frame, lista, etc.) a texto plano.
        """
        if hasattr(value, "text"):
            try:
                return ", ".join(str(v) for v in value.text)
            except Exception:
                return str(value)

        if isinstance(value, (list, tuple, set)):
            try:
                return ", ".join(str(v) for v in value)
            except Exception:
                return str(value)

        return str(value)

    def build_checkboxes(self):
        # Limpiar frame de campos
        for child in self.frame_campos.winfo_children():
            child.destroy()

        self.field_vars.clear()

        # Sección de campos básicos
        lbl_basicos = ttk.Label(
            self.frame_campos,
            text="Campos básicos",
            font=("Segoe UI", 10, "bold")
        )
        lbl_basicos.pack(anchor="w")

        frame_basicos = ttk.Frame(self.frame_campos)
        frame_basicos.pack(fill="x", pady=(0, 10))

        for field in self.basic_fields:
            var = tk.BooleanVar(value=True)  # por defecto incluidos
            chk = ttk.Checkbutton(frame_basicos, text=field, variable=var)
            chk.pack(anchor="w")
            self.field_vars[field] = var

        # Sección de metadatos musicales
        lbl_musicales = ttk.Label(
            self.frame_campos,
            text="Metadatos musicales detectados",
            font=("Segoe UI", 10, "bold")
        )
        lbl_musicales.pack(anchor="w")

        frame_musicales = ttk.Frame(self.frame_campos)
        frame_musicales.pack(fill="both", expand=True)

        # Scroll por si hay muchos metadatos
        canvas = tk.Canvas(frame_musicales, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame_musicales, orient="vertical", command=canvas.yview)
        inner_frame = ttk.Frame(canvas)

        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for key in self.music_fields:
            friendly = get_friendly_name(key)
            label_text = f"{friendly} [{key}]" if friendly != key else key

            # Activamos por defecto los típicos "bonitos"
            base = get_base_tag_key(key).upper()
            default_on = base in ("TIT2", "TPE1", "TALB", "TDRC", "TYER", "TRCK", "TCON") \
                         or key.lower() in ("title", "artist", "album", "date", "tracknumber", "genre")

            var = tk.BooleanVar(value=default_on)
            chk = ttk.Checkbutton(inner_frame, text=label_text, variable=var)
            chk.pack(anchor="w")
            self.field_vars[key] = var

    def on_exportar(self):
        if not self.data_rows:
            messagebox.showwarning("Sin datos", "Primero selecciona una carpeta y realiza el escaneo.")
            return

        # Qué campos ha seleccionado el usuario
        selected_basic = [f for f in self.basic_fields if self.field_vars.get(f, tk.BooleanVar(False)).get()]
        selected_music = [k for k in self.music_fields if self.field_vars.get(k, tk.BooleanVar(False)).get()]

        selected_fields = selected_basic + selected_music

        if not selected_fields:
            messagebox.showwarning("Sin campos", "No has seleccionado ningún campo para exportar.")
            return

        # Construir DataFrame
        df = pd.DataFrame(self.data_rows)

        # Asegurarnos de que todas las columnas seleccionadas existen (aunque sea vacías)
        for col in selected_fields:
            if col not in df.columns:
                df[col] = None

        df = df[selected_fields]

        # Renombrar columnas musicales a nombres humanizados
        renames = {}
        for col in selected_music:
            renames[col] = header_for_excel(col)
        # Campos básicos los dejamos tal cual
        df = df.rename(columns=renames)

        # Seleccionar/decidir Excel de salida
        ruta_excel = self.seleccionar_salida_excel()

        try:
            df.to_excel(ruta_excel, index=False)
        except Exception as e:
            messagebox.showerror("Error al guardar", f"No se pudo guardar el Excel:\n{e}")
            return

        messagebox.showinfo("Exportación completada", f"Metadatos exportados a:\n{ruta_excel}")

    def seleccionar_salida_excel(self):
        """
        Pide al usuario un Excel de salida. Si se cancela,
        usa metadata_music_<foldername>.xlsx en la carpeta origen,
        con foldername sin espacios.
        """
        if self.carpeta_origen:
            foldername = os.path.basename(self.carpeta_origen.rstrip(r"\/"))
        else:
            foldername = "output"

        foldername_sin_espacios = foldername.replace(" ", "")
        nombre_por_defecto = f"metadata_music_{foldername_sin_espacios}.xlsx"

        ruta_seleccionada = filedialog.asksaveasfilename(
            title="Selecciona el archivo Excel de salida (o pulsa Cancelar para usar el nombre por defecto)",
            defaultextension=".xlsx",
            initialfile=nombre_por_defecto,
            filetypes=[("Archivos de Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
        )

        if not ruta_seleccionada:
            carpeta = self.carpeta_origen if self.carpeta_origen else os.getcwd()
            ruta_seleccionada = os.path.join(carpeta, nombre_por_defecto)

        return ruta_seleccionada


def ruta_truncada(path, max_len=60):
    """Trunca rutas largas para mostrarlas en la etiqueta."""
    if len(path) <= max_len:
        return path
    else:
        return "..." + path[-(max_len - 3):]


def aplicar_tema_sun_valley(root):
    """
    Intenta cargar el tema Sun Valley (sun-valley.tcl).
    Si falla, simplemente usa el tema por defecto.
    """
    try:
        root.tk.call("source", "sun-valley.tcl")
        style = ttk.Style(root)
        # Puedes cambiar a "sun-valley-light" si prefieres claro
        style.theme_use("sun-valley-dark")
    except Exception as e:
        print("No se pudo cargar el tema Sun Valley:", e)


def main():
    root = tk.Tk()
    aplicar_tema_sun_valley(root)
    app = MetadataApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
