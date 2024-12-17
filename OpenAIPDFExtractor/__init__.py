import openai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, Extra
from typing import List, Literal
import logging  # Importar logging para reutilizar el logger global configurado
import re

# Configurar el logger reutilizando la configuración del main
logger = logging.getLogger(__name__)

class Precio(BaseModel):
    """Estructura precio"""
    nombre: str = Field(description="Nombre de la empresa que comercializa la oferta")
    nombre_oferta: str = Field(description="Nombre de la oferta")
    precio_te1: float = Field(description="Precio de la energía en el periodo 1 (también llamado periodo punta)")
    precio_te2: float = Field(description="Precio de la energía en el periodo 2 (también llamado periodo llano)")
    precio_te3: float = Field(description="Precio de la energía en el periodo 3 (también llamado periodo valle)")
    precio_tp1: float = Field(description="Precio del término de potencia en el periodo 1, también llamado periodo punta")
    precio_tp2: float = Field(description="Precio del término de potencia en el periodo 2, también llamado periodo valle")
    #unidades_potencia: Literal["€-kw/dia", "€-kW/mes", "€-kW/año"] = Field(description="Unidades del término de potencia: €-kw/dia, €-kW/mes o €-kW/año.")
    descuento_promo: float = Field(description="Descuento promocional sobre el término de energía en %, no considerar si el descuento es en € (sería un abono) ni el número de horas gratis")
    descuento_servicios: float = Field(description="Descuento extra en % por contratar otros servicios.  No confundir con abonos, es un descuento en porcentaje. Puede no haber ningún descuento")
    tipo_producto: str = Field(description="Tipo de producto, fijo o indexado")
    calendario: str = Field(description="Tipo de calendario que aplica al producto para facturarlo. Puede ser el calendario ATR que determina la legislación o calendarios personalizados (por ejemplo día-noche, horas promo/no promo...)")
    abonos: float = Field(description="Abonos al cliente en €/años. No incluir sorteos.")
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
        logger.info("PDFParser inicializado con la API de OpenAI")

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
            logger.info(f"Procesando el archivo PDF: {pdf_url}")
            
            # Descarga el archivo PDF y súbelo a OpenAI
            file = openai.files.create(file=open(pdf_url, "rb"), purpose='assistants')
            logger.info(f"Archivo PDF subido a OpenAI con ID: {file.id}")

            # Configura el asistente con herramientas y prompts
            tools = [{"type": "file_search"}]
            assistant = self.client.beta.assistants.create(
                name="Price extractor",
                instructions=(
                    "You are an expert analyzing electricity offers from websites and PDFs, "
                    "as well as extracting the prices and comparing them."
                ),
                model="gpt-4o-2024-08-06",
                tools=tools
            )
            logger.info("Asistente OpenAI configurado correctamente.")

            # Crea un thread con el archivo PDF como entrada
            schema_json_string = Overview.model_json_schema()
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Eres un asistente experto en ofertas de electricidad. "
                            "Extrae la información en el esquema JSON proporcionado."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Genera un output siguiendo el esquema: {schema_json_string}."
                        ),
                        "attachments": [{"file_id": file.id, "tools": [{"type": "file_search"}]}],
                    },
                ]
            )
            logger.info("Thread creado con el asistente para el análisis del archivo.")

            # Ejecuta el proceso de análisis
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant.id)
            logger.info("Análisis completado. Recuperando los mensajes.")

            messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            message_content = messages[0].content[0].text
            openai.files.delete(file_id=file.id)

            # Extraemos la información en formato JSON
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "user", "content": f"Extrae la información en formato JSON: {message_content.value}"}
                ],
                response_format=Overview,
            )
            overview = completion.choices[0].message.parsed
            logger.info(f"Datos parseados correctamente: {overview.model_dump()}")
            return overview

        except ValidationError as ve:
            logger.error(f"Error de validación al procesar los datos: {ve}")
            raise Exception(f"Error de validación al procesar los datos: {ve}")
        except Exception as e:
            logger.error(f"Error inesperado al procesar el PDF: {e}")
            raise Exception(f"Error inesperado al procesar el PDF: {e}")
