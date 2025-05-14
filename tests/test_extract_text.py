from document_utils import download_and_extract_text_from_pdf_drive

# Usaremos el primer PDF encontrado en la última lista: Manual_Compra_de_dólares (3).pdf
FILE_ID = '1X-YUYh9fTt0vp6TrYfcaf0RBwWKnCvBA'

def main():
    print(f"Descargando y extrayendo texto del PDF en memoria...")
    texto = download_and_extract_text_from_pdf_drive(FILE_ID)
    print("\n--- EXTRACTO DE TEXTO ---\n")
    print(texto[:2000])  # Solo mostramos los primeros 2000 caracteres para no saturar la consola
    print("\n--- FIN DEL EXTRACTO ---\n")

if __name__ == "__main__":
    main() 