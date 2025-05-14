# from google.adk import Tool, Parameter
# from google.adk.tool import ToolContext
from supabase import create_client
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
import pprint

# Load environment variables from root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configuración de Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Modelo de embeddings (debe coincidir con el usado para crear los embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')

def buscar_documentos(params: dict) -> str:
    """Busca documentos relevantes basados en la consulta proporcionada."""
    consulta = params.get("consulta")
    limite = params.get("numero_resultados", 5)
    umbral = params.get("umbral_similitud", 0.1)
    categoria = params.get("categoria", None)
    
    # Generar embedding para la consulta
    query_embedding = model.encode(consulta).tolist()
    print("[LOG] Consulta:", consulta)
    print("[LOG] Embedding generado (primeros 10 valores):", query_embedding[:10], "... (total:", len(query_embedding), ")")
    
    # Payload para Supabase
    payload = {
        'query_embedding': query_embedding,
        'match_threshold': umbral,
        'match_count': limite
    }
    print("[LOG] Payload enviado a Supabase:")
    pprint.pprint(payload)
    
    # Realizar búsqueda en Supabase
    if categoria:
        print(f"[LOG] Filtrando por categoría: {categoria}")
        # Intentar filtrar por la categoría del producto en los metadatos
        response = supabase.rpc(
            'match_documents_by_category',
            {**payload, 'category_name': categoria}
        ).execute()
    else:
        response = supabase.rpc(
            'match_documents',
            payload
        ).execute()
    
    print("[LOG] Respuesta cruda de Supabase:")
    pprint.pprint(response.data)
    
    results = response.data
    
    if not results:
        return "No se encontraron documentos relevantes para esta consulta."
    
    # Formatear resultados
    formatted_results = "Información encontrada en los documentos:\n\n"
    for i, result in enumerate(results, 1):
        formatted_results += f"Resultado {i} (Similitud: {result['similarity']:.2f}):\n"
        formatted_results += f"Contenido: {result['content']}\n"
        formatted_results += f"Fuente: {result['metadata']['source']}\n\n"
    
    return formatted_results

# Más herramientas pueden ser agregadas según sea necesario...