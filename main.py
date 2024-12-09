# MVP to check if it is possible to webscrap using LLMs + OCR
# The architecture will combine OpenAI + CrewAI in order to obtain an structured output from websites

# Import OpenAI keys from .env file
from dotenv import load_dotenv
import os

# Cargar variables del archivo .env
load_dotenv()

# Acceder a la clave
openai_api_key = os.getenv("OPENAI_API_KEY")

# Converting the websites to PDF
from PDFGenerator import PDFGenerator
import asyncio

# Ruta del archivo con las URLs
websites_file = "websites.txt"

# Crear una instancia de PDFGenerator
pdf_generator = PDFGenerator(websites_file)

# Ejecutar el proceso para generar los PDFs
asyncio.run(pdf_generator.process_all_websites())

import os
import shutil
from OpenAIPDFExtractor import PDFParser
import pandas as pd
from datetime import datetime

input_folder = './temp_pdf'
processed_folder = './processed_pdfs'
output_folder = './output'

# Crear carpetas necesarias si no existen
os.makedirs(processed_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

# Inicializamos el DataFrame vacío
df = pd.DataFrame()

# Procesar cada archivo PDF en la carpeta
parser = PDFParser(openai_api_key=openai_api_key)

for filename in os.listdir(input_folder):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(input_folder, filename)
        try:
            print(f"Procesando: {filename}")
            overview = parser.parse_pdf(pdf_path)
            
            # Convertir los precios en DataFrame y añadir a `df`
            for precio in overview.precios:
                df = pd.concat([df, pd.DataFrame([precio.model_dump()])], ignore_index=True)
            
            # Mover el archivo a la carpeta de procesados
            shutil.move(pdf_path, os.path.join(processed_folder, filename))
            print(f"{filename} procesado correctamente y movido a {processed_folder}")
        except Exception as e:
            print(f"Error al procesar {filename}: {e}")

# Guardar el DataFrame en un archivo Excel
# Generar una marca de tiempo para el nombre del archivo
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_excel_path = os.path.join(output_folder, f'resultados_procesados_{timestamp}.xlsx')

df.to_excel(output_excel_path, index=False)
print(f"DataFrame guardado en: {output_excel_path}")

input("Presiona Enter para cerrar...")  # Esto mantiene la terminal abierta hasta que el usuario presione Enter.
