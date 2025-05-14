import os
import json
import sys
from typing import List, Dict, Any, Optional, Tuple
import io
import PyPDF2
from supabase import create_client
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import logging
from dotenv import load_dotenv
import re
import tempfile
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ruta al archivo .env en la raíz del proyecto
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

# Forzar la recarga de variables de entorno
load_dotenv(dotenv_path=dotenv_path, override=True)

# Configuración de Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set as environment variables")

supabase = create_client(supabase_url, supabase_key)

# Importar el diccionario de productos bancarios
try:
    from productos_bancarios import PRODUCTOS_BANCARIOS
    logger.info(f"Diccionario de productos bancarios cargado: {len(PRODUCTOS_BANCARIOS)} productos")
except ImportError:
    logger.warning("No se pudo importar PRODUCTOS_BANCARIOS desde productos_bancarios.py")
    PRODUCTOS_BANCARIOS = {}

# Inicializar el modelo de embeddings de sentence-transformers
model = SentenceTransformer("all-MiniLM-L6-v2")
logger.info("Modelo de embeddings cargado: all-MiniLM-L6-v2")

# Configuración para Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'service-account.json')

def get_drive_service():
    """Autentica y devuelve un servicio de Google Drive usando service account."""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Error building Drive service: {str(e)}")
        raise

def list_drive_files(service, folder_id=None, mime_type=None):
    """Lista archivos en Drive, opcionalmente filtrando por carpeta y tipo MIME."""
    query_parts = []
    
    if folder_id:
        query_parts.append(f"'{folder_id}' in parents")
    
    if mime_type:
        query_parts.append(f"mimeType='{mime_type}'")
    else:
        # Por defecto, excluir carpetas
        query_parts.append("mimeType!='application/vnd.google-apps.folder'")
    
    # Archivos que no están en la papelera
    query_parts.append("trashed=false")
    
    query = " and ".join(query_parts)
    
    try:
        results = []
        page_token = None
        while True:
            response = service.files().list(
                q=query,
                spaces='drive',
                fields='nextPageToken, files(id, name, mimeType, parents)',
                pageToken=page_token
            ).execute()
            
            results.extend(response.get('files', []))
            page_token = response.get('nextPageToken')
            
            if not page_token:
                break
        
        return results
    except Exception as e:
        logger.error(f"Error listing Drive files: {str(e)}")
        return []

def download_drive_file(service, file_id, file_name):
    """Descarga un archivo de Google Drive."""
    try:
        request = service.files().get_media(fileId=file_id)
        
        # Crear un archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='_' + file_name) as temp_file:
            downloader = MediaIoBaseDownload(temp_file, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Downloading {file_name}: {int(status.progress() * 100)}%")
            
            return temp_file.name
    except Exception as e:
        logger.error(f"Error downloading file {file_name} (ID: {file_id}): {str(e)}")
        return None

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae el texto de un archivo PDF."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Divide el texto en chunks con overlap."""
    if not text:
        return []
    
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) > chunk_size / 2:  # Evitar chunks muy pequeños
            chunks.append(chunk)
    return chunks

def generate_embedding(text: str) -> List[float]:
    """Genera embedding para un texto usando sentence-transformers."""
    try:
        embedding = model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generando embedding con sentence-transformers: {str(e)}")
        return []

def limpiar_texto(texto: str) -> str:
    # Une palabras separadas por saltos de línea o espacios extraños
    texto = re.sub(r'(\w)\s+\n\s*(\w)', r'\1 \2', texto)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    texto = texto.strip()
    return texto

def process_pdf_directory(directory_path: str, chunk_size: int = 1000, overlap: int = 200) -> None:
    """Procesa todos los PDFs en un directorio y sus subdirectorios."""
    for root, _, files in os.walk(directory_path):
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        for filename in tqdm(pdf_files, desc=f"Processing {root}"):
            file_path = os.path.join(root, filename)
            try:
                process_pdf(file_path, chunk_size, overlap)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

def process_pdf(pdf_path: str, chunk_size: int = 1000, overlap: int = 200, category: str = None) -> None:
    """Procesa un solo PDF y lo guarda en Supabase."""
    # Extraer texto del PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        logger.warning(f"No text extracted from {pdf_path}")
        return
    
    # Dividir en chunks
    chunks = chunk_text(text, chunk_size, overlap)
    
    # Metadata básica
    base_metadata = {
        "source": os.path.basename(pdf_path),
        "path": pdf_path,
        "total_chunks": len(chunks),
        "category": category or os.path.basename(os.path.dirname(pdf_path))  # Añade la categoría del documento
    }
    
    # Procesar y guardar cada chunk
    for i, chunk in enumerate(chunks):
        try:
            chunk_limpio = limpiar_texto(chunk)
            metadata = {**base_metadata, "chunk_index": i}
            embedding = generate_embedding(chunk_limpio)
            
            if not embedding:
                logger.warning(f"Could not generate embedding for chunk {i} in {pdf_path}")
                continue
            
            # Insertar en Supabase
            response = supabase.table("documents").insert({
                "content": chunk_limpio,
                "metadata": metadata,
                "embedding": embedding
            }).execute()
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Error inserting chunk {i} from {pdf_path}: {response.error}")
                
        except Exception as e:
            logger.error(f"Error processing chunk {i} from {pdf_path}: {str(e)}")
    
    logger.info(f"Procesado: {pdf_path} - {len(chunks)} chunks")

def process_drive_files(drive_folder_id: str = None, chunk_size: int = 1000, overlap: int = 200) -> None:
    """Procesa archivos PDF desde Google Drive, incluyendo subcarpetas."""
    try:
        # Obtener servicio de Drive
        service = get_drive_service()
        
        # Lista para almacenar todos los PDFs encontrados
        all_pdfs = []
        
        # Función recursiva para buscar PDFs en carpetas y subcarpetas
        def search_pdfs_recursive(folder_id, path="/"):
            # Listar todos los archivos en esta carpeta
            items = list_drive_files(service, folder_id=folder_id)
            
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Es una carpeta, buscar recursivamente
                    folder_name = item['name']
                    logger.info(f"Explorando subcarpeta: {path}{folder_name}/")
                    search_pdfs_recursive(item['id'], path=f"{path}{folder_name}/")
                elif item['mimeType'] == 'application/pdf':
                    # Es un PDF, añadirlo a la lista
                    item['path'] = path
                    all_pdfs.append(item)
                    logger.info(f"PDF encontrado: {path}{item['name']}")
        
        # Iniciar búsqueda recursiva en la carpeta principal
        search_pdfs_recursive(drive_folder_id)
        
        # Si no se encontraron PDFs en la carpeta principal, intentar con todas las carpetas de productos
        if not all_pdfs and PRODUCTOS_BANCARIOS:
            logger.info("No se encontraron PDFs en la carpeta principal. Procesando carpetas de productos bancarios...")
            for producto, folder_id in PRODUCTOS_BANCARIOS.items():
                logger.info(f"Procesando producto: {producto} (Folder ID: {folder_id})")
                search_pdfs_recursive(folder_id, path=f"/{producto}/")
        
        if not all_pdfs:
            logger.warning(f"No se encontraron archivos PDF en ninguna carpeta")
            return
        
        logger.info(f"Se encontraron {len(all_pdfs)} archivos PDF en Drive")
        
        temp_files = []
        
        # Descargar y procesar cada archivo
        for pdf in tqdm(all_pdfs, desc="Processing Drive files"):
            try:
                file_id = pdf['id']
                file_name = pdf['name']
                file_path = pdf['path']
                
                # Descargar el archivo
                temp_path = download_drive_file(service, file_id, file_name)
                if temp_path:
                    temp_files.append(temp_path)
                    
                    # Obtener categoría desde la estructura de Drive
                    category = os.path.basename(file_path.rstrip('/'))
                    if not category:
                        category = "default"
                    
                    # Procesar el PDF
                    process_pdf(temp_path, chunk_size, overlap, category=category)
            except Exception as e:
                logger.error(f"Error processing Drive file {pdf.get('name', 'unknown')}: {str(e)}")
        
        # Limpiar archivos temporales
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Error removing temp file {temp_file}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in process_drive_files: {str(e)}")

def semantic_search(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Realiza una búsqueda semántica en la base de datos."""
    try:
        query_embedding = generate_embedding(query)
        
        response = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': limit
            }
        ).execute()
        
        return response.data
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        return []

if __name__ == "__main__":
    # Borrar todos los datos existentes en la tabla 'documents' antes de insertar
    logger.info("Eliminando todos los datos existentes en la tabla 'documents'...")
    try:
        supabase.table("documents").delete().neq("id", 0).execute()
        logger.info("Datos eliminados correctamente.")
    except Exception as e:
        logger.error(f"Error al eliminar datos de la tabla 'documents': {str(e)}")
    
    # Comprobar si se debe procesar desde Drive o localmente
    drive_folder_id = os.getenv("DRIVE_FOLDER_ID")
    
    if drive_folder_id:
        logger.info(f"Procesando documentos desde Google Drive folder: {drive_folder_id}")
        process_drive_files(drive_folder_id)
    else:
        # Procesar todos los PDFs en la carpeta 'documents' y subcarpetas
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'documents')
        logger.info(f"Procesando documentos locales desde: {docs_dir}")
        process_pdf_directory(docs_dir)

    logger.info("Procesamiento de documentos completado")