from playwright.sync_api import sync_playwright

# chrome_executable_path = "/home/vladimir/.cache/ms-playwright/chromium_headless_shell-1181/chrome-linux/headless_shell"

chrome_executable_path = (
    "/home/vladimir/.cache/ms-playwright/chromium-1181/chrome-linux/chrome"
)


def obtener_html_completo(url, espera_adicional=10000, timeout=30000):
    """
    Espera a que el DOM se estabilice antes de extraer el HTML.
    """
    with sync_playwright() as p:
        # browser = p.chromium.launch(headless=True)
        browser = p.chromium.launch(
            headless=False, executable_path=chrome_executable_path
        )
        page = browser.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)

            # Esperar tiempo adicional para contenido dinámico
            if espera_adicional > 0:
                page.wait_for_timeout(espera_adicional)

            # Esperar a que no haya cambios en el DOM por un período
            page.wait_for_function(
                """
                () => {
                    return new Promise((resolve) => {
                        const observer = new MutationObserver(() => {
                            // Reiniciar el timer si hay cambios
                            clearTimeout(window._stabilityTimer);
                            window._stabilityTimer = setTimeout(() => {
                                observer.disconnect();
                                resolve(true);
                            }, 1000);
                        });
                        
                        observer.observe(document.body, {
                            childList: true,
                            subtree: true,
                            attributes: true,
                            characterData: true
                        });
                        
                        // Timer inicial
                        window._stabilityTimer = setTimeout(() => {
                            observer.disconnect();
                            resolve(true);
                        }, 1000);
                    });
                }
            """,
                timeout=15000,
            )

            html_completo = page.content()
            return html_completo

        except Exception as e:
            print(f"Error al cargar la página: {e}")
            return None

        finally:
            browser.close()

# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo básico
    url = "https://www.mercadolibre.com.mx/aceite-loreal-elvive-aceite-extraordinario-reparacion-de-puntas/p/MLM24750853#polycard_client=recommendations_pdp-p2p&reco_backend=odin-uni-p2p-supermarket-repurchase_supermarket&reco_model=retrieval-ranker-complementarios&reco_client=pdp-p2p&reco_item_pos=0&reco_backend_type=low_level&reco_id=d57a33ad-517d-4757-8607-1efc927a3851&wid=MLM1710516068&sid=recos"
    html = obtener_html_completo(url)

    if html:
        print(f"HTML obtenido correctamente. Longitud: {len(html)} caracteres")
        # Puedes guardar el HTML en un archivo si lo necesitas
        with open("data/output/pagina_descargada.html", "w", encoding="utf-8") as f:
            f.write(html)
    else:
        print("No se pudo obtener el HTML")
