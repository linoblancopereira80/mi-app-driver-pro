# 🚗 Conductor Autónomo Pro v2.5

Sistema de gestión integral diseñado específicamente para conductores autónomos y profesionales del transporte. Esta aplicación combina herramientas financieras, gestión de flota y marketing en una interfaz optimizada para dispositivos móviles con tecnología 3D.

## 🌟 Características Principales

### 🔍 Peritaje Digital 3D
- **Visualizador Interactivo**: Modelo 3D del vehículo para realizar inspecciones visuales.
- **Feedback Visual**: Las partes del vehículo cambian a color rojo si se detectan daños (neumáticos, lunas, bajos, etc.).
- **Actas PDF**: Generación inmediata de informes de estado para el cliente.
- **Captura de Firmas**: Sistema listo para capturar firmas digitales en la entrega y recogida.

### 💰 Gestión Financiera Profesional
- **Calculadora de Tarifas**: Cálculo automático de Base Imponible, IVA e IRPF.
- **Soporte ROI**: Interruptor para operaciones intracomunitarias (IVA 0%).
- **Facturación PDF**: Crea y descarga facturas profesionales en segundos.
- **Control Trimestral**: Gráficos dinámicos para analizar ingresos, gastos y beneficio neto.

### 📱 Herramientas de Negocio (CRM)
- **WhatsApp Marketing**: Generador de mensajes profesionales listos para enviar a clientes.
- **Estadísticas de Conversión**: Panel para seguimiento de contactos y rentabilidad.
- **Exportación de Datos**: Descarga de informes en Excel y PDF.

## 🛠️ Tecnologías Utilizadas

- **Soporte Core**: [Streamlit](https://streamlit.io/)
- **Gráficos 3D**: [Three.js](https://threejs.org/)
- **Visualización de Datos**: [Plotly](https://plotly.com/)
- **Generación de Documentos**: [FPDF](http://www.fpdf.org/)
- **Diseño UI**: CSS Personalizado (Glassmorphism & Mobile First)

## 🚀 Instalación y Uso Local

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/linoblancopereira80/mi-app-driver.git
   cd mi-app-driver
   ```

2. **Crear y activar entorno virtual**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Ejecutar la aplicación**:
   ```bash
   streamlit run mi-app-driver.py
   ```

## 🔒 Privacidad y Seguridad
La aplicación procesa los datos localmente en la sesión del usuario. No se almacenan datos sensibles en servidores externos de forma predeterminada, garantizando la privacidad de la contabilidad y los datos de clientes.

---
**Desarrollado para la máxima eficiencia operativa del conductor autónomo moderno.**
