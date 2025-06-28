import openai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, Extra
from typing import List, Literal
import logging
import re

# Configurar el logger
logger = logging.getLogger(__name__)

# === MODELOS ===

class Precio(BaseModel):
    nombre: str
    nombre_oferta: str
    precio_te1: float  # €/MWh
    precio_te2: float
    precio_te3: float
    precio_tp1: float  # €/kW-año (después de normalización)
    precio_tp2: float
    unidades_potencia: Literal["€/kW/día", "€/kW/mes", "€/kW/año"] = "€/kW/año"
    descuento_promo: float
    descuento_servicios: float
    tipo_producto: str
    calendario: str
    abonos: float
    permanencia: str
    comentario: str
    analisis: str

    class Config:
        extra = Extra.ignore

    def normalizar(self):
        """Normaliza unidades y corrige incoherencias comunes"""

        # --- Preprocesamiento de potencia: detectar uso erróneo de "." como separador de miles ---
        for attr in ['precio_tp1', 'precio_tp2']:
            valor = getattr(self, attr)
            if valor > 10000:
                valor /= 1000  # probablemente se interpretó mal un punto decimal como miles
            setattr(self, attr, valor)

        # --- Normalizar energía a €/MWh si viene en €/kWh ---
        for attr in ['precio_te1', 'precio_te2', 'precio_te3']:
            valor = getattr(self, attr)
            if valor < 1:
                valor *= 1000
            elif valor > 10000:
                valor /= 1000
            setattr(self, attr, valor)

        # Ordenar precios te1 >= te2 >= te3
        precios_te = sorted([self.precio_te1, self.precio_te2, self.precio_te3], reverse=True)
        self.precio_te1, self.precio_te2, self.precio_te3 = precios_te

        # Si te2 y te3 son 0, asumir tarifa única y copiarlos de te1
        if self.precio_te2 == 0 and self.precio_te3 == 0:
            self.precio_te2 = self.precio_te3 = self.precio_te1

        # --- Normalizar potencia a €/kW-año ---
        if self.unidades_potencia == "€/kW/día":
            self.precio_tp1 *= 365
            self.precio_tp2 *= 365
        elif self.unidades_potencia == "€/kW/mes":
            self.precio_tp1 *= 12
            self.precio_tp2 *= 12
        self.unidades_potencia = "€/kW/año"

        # --- Procesar descuentos: mover € a abonos, dejar % en descuento_promo/servicios ---
        if self.descuento_promo > 1:  # probablemente en euros
            self.abonos += self.descuento_promo
            self.descuento_promo = 0.0

        if self.descuento_servicios > 1:  # probablemente en euros
            self.abonos += self.descuento_servicios
            self.descuento_servicios = 0.0


class Overview(BaseModel):
    precios: List[Precio]

    class Config:
        extra = Extra.ignore

    def normalizar_precios(self):
        for precio in self.precios:
            precio.normalizar()

# === PARSER ===

class PDFParser:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.client = OpenAI()
        logger.info("PDFParser inicializado con la API de OpenAI")

    def parse_pdf(self, pdf_url: str) -> Overview:
        try:
            logger.info(f"Procesando el archivo PDF: {pdf_url}")
            
            # Subir el archivo PDF
            file = openai.files.create(file=open(pdf_url, "rb"), purpose='assistants')
            logger.info(f"Archivo PDF subido a OpenAI con ID: {file.id}")

            # Crear asistente
            tools = [{"type": "file_search"}]
            assistant = self.client.beta.assistants.create(
                name="Price extractor",
                instructions=(
                    "Eres un experto en analizar ofertas de electricidad. "
                    "Extrae los precios y conviértelos a €/MWh y €/kW-año. "
                    "Ignora ofertas de gas y no inventes datos que no estén explícitamente presentes. "
                    "Los descuentos pueden estar en porcentaje (%) o en euros (€). "
                    "Si un descuento es en euros, debe ir en el campo 'abonos'. "
                    "Si los precios de energía tienen solo uno definido y los otros son 0, replica el mismo en todos. "
                    "Asegúrate de que precio_te1 >= precio_te2 >= precio_te3."
                ),
                model="gpt-4o",
                tools=tools
            )

            # Crear thread
            schema_json_string = Overview.model_json_schema()
            thread = self.client.beta.threads.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Extrae los datos de electricidad en el siguiente esquema JSON."
                    },
                    {
                        "role": "user",
                        "content": f"Genera output conforme a: {schema_json_string}.",
                        "attachments": [{"file_id": file.id, "tools": [{"type": "file_search"}]}],
                    },
                ]
            )

            # Ejecutar y esperar
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=thread.id, assistant_id=assistant.id
            )
            logger.info("Análisis completado.")

            # Obtener mensajes
            messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
            message_content = messages[0].content[0].text
            openai.files.delete(file_id=file.id)

            # Parsear output
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "user", "content": f"Extrae el JSON: {message_content.value}"}
                ],
                response_format=Overview,
            )
            overview = completion.choices[0].message.parsed

            # 🔁 Normalizar unidades aquí
            overview.normalizar_precios()

            logger.info("Datos normalizados correctamente.")
            return overview

        except ValidationError as ve:
            logger.error(f"Error de validación: {ve}")
            raise Exception(f"Error de validación: {ve}")
        except Exception as e:
            logger.error(f"Error al procesar PDF: {e}")
            raise Exception(f"Error al procesar PDF: {e}")
