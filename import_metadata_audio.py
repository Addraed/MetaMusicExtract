import os
import datetime
import pandas as pd
from mutagen import File

import tkinter as tk
from tkinter import filedialog, messagebox


AUDIO_EXTS = ('.mp3', '.flac', '.m4a', '.ogg')


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

        # Dict campo -> BooleanVar (checkbox)
        self.field_vars = {}

        # UI
        self._build_ui()

    def _build_ui(self):
        frame_top = tk.Frame(self.root, padx=10, pady=10)
        frame_top.pack(fill="x")

        btn_sel_carpeta = tk.Button(frame_top, text="1) Seleccionar carpeta y escanear",
                                    command=self.on_seleccionar_carpeta)
        btn_sel_carpeta.pack(side="left")

        self.lbl_carpeta = tk.Label(frame_top, text="Carpeta: (ninguna seleccionada)")
        self.lbl_carpeta.pack(side="left", padx=10)

        # Frame para checkboxes
        self.frame_campos = tk.Frame(self.root, padx=10, pady=10)
        self.frame_campos.pack(fill="both", expand=True)

        # Botón exportar
        frame_bottom = tk.Frame(self.root, padx=10, pady=10)
        frame_bottom.pack(fill="x")

        btn_exportar = tk.Button(frame_bottom, text="2) Exportar a Excel", command=self.on_exportar)
        btn_exportar.pack(side="right")

    def on_seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta de música a escanear")
        if not carpeta:
            return

        self.carpeta_origen = carpeta
        self.lbl_carpeta.config(text=f"Carpeta: {carreta_truncada(carpeta)}")

        # Escanear
        self.data_rows, music_fields_set = self.scan_folder(carpeta)

        if not self.data_rows:
            messagebox.showwarning("Sin datos",
                                   "No se han encontrado archivos de audio compatibles en la carpeta seleccionada.")
            return

        # Actualizar lista de campos musicales detectados
        self.music_fields = sorted(music_fields_set)

        # Reconstruir checkboxes
        self.build_checkboxes()

        messagebox.showinfo("Escaneo completado",
                            f"Se han encontrado {len(self.data_rows)} archivos de audio.\n"
                            f"Metadatos musicales distintos detectados: {len(self.music_fields)}")

    def scan_folder(self, carpeta):
        """
        Recorre la carpeta y subcarpetas, arma filas con:
        - Campos básicos: Archivo, Ruta, Tamaño, Fecha_modificación
        - Metadatos musicales: todas las claves encontradas en audio.tags
        Devuelve (lista_de_diccionarios, conjunto_de_claves_musicales)
        """
        datos = []
        music_fields = set()

        for root, dirs, files in os.walk(carpeta):
            for f in files:
                if not f.lower().endswith(AUDIO_EXTS):
                    continue

                full = os.path.join(root, f)

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
                    # Hay varios tipos de objetos, pero casi todos exponen items()
                    try:
                        items_iter = tags.items()
                    except Exception:
                        items_iter = []

                    for key, value in items_iter:
                        text = self._value_to_text(value)
                        row[str(key)] = text
                        music_fields.add(str(key))

                datos.append(row)

        return datos, music_fields

    @staticmethod
    def _value_to_text(value):
        """
        Convierte un valor de tag (ID3Frame, lista, etc.) a texto plano.
        """
        # ID3 frames suelen tener .text
        if hasattr(value, "text"):
            try:
                return ", ".join(str(v) for v in value.text)
            except Exception:
                return str(value)

        # Vorbis / FLAC: listas de strings
        if isinstance(value, (list, tuple, set)):
            try:
                return ", ".join(str(v) for v in value)
            except Exception:
                return str(value)

        # Fallback
        return str(value)

    def build_checkboxes(self):
        # Limpiar frame de campos
        for child in self.frame_campos.winfo_children():
            child.destroy()

        self.field_vars.clear()

        # Sección de campos básicos
        lbl_basicos = tk.Label(self.frame_campos, text="Campos básicos", font=("Segoe UI", 10, "bold"))
        lbl_basicos.pack(anchor="w")

        frame_basicos = tk.Frame(self.frame_campos)
        frame_basicos.pack(fill="x", pady=(0, 10))

        for field in self.basic_fields:
            var = tk.BooleanVar(value=True)  # por defecto incluidos
            chk = tk.Checkbutton(frame_basicos, text=field, variable=var)
            chk.pack(anchor="w")
            self.field_vars[field] = var

        # Sección de metadatos musicales
        lbl_musicales = tk.Label(self.frame_campos, text="Metadatos musicales detectados",
                                 font=("Segoe UI", 10, "bold"))
        lbl_musicales.pack(anchor="w")

        frame_musicales = tk.Frame(self.frame_campos)
        frame_musicales.pack(fill="both", expand=True)

        # Scroll por si hay muchos metadatos
        canvas = tk.Canvas(frame_musicales)
        scrollbar = tk.Scrollbar(frame_musicales, orient="vertical", command=canvas.yview)
        inner_frame = tk.Frame(canvas)

        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for field in self.music_fields:
            # Por defecto marcamos algunos típicos si existen
            default_on = field.upper() in ("TIT2", "TPE1", "TALB", "TDRC", "DATE", "ALBUM", "ARTIST", "TITLE")
            var = tk.BooleanVar(value=default_on)
            chk = tk.Checkbutton(inner_frame, text=field, variable=var)
            chk.pack(anchor="w")
            self.field_vars[field] = var

    def on_exportar(self):
        if not self.data_rows:
            messagebox.showwarning("Sin datos", "Primero selecciona una carpeta y realiza el escaneo.")
            return

        # Qué campos ha seleccionado el usuario
        selected_fields = [campo for campo, var in self.field_vars.items() if var.get()]

        if not selected_fields:
            messagebox.showwarning("Sin campos", "No has seleccionado ningún campo para exportar.")
            return

        # Construir DataFrame y filtrar a las columnas seleccionadas
        df = pd.DataFrame(self.data_rows)

        # Algunos campos seleccionados pueden no existir en todas las filas → usamos .reindex
        df = df.reindex(columns=selected_fields)

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
            # Si el usuario cancela, guardamos en la carpeta de origen o en cwd
            carpeta = self.carpeta_origen if self.carpeta_origen else os.getcwd()
            ruta_seleccionada = os.path.join(carpeta, nombre_por_defecto)

        return ruta_seleccionada


def carreta_truncada(path, max_len=60):
    """Trunca rutas largas para mostrarlas en la etiqueta."""
    if len(path) <= max_len:
        return path
    else:
        return "..." + path[-(max_len - 3):]


def main():
    root = tk.Tk()
    app = MetadataApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
