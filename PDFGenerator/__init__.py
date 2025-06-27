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
            # Función auxiliar para intentar hacer clic forzadamente
            async def try_click(button):
                try:
                    await button.scroll_into_view_if_needed()
                    await button.click(timeout=5000, force=True)
                    return True
                except Exception as e:
                    print(f"No se pudo hacer clic: {e}")
                    return False

            # Buscar en el documento principal
            buttons = await page.query_selector_all("button")
            if "octopus" in page.url:
                for button in buttons:
                    text = (await button.inner_text()).strip().lower()
                    if "rechazar" in text:
                        if await try_click(button):
                            print("Cookies rechazadas en documento principal")
                            return
            else:
                for button in buttons:
                    text = (await button.inner_text()).strip().lower()
                    if "aceptar" in text or "aceptar todo" in text:
                        if await try_click(button):
                            print("Cookies aceptadas en documento principal")
                            return

            # Buscar dentro de iframes
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                buttons = await frame.query_selector_all("button")
                for button in buttons:
                    text = (await button.inner_text()).strip().lower()
                    if "aceptar" in text or "aceptar todo" in text:
                        if await try_click(button):
                            print("Cookies aceptadas en iframe")
                            return

            print("No se encontró ningún botón de aceptar cookies")

            print("No se encontró ningún botón de aceptar cookies")
        except Exception as e:
            print(f"No se pudieron aceptar cookies: {e}")

    async def try_click(self, element):
        try:
            await element.scroll_into_view_if_needed()
            await element.click(timeout=5000, force=True)
            return True
        except Exception as e:
            print(f"No se pudo hacer clic: {e}")
            return False

    async def click_ver_mas_info(self, page):
        """
        Si la URL es de Iberdrola o TotalEnergies, busca y hace clic en botones que desplieguen información.
        """
        try:
            if "iberdrola.es" in page.url:
                selectors = [
                    "#ver-detalle",  # Selector por ID del botón
                    "span:has-text('Ver más información')",
                    "button:has-text('Más información')",
                    "a:has-text('Más información')"
                ]
                for selector in selectors:
                    element = await page.query_selector(selector)
                    if element and await self.try_click(element):
                        print(f"Se hizo clic en 'Ver más información' para {page.url}")
                        await asyncio.sleep(3)
                        break

            elif "totalenergies.es" in page.url:
                # Hacer scroll hasta abajo para asegurar que todo carga
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)

                # Buscar todos los elementos <summary> con clase item-title (los títulos del acordeón)
                summary_elements = await page.query_selector_all("summary")

                if not summary_elements:
                    print("No se encontraron elementos <summary> con clase 'item-title'.")
                    # Para debug, listamos todos los summaries
                    all_summaries = await page.query_selector_all("summary")
                    for idx, elem in enumerate(all_summaries):
                        text = await elem.inner_text()
                        classes = await elem.get_attribute("class")
                        print(f"Summary {idx+1}: texto='{text.strip()}', clases='{classes}'")
                    return

                print(f"Encontrados {len(summary_elements)} acordeones (summary.item-title)")

                # Hacer clic en cada summary para abrir acordeón
                for idx, summary in enumerate(summary_elements):
                    try:
                        await summary.scroll_into_view_if_needed()
                        await summary.click(force=True)
                        print(f"Acordeón {idx+1} abierto: {await summary.inner_text()}")
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Error al abrir acordeón {idx+1}: {e}")

        except Exception as e:
            print(f"No se pudo hacer clic en sección de información: {e}")

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

            # Si la página es de Iberdrola, intentar hacer clic en el botón 'Ver más información'
            await self.click_ver_mas_info(page)

            await asyncio.sleep(3)  # Espera tras aceptar cookies y hacer clic en 'Ver más información'

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

            # Obtener las dimensiones del contenido para ajustar el tamaño del PDF
            content_box = await page.evaluate('''
                () => {
                    const body = document.body;
                    const html = document.documentElement;
                    const width = Math.max(body.scrollWidth, body.offsetWidth, html.clientWidth, html.scrollWidth, html.offsetWidth);
                    const height = Math.max(body.scrollHeight, body.offsetHeight, html.clientHeight, html.scrollHeight, html.offsetHeight);
                    return { width, height };
                }
            ''')

            # Guardar la página como un PDF de una sola página ajustando el tamaño a las dimensiones del contenido
            await page.pdf(
                path=filepath,
                width=f"{content_box['width']}px",  # Ajuste del ancho al contenido
                height=f"{content_box['height']}px",  # Ajuste de la altura para que se capture todo el contenido
                scale=1,
                margin={"top": "0px", "right": "0px", "bottom": "0px", "left": "0px"},  # Márgenes a cero como cadenas
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
