import openai
from langchain.prompts import ChatPromptTemplate
from openai import OpenAI
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from pydantic import BaseModel, Field, ValidationError, Extra
from typing import List
import os
import re

class Precio(BaseModel):
    """Estructura precio. SOLO RELLENAR LA PARTE DE ELECTRICIDAD"""
    nombre: str = Field(description="Nombre de la empresa que comercializa la oferta")
    nombre_oferta: str = Field(description="Nombre de la oferta")
    precio_te1: float = Field(description="Precio de la energía en el periodo 1")
    precio_te2: float = Field(description="Precio de la energía en el periodo 2")
    precio_te3: float = Field(description="Precio de la energía en el periodo 3")
    precio_tp1: float = Field(description="Precio del término de potencia en el periodo 1 en €/kw-dia")
    precio_tp2: float = Field(description="Precio del término de potencia en el periodo 2 en €/kw-dia")
    tipo_producto: str = Field(description="Tipo de producto, fijo o indexado")
    abonos: float = Field(description="Abonos al cliente en €/años")
    permanencia: str = Field(description="Permanencia del producto")
    comentario: str = Field(description="Otros comentarios acerca del producto")
    analisis: str = Field(description="Análisis en formato Markdown acerca del producto desde un punto de vista económico pero también de marketing y mercado")
    class Config:
        extra = Extra.ignore  # Ignorar claves adicionales en el JSON

class Overview(BaseModel):
    """Haz un csv con 4 columnas e incluye solo luz, ELIMINA EL GAS"""
    precios: List[Precio] = Field(description=(
        "Lista de los diferentes precios que puede tener una factura. "
        "No te inventes ningún precio y extrae solo la información que existe. "
        "Puede haber varios periodos temporales con precios diferentes o un único periodo. "
        "Coge solo los valores totales, no el desglose e ignora la parte de acceso a redes."
    ))
    class Config:
        extra = Extra.ignore  # Ignorar claves adicionales en el JSON

class PDFParser:
    def __init__(self, openai_api_key: str):
        """Inicializa el cliente OpenAI con la clave proporcionada."""
        openai.api_key = openai_api_key
        self.client = OpenAI()

    def parse_pdf(self, pdf_url: str) -> Overview:
        """
        Procesa un PDF a partir de su URL, extrae información y devuelve un objeto Overview.

        Args:
            pdf_url (str): URL del PDF a analizar.

        Returns:
            Overview: Objeto Overview con los datos extraídos.

        Raises:
            Exception: Si ocurre un error durante el procesamiento o la validación.
        """
        try:
            # Descarga el archivo PDF y súbelo a OpenAI
            file = openai.files.create(file=open(pdf_url, "rb"), purpose='assistants')

            # Configura el asistente con herramientas y prompts
            tools = [{"type": "file_search"}]
            assistant = self.client.beta.assistants.create(
                name="Price extractor",
                instructions=(
                    "You are an expert analyzing electricity offers from websites and PDFs, "
                    "as well as extracting the prices and comparing them. "
                    "Generate a structured output according to the Overview schema."
                ),
                model="gpt-4o-2024-08-06",
                tools=tools
            )

            # Crea un thread con el archivo PDF como entrada
            schema_json_string = Overview.model_json_schema()
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Eres un asistente experto en ofertas de electricidad. "
                            "Puedes generar resúmenes detallados de las ofertas de electricidad "
                            "siguiendo un esquema JSON."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Extrae toda la información y explica la siguiente oferta de electricidad. "
                            f"Genera un json con la siguiente estructura: {schema_json_string}. "
                            "Incluye únicamente el json y comienza por '{{'."
                        ),
                        "attachments": [{"file_id": file.id, "tools": [{"type": "file_search"}]}],
                    },
                ]
            )

            # Ejecuta el proceso de análisis
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant.id)
            messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            message_content = messages[0].content[0].text

            # Extrae y valida el JSON
            match = re.search(r'(\{.*\})', message_content.value, re.DOTALL)
            if match:
                json_str = match.group(1)
                return Overview.parse_raw(json_str)
            else:
                raise ValueError("No se encontró un JSON válido en la respuesta.")

        except ValidationError as ve:
            raise Exception(f"Error de validación al procesar los datos: {ve}")
        except Exception as e:
            raise Exception(f"Error inesperado al procesar el PDF: {e}")

# Ejemplo de uso en un script principal
if __name__ == "__main__":
    try:
        parser = PDFParser(openai_api_key="TU_API_KEY")
        pdf_url = './temp_pdf/octopusenergy_es_7076053329209093311_20241208_180609.pdf'
        overview = parser.parse_pdf(pdf_url)
        print(overview)
    except Exception as e:
        print(f"Error al procesar el PDF: {e}")
