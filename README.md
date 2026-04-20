# 🎧 MetaMusicExtract

> Extrae y exporta los metadatos de tus archivos de música a Excel con un solo clic.

![Splash](splash_metadata_audio.png)

---

## ¿Qué es MetaMusicExtract?

**MetaMusicExtract** es una aplicación de escritorio para Windows que escanea carpetas de música, lee los metadatos de tus archivos de audio (título, artista, álbum, género, año...) y los exporta a un archivo Excel listo para usar.

Ideal para gestionar bibliotecas musicales grandes, auditar colecciones o simplemente tener tus metadatos organizados.

---

## Características

- 📁 Escaneo recursivo de carpetas (incluye subcarpetas)
- 🎵 Compatible con los formatos más comunes: `.mp3`, `.flac`, `.m4a`, `.ogg`
- 🏷️ Extrae metadatos ID3 (MP3) y Vorbis/FLAC: título, artista, álbum, artista del álbum, fecha, nº de pista, género, comentarios, URLs y más
- ☑️ Selección granular de campos a exportar mediante checkboxes
- 📊 Exportación directa a `.xlsx` con nombres de columna humanizados
- 🌙 Interfaz con tema oscuro (Sun Valley Dark)
- 💻 Ejecutable único `.exe` sin necesidad de instalar Python

---

## Uso

1. Abre `MetaMusicExtract.exe`
2. Haz clic en **"Selecciona la carpeta a escanear"** y elige tu carpeta de música
3. Espera a que el escaneo termine (se mostrará el número de archivos y metadatos encontrados)
4. Marca o desmarca los campos que quieras incluir en el Excel
5. Haz clic en **"Exportar a Excel"** y elige dónde guardar el archivo

El archivo resultante se llamará `metadata_music_<nombre_carpeta>.xlsx` por defecto.

---

## 📦 Formatos y metadatos soportados

| Formato | Estándar de tags |
|---------|-----------------|
| `.mp3`  | ID3 (TIT2, TPE1, TALB, TDRC, TCON...) |
| `.flac` | Vorbis Comment (title, artist, album, date...) |
| `.m4a`  | iTunes Tags |
| `.ogg`  | Vorbis Comment |

---

## Compilación desde código fuente

El proyecto usa **[auto-py-to-exe](https://github.com/brentvollebregt/auto-py-to-exe)** para generar el ejecutable. Parámetros de compilación:

| Parámetro | Valor |
|-----------|-------|
| **Script** | `import_metadata_audio.py` |
| **Modo** | One File |
| **Icono** | `music_metadata.ico` |
| **Nombre** | `MetaMusicExtract` |
| **Splash** | `splash_metadata_audio.png` |

### Dependencias Python

```
mutagen
pandas
openpyxl
sv-ttk
```

Instálalas con:

```bash
pip install mutagen pandas openpyxl sv-ttk
```

---

## Estructura del proyecto

```
MetaMusicExtract/
├── import_metadata_audio.py   # Script principal
├── music_metadata.ico         # Icono de la aplicación
├── splash_metadata_audio.png  # Pantalla de carga
└── output/
    └── MetaMusicExtract.exe   # Ejecutable compilado
```

---

## Requisitos

- **Windows** (el `.exe` compilado es para Windows)
- Para ejecutar desde código fuente: Python 3.8+

---

## Licencia

Este proyecto está licenciado bajo Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
Puedes copiar, modificar y distribuir este proyecto siempre que:

- Des crédito al autor original
- No lo uses con fines comerciales

Consulta el archivo `LICENSE` para más detalles.
