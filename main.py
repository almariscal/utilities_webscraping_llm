import os
import shutil
import asyncio
import pandas as pd
import logging
from datetime import datetime
from dotenv import load_dotenv
from PDFGenerator import PDFGenerator
from OpenAIPDFExtractor import PDFParser

# Cargar variables del archivo .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configuración de carpetas y archivos
websites_file = "websites.txt"
input_folder = './temp_pdf'
processed_folder = './processed_pdfs'
output_folder = './output'
logs_folder = './logs'

# Crear carpetas necesarias si no existen
os.makedirs(processed_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)
os.makedirs(logs_folder, exist_ok=True)

# Configuración del logging
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(logs_folder, f'log_proceso_{timestamp}.log')
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(log_file),
                        logging.StreamHandler()
                    ])
logger = logging.getLogger()

# Paso 1: Generar PDFs desde sitios web
logger.info("Iniciando generación de PDFs a partir de las URLs")
try:
    pdf_generator = PDFGenerator(websites_file)
    asyncio.run(pdf_generator.process_all_websites())
    logger.info("Generación de PDFs completada")
except Exception as e:
    logger.error(f"Error al generar PDFs: {e}")

# Paso 2: Procesar PDFs y extraer datos
logger.info("Iniciando procesamiento de PDFs")
parser = PDFParser(openai_api_key=openai_api_key)
execution_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
excel_file_path = os.path.join(output_folder, 'resultados_procesados.xlsx')

# Leer el archivo existente si ya existe
if os.path.exists(excel_file_path):
    df = pd.read_excel(excel_file_path)
    logger.info("Archivo Excel existente cargado")
else:
    df = pd.DataFrame()
    logger.info("Nuevo archivo Excel creado")

for filename in os.listdir(input_folder):
    if filename.endswith('.pdf'):
        pdf_path = os.path.join(input_folder, filename)
        try:
            logger.info(f"Procesando archivo: {filename}")
            overview = parser.parse_pdf(pdf_path)
            
            # Extraer y transformar los datos, añadiendo la fecha de ejecución
            for precio in overview.precios:
                precio_data = precio.model_dump()
                precio_data['Fecha de Ejecucion'] = execution_date
                df = pd.concat([df, pd.DataFrame([precio_data])], ignore_index=True)
            
            # Mover archivo procesado
            shutil.move(pdf_path, os.path.join(processed_folder, filename))
            logger.info(f"{filename} procesado y movido a {processed_folder}")
        except Exception as e:
            logger.error(f"Error al procesar {filename}: {e}")

# Guardar el DataFrame en el archivo Excel existente sin borrar datos anteriores
try:
    with pd.ExcelWriter(excel_file_path, mode='w', engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    logger.info(f"Datos guardados en el archivo Excel: {excel_file_path}")
except Exception as e:
    logger.error(f"Error al guardar el archivo Excel: {e}")

logger.info("Proceso completado")
input("Presiona Enter para cerrar...")