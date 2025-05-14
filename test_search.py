import sys
import os

# Agregar las rutas necesarias al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'chatbot-contact-center'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'vector-tools'))

# Importar las constantes directamente desde prompts.py
from prompts import ROOT_AGENT_DESCRIPTION, ROOT_AGENT_INSTRUCTION

# Importamos la función directamente desde agent.py
from agent import search_documents_tool

def test_search():
    # Prueba buscando información sobre reset de clave
    result = search_documents_tool('Reset de Clave', 'Cómo puedo cambiar mi contraseña?')
    print("=== Resultado de la búsqueda ===")
    print(result)
    print("================================")

    # Prueba buscando información sobre tarjetas de crédito
    result = search_documents_tool('Tarjetas de Crédito', 'Límite de compra')
    print("=== Resultado de la búsqueda ===")
    print(result)
    print("================================")

if __name__ == "__main__":
    print(f"Usando descripción del agente: {ROOT_AGENT_DESCRIPTION[:50]}...")
    print(f"Usando instrucción del agente: {ROOT_AGENT_INSTRUCTION[:50]}...")
    test_search() 