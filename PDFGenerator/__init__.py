import os
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from urllib.parse import urlparse

class PDFGenerator:
    def __init__(self, websites_file, output_folder="temp_pdf"):
        self.websites_file = websites_file
        self.output_folder = output_folder
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Crear carpeta de salida si no existe
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def fetch_websites(self):
        """
        Lee las URLs desde el archivo y devuelve una lista de URLs.
        """
        with open(self.websites_file, "r") as file:
            websites = [line.strip() for line in file if line.strip()]
        return websites

    async def accept_cookies(self, page):
        """
        Busca y hace clic en un botón de aceptación de cookies si está presente.
        """
        try:
            selectors = [
                "button:has-text('Aceptar')",
                "button:has-text('Aceptar todo')",
                "button:has-text('Accept')",
                "button:has-text('Accept all')"
            ]
            for selector in selectors:
                if await page.query_selector(selector):
                    await page.click(selector)
                    print("Cookies aceptadas")
                    break
        except Exception as e:
            print(f"No se pudieron aceptar cookies: {e}")

    async def generate_pdf(self, url, browser):
        """
        Genera un PDF desde una URL utilizando Playwright.
        """
        try:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"  # User-agent estándar
            )
            page = await context.new_page()

            # Reintento de navegación en caso de error
            for attempt in range(3):
                try:
                    print(f"Intento {attempt + 1} de navegación para {url}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(5)  # Espera adicional
                    break
                except Exception as e:
                    print(f"Intento {attempt + 1} fallido para {url}: {e}")
                    if attempt == 2:
                        raise

            # Aceptar cookies, si es necesario
            await self.accept_cookies(page)
            await asyncio.sleep(3)  # Espera tras aceptar cookies

            # Verificar contenido visible
            content = await page.content()
            if not content.strip():
                print(f"El contenido de la página {url} está vacío.")
                return

            # Generar nombre del archivo único
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.replace(".", "_")
            path_hash = hash(parsed_url.path)  # Crear identificador único basado en el path
            filename = f"{domain}_{path_hash}_{self.timestamp}.pdf"
            filepath = os.path.join(self.output_folder, filename)

            # Guardar la página como un PDF de una sola página
            await page.pdf(
                path=filepath,
                format=None,
                width="1920px",
                height="10000px",  # Captura todo el contenido en una sola página
                scale=1,
                print_background=True
            )
            print(f"PDF generado para {url}: {filepath}")

            await context.close()
        except Exception as e:
            print(f"Error procesando {url}: {e}")

    async def process_all_websites(self):
        """
        Procesa todas las URLs y genera un PDF para cada una.
        """
        websites = self.fetch_websites()

        # Lanzar el navegador en modo no headless
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Cambiado a no headless
            for url in websites:
                await self.generate_pdf(url, browser)
            await browser.close()

if __name__ == "__main__":
    pdf_generator = PDFGenerator("websites.txt")
    asyncio.run(pdf_generator.process_all_websites())
