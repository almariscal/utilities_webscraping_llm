# Documentación del Proyecto: Extracción y Procesamiento de Precios desde PDFs

## Descripción General
Este proyecto tiene como objetivo generar y procesar archivos PDF que contienen información sobre ofertas de electricidad. Utiliza OpenAI para analizar los PDFs, extraer precios relevantes y guardarlos en un archivo Excel de salida.

El proceso está dividido en dos partes principales:
1. Generación de PDFs a partir de sitios web.
2. Procesamiento de PDFs y extracción de datos utilizando la API de OpenAI.

## Estructura del Proyecto
El proyecto está compuesto por los siguientes módulos y archivos:

### Archivos Principales
- **main.py**: Punto de entrada principal del programa.
- **OpenAIPDFExtractor.py**: Módulo encargado del procesamiento de PDFs utilizando OpenAI.
- **PDFGenerator.py**: (Suponiendo su existencia) Genera PDFs a partir de URLs especificadas.
- **websites.txt**: Archivo de texto con las URLs a procesar.

### Carpetas
- **./temp_pdf**: Almacena los PDFs generados temporalmente.
- **./processed_pdfs**: Almacena los PDFs ya procesados.
- **./output**: Almacena el archivo Excel con los resultados procesados.
- **./logs**: Contiene los registros de ejecución del programa.

### Archivos de Configuración
- **.env**: Contiene la clave API de OpenAI.

Ejemplo del archivo `.env`:
```
OPENAI_API_KEY=tu_clave_api_aqui
```

## Dependencias

Para ejecutar este proyecto, asegúrate de instalar las siguientes dependencias:

```bash
pip install pandas openai python-dotenv pydantic openpyxl
```

Además, el programa utiliza:
- Python 3.8 o superior.
- API de OpenAI para la extracción de datos.

## Flujo de Trabajo

### 1. Generación de PDFs
El programa utiliza el módulo `PDFGenerator` para generar archivos PDF a partir de un listado de URLs ubicado en `websites.txt`. Estos PDFs se guardan en la carpeta `./temp_pdf`.

### 2. Procesamiento de PDFs
Los PDFs generados se procesan con el módulo `OpenAIPDFExtractor`. El flujo de trabajo incluye:

1. **Subida del PDF a OpenAI**: El archivo se sube a la API de OpenAI.
2. **Configuración del asistente**: Se utiliza un asistente configurado para extraer información en un formato predefinido.
3. **Extracción de datos**: Se extraen los precios de electricidad y otros campos relevantes siguiendo el esquema Pydantic definido.
4. **Guardado de resultados**: Los datos extraídos se agregan a un archivo Excel (`resultados_procesados.xlsx`) que se encuentra en `./output`.
5. **Movido de PDFs procesados**: Los archivos PDF se mueven a la carpeta `./processed_pdfs`.

## Esquema de Datos
Los datos extraídos siguen la siguiente estructura (definida en `OpenAIPDFExtractor`):

### Clase Precio
- **nombre**: Nombre de la empresa.
- **nombre_oferta**: Nombre de la oferta.
- **precio_te1**: Precio de energía en periodo 1 (punta).
- **precio_te2**: Precio de energía en periodo 2 (llano).
- **precio_te3**: Precio de energía en periodo 3 (valle).
- **precio_tp1**: Precio del término de potencia en periodo 1.
- **precio_tp2**: Precio del término de potencia en periodo 2.
- **unidades_potencia**: Unidades del término de potencia (€-kW/día, €-kW/mes, €-kW/año).
- **descuento_promo**: Descuento promocional en %.
- **descuento_servicios**: Descuento extra en %.
- **tipo_producto**: Tipo de producto (fijo o indexado).
- **calendario**: Calendario de facturación.
- **abonos**: Abonos al cliente en €/años.
- **permanencia**: Permanencia del producto.
- **comentario**: Otros comentarios.
- **analisis**: Análisis económico y de mercado en formato Markdown.

### Clase Overview
- **precios**: Lista de objetos `Precio`.

## Ejecución del Programa

1. Asegúrate de que el archivo `.env` contiene la clave API de OpenAI.
2. Coloca las URLs en el archivo `websites.txt`.
3. Ejecuta el programa principal:

```bash
python main.py
```

4. Al finalizar, los resultados se almacenarán en `./output/resultados_procesados.xlsx` y los archivos PDF se moverán a `./processed_pdfs`.

## Registro de Logs
Los registros se almacenan en la carpeta `./logs` con un archivo nombrado de la siguiente forma:

```
log_proceso_YYYYMMDD_HHMMSS.log
```

Ejemplo de salida en logs:

```
2024-06-01 10:00:00 - INFO - Iniciando generación de PDFs a partir de las URLs
2024-06-01 10:01:00 - INFO - Procesando archivo: oferta_empresa.pdf
2024-06-01 10:01:10 - INFO - Datos parseados correctamente: {...}
2024-06-01 10:01:15 - INFO - Datos guardados en el archivo Excel: ./output/resultados_procesados.xlsx
2024-06-01 10:01:20 - INFO - Proceso completado
```

## Errores y Solución de Problemas

### Clave API Inválida
- **Error**: `AuthenticationError: Incorrect API Key provided.`
- **Solución**: Verifica que la clave en el archivo `.env` sea correcta.

### Archivo Excel Bloqueado
- **Error**: `PermissionError: [Errno 13] Permission denied: 'resultados_procesados.xlsx'`
- **Solución**: Cierra el archivo Excel si está abierto antes de ejecutar el programa.

### Error en la Validación de Datos
- **Error**: `ValidationError: ...`
- **Solución**: Asegúrate de que el PDF contiene los campos esperados y que el esquema JSON esté bien definido.

## Licencia
Este proyecto está bajo la licencia MIT pero debes solicitar permiso para uso comercial.

## Autor
**Nombre del Autor**  
Alberto L. Mariscal
albertolmariscal@gmail.com  
© 2024

