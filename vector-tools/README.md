# Vector Tools - Procesador de Documentos

Esta herramienta permite procesar documentos PDF desde Google Drive o desde el sistema de archivos local, extrayendo su contenido, generando embeddings, y almacenándolos en una base de datos vectorizada de Supabase.

## Configuración

1. El script utiliza las credenciales de Supabase que ya están configuradas en el archivo `.env` en la raíz del proyecto:
   ```
   SUPABASE_URL=https://somsshavzjkkdarfmrom.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. Para procesar documentos desde Google Drive, añade la siguiente variable al archivo `.env` en la raíz del proyecto:
   ```
   DRIVE_FOLDER_ID=your-drive-folder-id  # ID de la carpeta en Google Drive
   ```

3. Para usar Google Drive, necesitas configurar la autenticación:
   - Crea un proyecto en la [Google Cloud Console](https://console.cloud.google.com/)
   - Habilita la API de Google Drive
   - Crea credenciales OAuth 2.0 para una aplicación de escritorio
   - Descarga el archivo JSON de credenciales y guárdalo como `credentials.json` en la carpeta `vector-tools`

## Uso

Ejecuta el script principal:

```bash
cd vector-tools
python process_docs.py
```

El script realizará las siguientes acciones:

1. Si `DRIVE_FOLDER_ID` está configurado en el archivo `.env`:
   - Descargará todos los archivos PDF de la carpeta especificada en Google Drive
   - Procesará cada archivo, dividiendo el texto en chunks con solapamiento
   - Generará embeddings para cada chunk utilizando el modelo `all-MiniLM-L6-v2`
   - Almacenará los chunks y embeddings en la tabla `documents` de Supabase

2. Si `DRIVE_FOLDER_ID` no está configurado:
   - Procesará todos los archivos PDF en la carpeta `documents` del proyecto

## Estructura de Datos en Supabase

Los documentos se almacenan en la tabla `documents` con la siguiente estructura:

- `content`: El texto del chunk
- `metadata`: JSON con información sobre el documento (fuente, ruta, índice del chunk, etc.)
- `embedding`: Vector de embeddings generado por sentence-transformers

## Funcionalidades Adicionales

- `semantic_search`: Permite realizar búsquedas semánticas en la base de datos de documentos

## Requisitos

Ver `requirements.txt` en la raíz del proyecto para las dependencias. 