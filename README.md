# 🛍️ Web Scraper to WooCommerce Importer

Este proyecto automatiza la extracción de información de productos de tiendas en línea y su posterior importación a WooCommerce mediante su API REST.

## 📋 Descripción

El sistema toma una lista de URLs de productos de e-commerce, extrae automáticamente información relevante (imágenes, descripciones, etiquetas, etc.) y la sube a una tienda WooCommerce utilizando la API REST.

## ✨ Características

- **🔍 Scraping Inteligente**: Extrae información de productos de múltiples tiendas en línea
- **🖼️ Gestión de Imágenes**: Descarga y optimiza imágenes de productos
- **📦 Importación Masiva**: Procesa listas grandes de productos eficientemente
- **⚙️ Configuración Flexible**: Adaptable a diferentes estructuras de tiendas online
- **🔒 Manejo de Errores**: Sistema robusto con reintentos y logging
- **🔄 Sincronización**: Actualización de productos existentes y creación de nuevos

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.8+
- **Web Scraping**: BeautifulSoup4, Scrapy, Selenium
- **API Client**: WooCommerce REST API Python client
- **Procesamiento de Imágenes**: Pillow, requests
- **Manejo de Datos**: Pandas, JSON
- **Base de Datos**: SQLite/PostgreSQL (opcional)
- **Orquestación**: Celery (para procesamiento asíncrono)

## 📁 Estructura del Proyecto

```
scraper-woocommerce/
├── src/
│   ├── scrapers/          # Módulos de scraping por tienda
│   ├── woocommerce/       # Cliente y adaptadores de WooCommerce
│   ├── models/           # Modelos de datos
│   ├── utils/            # Utilidades comunes
│   └── config/           # Configuración
├── data/
│   ├── input/            # URLs de productos a importar
│   ├── output/           # Datos extraídos
│   └── images/           # Imágenes descargadas
├── logs/                 # Archivos de log
└── tests/               # Pruebas unitarias e integración
```

## 🚀 Instalación

### Prerrequisitos
- Python 3.8 o superior
- WooCommerce 5.0+ con REST API habilitada
- Claves de API de WooCommerce (Consumer Key y Consumer Secret)

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/scraper-woocommerce.git
cd scraper-woocommerce

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Configuración

1. Copiar el archivo de configuración:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Configurar las credenciales de WooCommerce en `config/config.yaml`:

```yaml
woocommerce:
  url: "https://tu-tienda.com"
  consumer_key: "ck_tu_consumer_key"
  consumer_secret: "cs_tu_consumer_secret"
  version: "wc/v3"

scraping:
  delay_between_requests: 2
  timeout: 30
  max_retries: 3

images:
  download_path: "./data/images"
  max_size: "1000x1000"
  quality: 85
```

## 📖 Uso

### Ejemplo Básico

```python
from src.main import ProductImporter

# Inicializar el importador
importer = ProductImporter()

# Procesar lista de URLs
urls = [
    "https://tienda-ejemplo.com/producto-1",
    "https://tienda-ejemplo.com/producto-2"
]

results = importer.process_urls(urls)
```

### Desde Línea de Comandos

```bash
# Procesar archivo con URLs
python main.py --input urls.txt --output productos.json

# Solo extraer datos sin subir
python main.py --input urls.txt --extract-only

# Forzar re-extracción de imágenes
python main.py --input urls.txt --redownload-images
```

### Formato de Archivo de Entrada

El archivo de entrada debe contener una URL por línea:

```
https://tienda1.com/producto-abc
https://tienda2.com/item-xyz
https://tienda3.com/product/123
```

## 🔧 Configuración de WooCommerce

### Habilitar REST API

1. Ir a **WooCommerce > Ajustes > Avanzado > REST API**
2. Crear nuevas claves de API con permisos de lectura/escritura
3. Guardar el Consumer Key y Consumer Secret

### Permisos Requeridos

- `read_products`
- `write_products` 
- `read_media`
- `write_media`

## 📊 Datos Extraídos

El sistema extrae y procesa la siguiente información:

### Información Básica
- ✅ Nombre del producto
- ✅ Descripción completa
- ✅ Descripción corta
- ✅ Precio regular y de oferta
- ✅ SKU/Código de producto

### Imágenes
- ✅ Imagen principal
- ✅ Galería de imágenes
- ✅ Optimización y redimensionamiento
- ✅ Metadatos ALT y título

### Categorización
- ✅ Categorías principales
- ✅ Etiquetas y tags
- ✅ Atributos personalizados

### Inventario
- ✅ Stock disponible
- ✅ Gestión de inventario
- ✅ Estado del producto (publicado/borrador)

## 🐛 Manejo de Errores

El sistema incluye manejo robusto de errores:

- **Reintentos automáticos** en fallos de red
- **Logging detallado** para debugging
- **Validación de datos** antes de la importación
- **Respaldo de datos** extraídos

## 📝 Logs

Los logs se guardan en la carpeta `logs/` con los siguientes niveles:
- `scraper.log`: Proceso de scraping
- `importer.log`: Importación a WooCommerce  
- `errors.log`: Errores y excepciones

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ⚠️ Disclaimer

Este software está diseñado para uso educativo y en entornos controlados. Asegúrate de cumplir con:
- Los términos de servicio de los sitios web scrapeados
- Las leyes de protección de datos aplicables
- Las políticas de uso de la API de WooCommerce

## 🆘 Soporte

Si encuentras algún problema:
1. Revisa los logs en `logs/`
2. Verifica la configuración de WooCommerce API
3. Asegúrate de que las URLs sean accesibles
4. Abre un issue en el repositorio con la información del error

---

**¿Listo para comenzar?** Consulta [QUICKSTART.md](docs/QUICKSTART.md) para una guía rápida de instalación y uso.