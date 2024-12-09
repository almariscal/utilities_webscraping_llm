import os
import fitz  # PyMuPDF
#from PIL import Image
#import pytesseract

# Configura la ruta de Tesseract en tu sistema si es necesario
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Si usas Windows

class PDFParser:
    def __init__(self, pdf_folder, dpi=300):
        self.pdf_folder = pdf_folder  # Carpeta que contiene los PDFs
        self.dpi = dpi  # Resolución en DPI para la conversión de PDF a imagen
    
    def extraer_imagenes_pdf(self, pdf_path):
        """
        Convierte cada página de un archivo PDF en una imagen de alta calidad usando PyMuPDF.
        :param pdf_path: Ruta del archivo PDF
        :return: Lista de imágenes (cada página convertida a una imagen)
        """
        # Abre el archivo PDF
        documento = fitz.open(pdf_path)
        
        # Lista para almacenar las imágenes de las páginas
        imagenes = []
        
        # Iterar sobre las páginas
        for pagina_num in range(documento.page_count):
            pagina = documento.load_page(pagina_num)  # Cargar la página
            # Convertir la página a una imagen (pixmap)
            imagen = pagina.get_pixmap(matrix=fitz.Matrix(self.dpi / 72, self.dpi / 72))  # Ajustar resolución (DPI)
            imagenes.append(imagen)  # Añadir imagen a la lista
        
        return imagenes

    def extraer_texto_imagen(self, imagen):
        """
        Usa Tesseract OCR para extraer texto de una imagen.
        :param imagen: Imagen de la que extraer el texto
        :return: El texto extraído de la imagen
        """
        pil_imagen = Image.frombytes("RGB", (imagen.width, imagen.height), imagen.samples)
        return pytesseract.image_to_string(pil_imagen)

    def procesar_pdf(self, pdf_path):
        """
        Procesa un archivo PDF, convierte sus páginas a imágenes y extrae el texto de las imágenes usando OCR.
        :param pdf_path: Ruta del archivo PDF
        :return: Lista de textos extraídos de cada página
        """
        # Extraer imágenes de las páginas del PDF
        imagenes = self.extraer_imagenes_pdf(pdf_path)
        
        # Extraer el texto de cada imagen usando Tesseract
        textos = [self.extraer_texto_imagen(imagen) for imagen in imagenes]
        
        return textos

    def analizar_ofertas(self):
        """
        Procesa todos los PDFs de una carpeta dada, convirtiendo las páginas a imágenes y extrayendo el texto.
        :return: Lista con los textos extraídos de todos los PDFs
        """
        ofertas = []
        
        # Iterar sobre todos los archivos PDF en la carpeta
        for archivo_pdf in os.listdir(self.pdf_folder):
            if archivo_pdf.endswith(".pdf"):
                pdf_path = os.path.join(self.pdf_folder, archivo_pdf)
                print(f"Procesando {pdf_path}...")
                
                # Procesar el PDF y extraer textos
                textos = self.procesar_pdf(pdf_path)
                
                # Aquí puedes agregar más lógica para extraer la información específica de los textos
                for texto in textos:
                    print(texto)  # Imprimir el texto extraído (aquí puedes adaptarlo a lo que necesitas)
                
                # Añadir los textos extraídos a la lista de ofertas
                ofertas.append(textos)
        
        return ofertas