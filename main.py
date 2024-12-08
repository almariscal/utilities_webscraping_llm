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