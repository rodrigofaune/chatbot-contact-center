from drive_utils import list_files_in_folder_recursive

FOLDER_ID = '1BzbTrD2nVyTSN5Z5T_4-RYTpKPWvhmBQ'

def main():
    files = list_files_in_folder_recursive(FOLDER_ID)
    if not files:
        print('No se encontraron archivos en la carpeta ni en subcarpetas.')
    else:
        print('Archivos encontrados:')
        for f in files:
            print(f"- {f['name']} (ID: {f['id']}, Tipo: {f['mimeType']})")

if __name__ == "__main__":
    main() 