import os
import pandas as pd
from mutagen import File
import tkinter as tk
from tkinter import filedialog, messagebox


def seleccionar_carpeta():
    """Abre un diálogo para seleccionar la carpeta a escanear."""
    return filedialog.askdirectory(title="Selecciona la carpeta de música a escanear")


def seleccionar_salida_excel(carpeta_origen):
    """
    Abre un diálogo para seleccionar el Excel de salida.
    Si el usuario cancela, genera un nombre por defecto:
    metadata_music_<foldername>.xlsx (sin espacios en foldername).
    """
    # Nombre de la carpeta (último segmento de la ruta)
    foldername = os.path.basename(carpeta_origen.rstrip(r"\/"))
    foldername_sin_espacios = foldername.replace(" ", "")

    # Sugerencia de nombre de archivo
    nombre_por_defecto = f"metadata_music_{foldername_sin_espacios}.xlsx"

    ruta_seleccionada = filedialog.asksaveasfilename(
        title="Selecciona el archivo Excel de salida (o pulsa Cancelar para usar el nombre por defecto)",
        defaultextension=".xlsx",
        initialfile=nombre_por_defecto,
        filetypes=[("Archivos de Excel", "*.xlsx"), ("Todos los archivos", "*.*")]
    )

    # Si el usuario cancela, usamos el nombre por defecto en la misma carpeta de origen
    if not ruta_seleccionada:
        ruta_seleccionada = os.path.join(carpeta_origen, nombre_por_defecto)

    return ruta_seleccionada


def extraer_metadatos(carpeta):
    """Recorre la carpeta y extrae metadatos de los ficheros de audio compatibles."""
    datos = []

    for root, dirs, files in os.walk(carpeta):
        for f in files:
            if f.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg')):
                full = os.path.join(root, f)
                audio = File(full)
                if audio and audio.tags:
                    tags = audio.tags
                    datos.append({
                        "Archivo": f,
                        "Ruta": full,
                        "Título": str(tags.get("TIT2", [""])[0]) if "TIT2" in tags else "",
                        "Artista": str(tags.get("TPE1", [""])[0]) if "TPE1" in tags else "",
                        "Álbum":   str(tags.get("TALB", [""])[0]) if "TALB" in tags else "",
                        "Año":     str(tags.get("TDRC", [""])[0]) if "TDRC" in tags else "",
                    })

    return datos


def main():
    # Iniciar Tkinter en modo oculto (solo diálogos)
    root = tk.Tk()
    root.withdraw()

    # 1) Seleccionar carpeta
    carpeta = seleccionar_carpeta()
    if not carpeta:
        messagebox.showinfo("Cancelado", "No se ha seleccionado ninguna carpeta. El programa se cerrará.")
        return

    # 2) Seleccionar (o generar) archivo de salida
    ruta_excel = seleccionar_salida_excel(carpeta)

    # 3) Extraer metadatos
    datos = extraer_metadatos(carpeta)

    if not datos:
        messagebox.showwarning("Sin datos", "No se han encontrado archivos de audio compatibles en la carpeta seleccionada.")
        return

    # 4) Crear DataFrame y exportar
    df = pd.DataFrame(datos)
    print(df)  # Para ver el resultado en consola si ejecutas desde VS Code / terminal

    df.to_excel(ruta_excel, index=False)

    messagebox.showinfo("Proceso completado", f"Metadatos exportados correctamente a:\n{ruta_excel}")


if __name__ == "__main__":
    main()

