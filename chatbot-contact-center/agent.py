from google.adk.agents import Agent
import sys
import os
from google.adk.sessions import Session

# Añadir la ruta del directorio chatbot-contact-center al path si no está ya
chatbot_path = os.path.dirname(__file__)
if chatbot_path not in sys.path:
    sys.path.append(chatbot_path)

# Importación absoluta de prompts.py
from prompts import ROOT_AGENT_DESCRIPTION, ROOT_AGENT_INSTRUCTION

# Agregar la ruta del directorio vector-tools al path para poder importar get_vector_docs
vector_tools_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vector-tools')
if vector_tools_path not in sys.path:
    sys.path.append(vector_tools_path)

# Importar la función buscar_documentos desde get_vector_docs
from get_vector_docs import buscar_documentos

# IDs de productos bancarios y sus carpetas en Drive
# Esta información ahora se utilizará como filtro o metadatos para la búsqueda en Supabase
PRODUCTOS_BANCARIOS = {
    "Compra Dolares": "1ghsO_g7jWbz5Ar8QKG23ahNCdkh0H-Sp",
    "DAP": "1x26utz9YuckkshXYjlVnVDB74LTI1N6g",
    "Tarjetas de Crédito": "1e11pamT4-KWlfFNk_-pNu-gD3fkVL1cQ",
    "APP Empresa": "1oYS5pKwBnHbLN6_59GvzDRqPXXQwxcN1",
    "Venta Dolares": "1gtgMNwGAChBSlMiEdipkn7eGR-mrSzOQ",
    "Reset y Recuperacion Clave": "1SR5QWqB8Jwjg0OJcx1HYc3E-WxMUUhUy",
    "Datos Clientes": "12l4rRlSx8ctUVN4LJ95Y84JQIXSGdTi3",
    "abonos Masivos": "1wvPElP7cGRKx80XUDBsB8B4XJBkCxTQC",
    "Crédito Comercial FOGAPE": "1Ae00CARbtXAboWcnCMpZA9XZBeQvAKTN",
    "Onboarding Empresas": "1GzJmx0RzVwZ6a2vmvAzc4_1uhduBiyu4",
    "Aumento LAC": "1NjPRcQQHvrNAk1VEQaRZWVJvivo4Y_Li",
    "Manual Boton de Pago": "1URPsJhGRd8u6I_T9tkrj2Tco-jroXpXu",
    "Consulta Credito Consumo": "1l1RcItbnFiQTB-Bbup6wcQL6ZsaqPY-8",
    "InterPass": "1GAbCNIQLxsuu0879trdVbO0LaHP5r8gY",
    "Credito Comercial": "1Bz_Snfy0qy_RSDxM_gb-d6CnXTnADqA_",
    "Pago de Linea": "1iBXnmHMtFZELDuJIx7JA7QK3YNvX2V67",
    "Consulta Credito Hipotecario": "1XKZ_u01dRFYzCNfnF9dMK239H280qXZ4",
    "Pac Multibanco": "1bLrR6ihm-n87BLa-PZHro7fw5nLgDmfA",
    "LBTR": "10YaJIXypa3mztrl7i20ta6qtCJmlQYBh",
    "Cartola FFMM": "1qRsY5jnky_rVKNC0kQc8MC-q-Lol2ACF"
}

def search_documents_tool(producto: str, consulta: str) -> str:
    """
    Busca documentos relevantes sobre el producto bancario utilizando la búsqueda vectorial en Supabase.
    """
    # Normalizar el nombre del producto para facilitar la búsqueda en las categorías de metadata
    producto_normalizado = None
    if producto:
        # Intentar encontrar la mejor coincidencia en las claves de PRODUCTOS_BANCARIOS
        for nombre_producto in PRODUCTOS_BANCARIOS.keys():
            if producto.lower() in nombre_producto.lower() or nombre_producto.lower() in producto.lower():
                producto_normalizado = nombre_producto
                break
    
    # Crear una consulta combinada que incluya el nombre del producto y la consulta específica
    consulta_combinada = f"{producto}: {consulta}" if producto else consulta
    
    # Utilizar la función buscar_documentos importada desde get_vector_docs
    params = {
        "consulta": consulta_combinada,
        "numero_resultados": 5,  # Puedes ajustar este valor según sea necesario
        "umbral_similitud": 0.1,  # Puedes ajustar este valor según sea necesario
        "categoria": producto_normalizado  # Filtrar por categoría de producto si es posible
    }
    
    try:
        # Realizar la búsqueda vectorial
        resultados = buscar_documentos(params)
        
        if resultados.startswith("No se encontraron documentos"):
            # Si no se encuentran documentos relevantes, informar al usuario
            return f"No encontré información específica sobre '{consulta}' para el producto '{producto}'. Por favor, intenta reformular tu pregunta o consulta sobre otro producto."
        
        return resultados
    except Exception as e:
        # Manejar cualquier error que pueda ocurrir durante la búsqueda
        error_message = f"Ocurrió un error al buscar documentos: {str(e)}"
        print(error_message)
        return "Lo siento, tuve un problema al buscar información relevante. Por favor, intenta de nuevo con otra consulta."

root_agent = Agent(
    model='gemini-2.0-flash-001',
    name='root_agent',
    description=ROOT_AGENT_DESCRIPTION,
    instruction=ROOT_AGENT_INSTRUCTION,
    tools=[search_documents_tool]
)
