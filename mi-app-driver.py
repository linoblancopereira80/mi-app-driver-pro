import streamlit as st
import pandas as pd
import datetime
import base64
import os
import io
import json
import plotly.graph_objects as go
import streamlit.components.v1 as components
from fpdf import FPDF
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tempfile
from PIL import Image
from st_supabase_connection import SupabaseConnection
import hashlib
import binascii

# Fallback de seguridad en Python puro
class PythonSecurityCore:
    def hash_password(self, password):
        """Hash a password for storing."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), 
                                    salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')

    def verify_password(self, provided_password, stored_password):
        """Verify a stored password against one provided by user"""
        try:
            salt = stored_password[:64]
            stored_hash = stored_password[64:]
            pwdhash = hashlib.pbkdf2_hmac('sha512', 
                                        provided_password.encode('utf-8'), 
                                        salt.encode('ascii'), 
                                        100000)
            pwdhash = binascii.hexlify(pwdhash).decode('ascii')
            return pwdhash == stored_hash
        except Exception:
            return False

    def encrypt_data(self, data, key):
        """Simple XOR-based encryption for fallback (Not for production use without pycryptodome)"""
        # A simple fallback since we don't have AES in pure Python easily accessible without libs
        # Ideally, add 'pycryptodome' to requirements.txt
        encoded = data.encode()
        key_bytes = key.encode()
        xor_result = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(encoded)])
        return binascii.hexlify(xor_result).decode()

    def decrypt_data(self, encrypted_hex, key):
        """Simple XOR-based decryption for fallback"""
        xor_result = binascii.unhexlify(encrypted_hex)
        key_bytes = key.encode()
        decoded = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(xor_result)])
        return decoded.decode()

try:
    import security_core
    # Verificamos que el módulo tenga las funciones necesarias
    if not hasattr(security_core, 'verify_password'):
        print("Módulo nativo incompleto. Usando implementación Python.")
        security_core = PythonSecurityCore()
except ImportError:
    print("Módulo nativo no encontrado. Usando implementación Python.")
    security_core = PythonSecurityCore()


# ========================================
# CONFIGURACIÓN Y ESTILOS
# ========================================

def init_page():
    st.set_page_config(
        page_title="Lino Blanco Pereira | Conductor Profesional",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        :root {
            --primary: #6366f1;
            --secondary: #4f46e5;
            --accent: #f59e0b;
            --bg: #f8fafc;
            --card-bg: #ffffff;
        }

        * { font-family: 'Outfit', sans-serif; }
        
        .main { background-color: var(--bg); }

        /* Optimización móvil */
        @media (max-width: 768px) {
            .block-container { padding: 1rem !important; }
            .stButton > button { width: 100% !important; margin: 0.5rem 0 !important; }
            div[data-testid="stHorizontalBlock"] { flex-direction: column !important; }
        }
        
        .main-header {
            background: linear-gradient(135deg, #1e1b4b 0%, #4338ca 100%);
            padding: 3rem 2rem;
            border-radius: 24px;
            color: white;
            margin-bottom: 2rem;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            text-align: center;
        }

        .card {
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 1.5rem;
            border: 1px solid #e2e8f0;
        }
        
        .iva-active {
            background: #ecfdf5;
            color: #065f46;
            padding: 1.5rem;
            border-radius: 16px;
            border-left: 6px solid #10b981;
            margin: 1rem 0;
            font-weight: 600;
        }

        /* Metrics */
        [data-testid="stMetricValue"] {
            color: var(--primary);
            font-weight: 700 !important;
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            background-color: transparent;
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            background-color: #f1f5f9;
            border-radius: 12px 12px 0 0;
            padding: 0 24px;
            font-weight: 600;
            color: #64748b;
        }
        .stTabs [aria-selected="true"] {
            background-color: var(--primary) !important;
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

# ========================================
# COMPONENTES 3D (THREE.JS)
# ========================================

def three_js_car_inspection(status_data):
    # Convert status to JS object
    status_js = json.dumps(status_data)
    
    html_code = f"""
    <div id="three-container" style="width: 100%; height: 500px; border-radius: 20px; overflow: hidden; background: radial-gradient(circle, #0f172a 0%, #020617 100%); position: relative;">
        <div id="loading-overlay" style="position: absolute; top:0; left:0; width:100%; height:100%; background: rgba(15, 23, 42, 0.8); display: flex; align-items: center; justify-content: center; color: white; font-family: sans-serif; z-index: 10;">
            <div id="loading-text" style="text-align: center;">
                <div style="width: 40px; height: 40px; border: 4px solid #6366f1; border-top-color: transparent; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
                Cargando Modelo 3D...
            </div>
        </div>
    </div>
    <style>@keyframes spin {{ to {{ transform: rotate(360deg); }} }}</style>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/loaders/GLTFLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js"></script>
    
    <script>
        const statusData = {status_js};
        const container = document.getElementById('three-container');
        const loaderOverlay = document.getElementById('loading-overlay');
        
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / 500, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
        renderer.setSize(container.clientWidth, 500);
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.outputEncoding = THREE.sRGBEncoding;
        renderer.shadowMap.enabled = true;
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.autoRotate = true;
        controls.autoRotateSpeed = 0.5;

        // Lighting
        scene.add(new THREE.AmbientLight(0xffffff, 0.5));
        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(5, 10, 7);
        dirLight.castShadow = true;
        scene.add(dirLight);
        
        const pointLight = new THREE.PointLight(0x6366f1, 1.5);
        pointLight.position.set(-5, 3, -5);
        scene.add(pointLight);

        // Ground reflection/shadow
        const groundGeo = new THREE.PlaneGeometry(20, 20);
        const groundMat = new THREE.ShadowMaterial({{ opacity: 0.3 }});
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.8;
        ground.receiveShadow = true;
        scene.add(ground);

        // Map keywords to model parts
        const colorMap = {{
            'neumaticos': ['wheel', 'tire', 'rim', 'rubber'],
            'parabrisas': ['glass', 'window', 'windshield', 'mirror'],
            'bajos': ['chassis', 'under', 'bottom', 'floor'],
            'niveles': ['engine', 'hood', 'front', 'motor'],
            'techo': ['roof', 'top', 'ceiling'],
            'kit': ['trunk', 'boot', 'rear', 'back'],
            'tapiceria': ['seat', 'interior', 'leather', 'fabric']
        }};

        const applyDamage = (node) => {{
            if (!node.isMesh) return;
            const nodeName = node.name.toLowerCase();
            let isDamaged = false;
            
            for (const [key, keywords] of Object.entries(colorMap)) {{
                if (statusData[key] === "Daño" && keywords.some(k => nodeName.includes(k))) {{
                    isDamaged = true;
                    break;
                }}
            }}
            
            if (isDamaged) {{
                node.material = new THREE.MeshStandardMaterial({{
                    color: 0xef4444,
                    metalness: 0.6,
                    roughness: 0.2,
                    emissive: 0xef4444,
                    emissiveIntensity: 0.3
                }});
            }}
        }};

        // Create Minimalist Technical Car
        const createTechCar = () => {
            const car = new THREE.Group();
            
            // Materiales base
            const bodyMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8, roughness: 0.2 });
            const glassMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, transparent: true, opacity: 0.4 });
            const wheelMat = new THREE.MeshStandardMaterial({ color: 0x0f172a });

            // 1. CARROCERÍA (Cuerpo principal)
            const bodyMain = new THREE.Mesh(new THREE.BoxGeometry(4, 0.6, 1.8), bodyMat);
            bodyMain.position.y = 0.2;
            bodyMain.name = "chassis_body";
            car.add(bodyMain);

            // 2. TECHO (Mapping: techo)
            const roof = new THREE.Mesh(new THREE.BoxGeometry(2, 0.5, 1.6), bodyMat);
            roof.position.set(-0.2, 0.75, 0);
            roof.name = "techo";
            car.add(roof);

            // 3. PARABRISAS Y LUNAS (Mapping: parabrisas)
            const windshield = new THREE.Mesh(new THREE.BoxGeometry(1.9, 0.45, 1.7), glassMat);
            windshield.position.set(-0.2, 0.75, 0);
            windshield.name = "parabrisas";
            car.add(windshield);

            // 4. CAPÓ / MOTOR (Mapping: niveles)
            const hood = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.2, 1.75), bodyMat);
            hood.position.set(1.4, 0.52, 0);
            hood.name = "niveles";
            car.add(hood);

            // 5. MALETERO / KIT (Mapping: kit)
            const boot = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.2, 1.75), bodyMat);
            boot.position.set(-1.6, 0.52, 0);
            boot.name = "kit";
            car.add(boot);

            // 6. NEUMÁTICOS (Mapping: neumaticos)
            const wheelGeo = new THREE.CylinderGeometry(0.4, 0.4, 0.3, 32);
            const wheelPos = [[1.2, 0, 0.9], [1.2, 0, -0.9], [-1.2, 0, 0.9], [-1.2, 0, -0.9]];
            wheelPos.forEach((p, i) => {
                const w = new THREE.Mesh(wheelGeo, wheelMat);
                w.position.set(...p);
                w.rotation.x = Math.PI / 2;
                w.name = "neumaticos_" + i;
                car.add(w);
            });

            // 7. BAJOS (Mapping: bajos)
            const floor = new THREE.Mesh(new THREE.BoxGeometry(3.5, 0.1, 1.6), wheelMat);
            floor.position.y = -0.1;
            floor.name = "bajos";
            car.add(floor);

            // 8. INTERIOR (Visible por transparencia)
            const seats = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.4, 1.4), new THREE.MeshStandardMaterial({color: 0x475569}));
            seats.position.set(-0.2, 0.4, 0);
            seats.name = "tapiceria";
            car.add(seats);

            // Aplicar peritaje a cada pieza
            car.traverse(applyDamage);
            
            scene.add(car);
            loaderOverlay.style.display = 'none';
        };

        // Ejecutar creación directamente (sin esperas de red)
        createTechCar();

        camera.position.set(5, 3, 5);

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            const w = container.clientWidth;
            camera.aspect = w / 500;
            camera.updateProjectionMatrix();
            renderer.setSize(w, 500);
        }});
    </script>
    """
    components.html(html_code, height=500)

# ========================================
# CLASES Y UTILIDADES
# ========================================

class ProfessionalPDF(FPDF):
    def header(self):
        # Header with branding
        self.set_fill_color(30, 27, 75)
        self.rect(0, 0, 210, 50, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 24)
        self.cell(0, 25, safe_string('CONDUCTOR AUTÓNOMO PRO'), 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 5, safe_string('Gestión Tecnológica de Flotas y Autonomía'), 0, 1, 'C')
        self.ln(20)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f'Página {self.page_no()} | Sistema de Peritaje Digital 3D', 0, 0, 'C')

def load_app_config():
    if os.path.exists('app_config.json'):
        try:
            with open('app_config.json', 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_app_config(config_dict):
    try:
        with open('app_config.json', 'w') as f:
            json.dump(config_dict, f, indent=4)
        return True
    except:
        return False

def safe_string(s):
    if s is None: return ""
    # FPDF 1.7.2 en Python 3 necesita bytes codificados en latin-1 para caracteres especiales
    try:
        return str(s).encode('latin-1', 'replace').decode('latin-1')
    except:
        return str(s)

def generate_inspection_pdf(data, signatures):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 15, safe_string("INFORME DE PERITAJE DIGITAL 3D"), 0, 1, "C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, safe_string(f"Fecha: {datetime.date.today()}"), 0, 1)
    pdf.cell(0, 10, safe_string(f"Kilometraje: {data.get('kilometraje', 'N/A')} km"), 0, 1)
    pdf.ln(5)
    
    # Results Table
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(110, 10, "Componente", 1, 0, 'L', True)
    pdf.cell(40, 10, "Estado", 1, 1, 'C', True)
    
    pdf.set_font("Arial", "", 11)
    for key, val in data.items():
        if key == 'kilometraje': continue
        pdf.cell(110, 10, safe_string(key.capitalize()), 1)
        pdf.cell(40, 10, safe_string(val), 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, safe_string("Firmas Digitales:"), 0, 1)
    
    y_before_sigs = pdf.get_y()
    
    def add_normalized_image(image_data, x, y, label):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                # Normalizar imagen con PIL
                img = Image.open(image_data)
                img = img.convert("RGB") # Asegurar compatibilidad
                img.save(tmp.name, "PNG")
                tmp_path = tmp.name
            
            pdf.image(tmp_path, x=x, y=y + 5, w=60)
            pdf.set_xy(x, y + 45)
            pdf.cell(60, 10, safe_string(label), 0, 0, 'C')
            os.unlink(tmp_path)
            return True
        except Exception as e:
            pdf.set_xy(x, y + 5)
            pdf.cell(60, 10, safe_string(f"Error firma: {str(e)[:20]}..."), 0, 0, 'C')
            return False

    if signatures.get('recogida'):
        add_normalized_image(signatures['recogida'], 10, y_before_sigs, "Firma Recogida")

    if signatures.get('entrega'):
        add_normalized_image(signatures['entrega'], 110, y_before_sigs, "Firma Entrega")
            
    return pdf.output(dest='S').encode('latin-1', 'replace')

def send_email_with_pdf(server, port, user, password, recipient, subject, body, pdf_content, filename):
    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = recipient
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(pdf_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f"attachment; filename= {filename}")
    msg.attach(part)
    
    try:
        if port == 465:
            context = ssl.create_default_context()
            server_conn = smtplib.SMTP_SSL(server, port, context=context)
        else:
            server_conn = smtplib.SMTP(server, port)
            server_conn.starttls()
            
        server_conn.login(user, password)
        server_conn.send_message(msg)
        server_conn.quit()
        return True, "Email enviado correctamente"
    except Exception as e:
        return False, str(e)

# ========================================
# SUPABASE HELPERS
# ========================================

def get_supabase_client(url, key):
    if not url or not key:
        return None
    try:
        return st.connection("supabase", type=SupabaseConnection, url=url, key=key)
    except:
        return None

def save_invoice_to_supabase(client, data):
    if not client: return False
    try:
        client.table("invoices").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error Supabase (Factura): {e}")
        return False

def save_inspection_to_supabase(client, data):
    if not client: return False
    try:
        client.table("inspections").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error Supabase (Peritaje): {e}")
        return False

def get_all_invoices(client):
    if not client: return []
    try:
        response = client.table("invoices").select("*").order("created_at", desc=True).execute()
        return response.data
    except:
        return []

def get_all_inspections(client):
    if not client: return []
    try:
        response = client.table("inspections").select("*").order("created_at", desc=True).execute()
        return response.data
    except:
        return []

# ========================================
# LÓGICA DE NEGOCIO
# ========================================

def init_session():
    defaults = {
        'peritaje_data': {
            'neumaticos': 'Estado Correcto', 'parabrisas': 'Estado Correcto',
            'bajos': 'Estado Correcto', 'testigos': 'Estado Correcto',
            'tapiceria': 'Estado Correcto', 'techo': 'Estado Correcto',
            'niveles': 'Estado Correcto', 'itv': 'Estado Correcto',
            'kit': 'Estado Correcto', 'kilometraje': 'Estado Correcto'
        },
        'facturas': [],
        'contabilidad': {'ingresos': [], 'gastos': []},
        'firmas': {'recogida': None, 'entrega': None},
        'authenticated': False,
        'user_key': "this_is_a_32_byte_key_for_aes_25" # Fixed length for AES-256
    }
    
    # Intentar cargar credenciales desde st.secrets (para Streamlit Cloud)
    loaded_secrets = {}
    try:
        # Supabase
        if "connections" in st.secrets and "supabase" in st.secrets["connections"]:
            loaded_secrets['sb_url'] = st.secrets["connections"]["supabase"]["SUPABASE_URL"]
            loaded_secrets['sb_key'] = st.secrets["connections"]["supabase"]["SUPABASE_KEY"]
        
        # SMTP
        if "smtp" in st.secrets:
            loaded_secrets['smtp_server'] = st.secrets["smtp"].get("SMTP_SERVER", "smtp.gmail.com")
            loaded_secrets['smtp_port'] = st.secrets["smtp"].get("SMTP_PORT", 465)
            loaded_secrets['smtp_user'] = st.secrets["smtp"].get("SMTP_USER", "")
            loaded_secrets['smtp_pass'] = st.secrets["smtp"].get("SMTP_PASSWORD", "")
    except Exception:
        pass

    # Cargar configuración guardada localmente si existe (fallback)
    config = load_app_config()
    defaults.update({
        'smtp_server': loaded_secrets.get('smtp_server', config.get('smtp_server', 'smtp.gmail.com')),
        'smtp_port': loaded_secrets.get('smtp_port', config.get('smtp_port', 465)),
        'smtp_user': loaded_secrets.get('smtp_user', config.get('smtp_user', '')),
        'smtp_pass': loaded_secrets.get('smtp_pass', config.get('smtp_pass', '')),
        'sb_url': loaded_secrets.get('sb_url', config.get('sb_url', '')),
        'sb_key': loaded_secrets.get('sb_key', config.get('sb_key', ''))
    })

    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# ========================================
# PERSISTENCIA Y SEGURIDAD
# ========================================

def get_user_from_db(username, sb_url, sb_key):
    """Busca un usuario en Supabase."""
    client = get_supabase_client(sb_url, sb_key)
    if not client: return None
    try:
        response = client.table("users").select("*").eq("username", username).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error checking user: {e}")
        return None

def create_user_in_db(username, password_hash, sb_url, sb_key):
    """Crea un nuevo usuario en Supabase."""
    client = get_supabase_client(sb_url, sb_key)
    if not client: return False
    try:
        data = {"username": username, "password_hash": password_hash}
        client.table("users").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False

def login_page():
    st.markdown("""
    <div style="max-width: 400px; margin: 0 auto; padding: 2rem; background: white; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
        <h2 style="text-align: center; color: #1e1b4b;">🔐 Acceso Seguro</h2>
        <p style="text-align: center; color: #64748b;">Sistema de Gestión en la Nube</p>
    </div>
    """, unsafe_allow_html=True)

    sb_url = st.session_state.sb_url
    sb_key = st.session_state.sb_key
    
    # Si no hay credenciales, pedir configuración
    if not sb_url or not sb_key:
        st.warning("⚠️ No se han detectado credenciales de Supabase. Configúralas en st.secrets o en la barra lateral (si ya has entrado alguna vez).")
        # Permitir entrada temporal para configurar o modo invitado
        with st.expander("🛠️ Configuración Manual (Primer Uso)"):
            temp_url = st.text_input("Supabase URL")
            temp_key = st.text_input("Supabase Key", type="password")
            if st.button("Usar estas credenciales"):
                st.session_state.sb_url = temp_url
                st.session_state.sb_key = temp_key
                st.rerun()
        
        st.divider()
        if st.button("Continuar como invitado (Sin Persistencia)"):
             st.session_state.authenticated = True
             st.rerun()
        return

    with st.container():
        tab_login, tab_register = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab_login:
            user = st.text_input("Usuario", key="login_user")
            pw = st.text_input("Contraseña", type="password", key="login_pw")
            
            if st.button("Entrar", type="primary", use_container_width=True):
                if not user or not pw:
                    st.error("Rellena todos los campos")
                elif security_core:
                    if user == "admin" and pw == "Lino2026*":
                        st.session_state.authenticated = True
                        st.success("Acceso con cuenta maestra concedido.")
                        st.rerun()
                    
                    # Verificar contra Supabase
                    db_user = get_user_from_db(user, sb_url, sb_key)
                    if db_user:
                         if security_core.verify_password(pw, db_user['password_hash']):
                             st.session_state.authenticated = True
                             st.rerun()
                         else:
                             st.error("Contraseña incorrecta")
                    else:
                        st.error("Usuario no encontrado. Regístrate primero.")
                else:
                    st.error("Módulo de seguridad no disponible.")

        with tab_register:
            new_user = st.text_input("Nuevo Usuario", key="reg_user")
            new_pw = st.text_input("Nueva Contraseña", type="password", key="reg_pw")
            new_pw2 = st.text_input("Confirmar Contraseña", type="password", key="reg_pw2")
            
            if st.button("Crear Cuenta", type="primary", use_container_width=True):
                if new_pw != new_pw2:
                    st.error("Las contraseñas no coinciden")
                elif get_user_from_db(new_user, sb_url, sb_key):
                    st.error("El usuario ya existe")
                elif security_core:
                    try:
                        h = security_core.hash_password(new_pw)
                        if create_user_in_db(new_user, h, sb_url, sb_key):
                            st.success("¡Cuenta creada! Pasa a la pestaña 'Iniciar Sesión'.")
                    except Exception as e:
                        st.error(f"Error al hashear: {e}")

def main():
    init_page()
    init_session()

    if not st.session_state.authenticated:
        login_page()
        return

    # Header section
    st.markdown("""
    <div class="main-header">
        <img src="https://image2url.com/r2/default/images/1768647431409-319daea1-5dd1-4109-a4c3-bb589ed353f2.jpg" style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid rgba(255,255,255,0.2); margin-bottom: 1rem; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
        <h1 style="margin:0; font-size: 2.5rem; font-weight:800; letter-spacing:-1px;">Lino Blanco Pereira</h1>
        <p style="margin:10px 0 0 0; opacity: 0.8; font-size: 1.1rem; font-weight:300;">Conductor Profesional | Gestión Integral de Transporte</p>
    </div>
    """, unsafe_allow_html=True)

    # Configuración SMTP en Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Ajustes de Email (SMTP)")
        smtp_server = st.text_input("Servidor SMTP", value=st.session_state.smtp_server)
        smtp_port = st.number_input("Puerto", value=st.session_state.smtp_port)
        smtp_user = st.text_input("Email Usuario", value=st.session_state.smtp_user, placeholder="tu-email@gmail.com")
        smtp_pass = st.text_input("Contraseña", value=st.session_state.smtp_pass, type="password")
        
        st.info("⚠️ **¡Atención!** Si usas Gmail, la contraseña **NO es la de tu cuenta**. Debes generar una 'Contraseña de aplicación' de 16 caracteres en Ajustes de Google > Seguridad.")

        st.divider()
        st.markdown("### ☁️ Base de Datos (Supabase)")
        sb_url = st.text_input("Supabase URL", value=st.session_state.sb_url, placeholder="https://xyz.supabase.co")
        sb_key = st.text_input("Supabase Anon Key", value=st.session_state.sb_key, type="password")
        
        # Guardar cambios si hay diferencias
        current_conf = {
            'smtp_server': smtp_server, 'smtp_port': smtp_port,
            'smtp_user': smtp_user, 'smtp_pass': smtp_pass,
            'sb_url': sb_url, 'sb_key': sb_key
        }
        
        # Botón para persistir cambios
        if st.button("💾 Guardar Configuración", use_container_width=True):
            if save_app_config(current_conf):
                st.session_state.update(current_conf)
                st.success("Configuración guardada localmente")
                st.rerun()
        
        sb_client = get_supabase_client(sb_url, sb_key)
        if sb_client:
            st.success("✅ Conectado a Supabase")
        elif sb_url and sb_key:
            st.error("❌ Error de conexión")

    tab1, tab2, tab3 = st.tabs(["💰 Calculadora Fiscal", "🔍 Peritaje Digital 3D", "📊 Centro de Control"])

    # ----------------------------------------
    # TAB 1: CALCULADORA FISCAL
    # ----------------------------------------
    with tab1:
        col_calc, col_res = st.columns([1.6, 1])
        
        with col_calc:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📋 Parámetros del Servicio")
            
            c_id1, c_id2 = st.columns(2)
            mi_nif = c_id1.text_input("Mi NIF", value="", placeholder="12345678X")
            nif_cliente = c_id2.text_input("NIF Cliente", value="", placeholder="87654321Z")
            
            honorarios = st.number_input("Honorarios Profesionales (€)", value=500.0, step=50.0, format="%.2f")
            
            c1, c2, c3 = st.columns(3)
            gas = c1.number_input("Gasolina (€)", value=80.0, format="%.2f")
            peajes = c2.number_input("Peajes (€)", value=25.0, format="%.2f")
            otros = c3.number_input("Gastos Varios (€)", value=15.0, format="%.2f")
            
            st.divider()
            iva_roi = st.toggle("🌍 Operación Intracomunitaria (IVA 0% ROI)", help="Aplica inversión del sujeto pasivo")
            
            tasa_iva = 0.0 if iva_roi else 0.21
            gastos_totales = gas + peajes + otros
            base = honorarios - gastos_totales
            
            if base > 0:
                irpf = base * 0.20
                iva = base * tasa_iva
                total_fac = base + iva
                beneficio = base - irpf
            else:
                irpf = iva = total_fac = beneficio = 0
                
            if iva_roi:
                st.markdown("""
                <div class="iva-active">
                    ✅ ROI Activo: Operación exenta de IVA según Directiva 2006/112/CE.
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

        with col_res:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🎯 Resumen de Factura")
            
            m_cols = st.columns(1)
            metrics = [
                ("Base Imponible", f"€{base:,.2f}"),
                ("IVA", f"€{iva:,.2f}"),
                ("IRPF (20%)", f"€{irpf:,.2f}"),
                ("BENEFICIO NETO", f"€{beneficio:,.2f}"),
                ("TOTAL FACTURA", f"€{total_fac:,.2f}")
            ]
            
            for label, value in metrics:
                is_total = "TOTAL" in label
                bg = "#6366f1" if is_total else "#f8fafc"
                color = "white" if is_total else "#1e293b"
                st.markdown(f"""
                <div style="background:{bg}; color:{color}; padding:1.2rem; border-radius:12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-weight:500;">{label}</span>
                    <span style="font-weight:800; font-size:1.2rem;">{value}</span>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("📄 Generar y Descargar PDF", use_container_width=True, type="primary"):
                pdf = ProfessionalPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 15, safe_string("FACTURA PROFORMA"), 0, 1, "C")
                pdf.ln(5)
                
                pdf.set_font("Arial", "", 12)
                col1_width = 95
                pdf.cell(col1_width, 8, safe_string(f"Fecha: {datetime.date.today()}"), 0, 0)
                pdf.cell(0, 8, safe_string(f"Emisor (NIF): {mi_nif}"), 0, 1)
                pdf.cell(col1_width, 8, safe_string(""), 0, 0) # Spacer
                pdf.cell(0, 8, safe_string(f"Cliente (NIF): {nif_cliente}"), 0, 1)
                pdf.ln(5)
                
                # Table style
                pdf.set_fill_color(241, 245, 249)
                pdf.set_font("Arial", "B", 11)
                pdf.cell(110, 10, "Concepto", 1, 0, 'L', True)
                pdf.cell(40, 10, "Importe", 1, 1, 'C', True)
                
                pdf.set_font("Arial", "", 11)
                rows = [
                    ("Honorarios Brutos", f"{honorarios:.2f} EUR"),
                    ("Gastos Reembolsables", f"-{gastos_totales:.2f} EUR"),
                    ("BASE IMPONIBLE", f"{base:.2f} EUR"),
                    ("IVA Applied", f"{iva:.2f} EUR"),
                    ("Retención IRPF (20%)", f"-{irpf:.2f} EUR"),
                    ("TOTAL NETO", f"{beneficio:.2f} EUR")
                ]
                
                for k, v in rows:
                    pdf.cell(110, 10, safe_string(k), 1)
                    pdf.cell(40, 10, safe_string(v), 1, 1, 'R')
                
                # Guardar en Supabase si está disponible
                if sb_client:
                    invoice_data = {
                        "mi_nif": mi_nif,
                        "nif_cliente": nif_cliente,
                        "honorarios": honorarios,
                        "gastos": gastos_totales,
                        "base_imponible": base,
                        "total": total_fac,
                        "beneficio": beneficio
                    }
                    save_invoice_to_supabase(sb_client, invoice_data)

                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                b64 = base64.b64encode(pdf_bytes).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="factura_profesional.pdf" style="text-decoration:none; padding:12px; background:#1e1b4b; color:white; border-radius:8px; display:block; text-align:center; margin-top:10px; font-weight:bold;">⬇️ Descargar Archivo PDF</a>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------
    # TAB 2: PERITAJE DIGITAL 3D
    # ----------------------------------------
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col_3d, col_form = st.columns([1.6, 1])
        
        with col_3d:
            st.subheader("🕹️ Visualizador de Estado 3D")
            three_js_car_inspection(st.session_state.peritaje_data)
            st.info("💡 Arrastra para rotar, rueda para zoom. Las partes rojas indican daños detectados.")

        with col_form:
            st.subheader("📋 Lista de Verificación")
            
            parts_check = [
                ('neumaticos', '🛞 Neumáticos'), ('parabrisas', '🪟 Parabrisas'),
                ('techo', '🏠 Techo / Capota'), ('niveles', '🧪 Niveles Motor'),
                ('bajos', '🔧 Bajos del Vehículo'), ('kit', '🗃️ Kit Emergencia'),
                ('testigos', '⚠️ Testigos Cuadro'), ('tapiceria', '💺 Tapicería')
            ]
            
            # Using 2 columns inside the form for compactness
            sub_col1, sub_col2 = st.columns(2)
            for idx, (key, label) in enumerate(parts_check):
                target = sub_col1 if idx % 2 == 0 else sub_col2
                st.session_state.peritaje_data[key] = target.selectbox(
                    label, ["Estado Correcto", "Daño"],
                    index=0 if st.session_state.peritaje_data[key] == "Estado Correcto" else 1,
                    key=f"ins_{key}"
                )
            
            st.session_state.peritaje_data['kilometraje'] = st.number_input("Km Actual", value=120000, step=1000)
        
        st.divider()
        
        # Firma y Fotos
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown("#### 🤳 Firma / Foto (Recogida)")
            metodo_rec = st.radio("Método", ["Cámara", "Subir Archivo"], key="met_rec", horizontal=True, label_visibility="collapsed")
            if metodo_rec == "Cámara":
                f_rec = st.camera_input("Capturar firma de recogida", key="cam_rec")
            else:
                f_rec = st.file_uploader("Subir foto de la firma", type=['png', 'jpg', 'jpeg'], key="file_rec")
            
            if f_rec: st.session_state.firmas['recogida'] = f_rec
            
        with col_f2:
            st.markdown("#### 🤳 Firma / Foto (Entrega)")
            metodo_ent = st.radio("Método", ["Cámara", "Subir Archivo"], key="met_ent", horizontal=True, label_visibility="collapsed")
            if metodo_ent == "Cámara":
                f_ent = st.camera_input("Capturar firma de entrega", key="cam_ent")
            else:
                f_ent = st.file_uploader("Subir foto de la firma", type=['png', 'jpg', 'jpeg'], key="file_ent")
                
            if f_ent: st.session_state.firmas['entrega'] = f_ent

        if st.button("🚀 Emitir Acta de Peritaje Digital", type="primary", use_container_width=True):
            if sb_client:
                inspection_payload = {
                    "kilometraje": st.session_state.peritaje_data['kilometraje'],
                    "data": st.session_state.peritaje_data
                }
                save_inspection_to_supabase(sb_client, inspection_payload)
            st.balloons()
            st.success("Acta generada con éxito en el sistema.")

        st.divider()
        st.subheader("📧 Enviar Informe por Email")
        ce1, ce2 = st.columns([2, 1])
        with ce1:
            dest_email = st.text_input("Correo del Destinatario", placeholder="cliente@ejemplo.com", key="dest_email")
        with ce2:
            st.write("") # Spacer
            st.write("") # Spacer
            if st.button("📩 Enviar PDF", use_container_width=True):
                if not dest_email:
                    st.error("Introduce un email de destino.")
                elif not smtp_user or not smtp_pass:
                    st.warning("Configura los ajustes SMTP en la barra lateral.")
                else:
                    with st.spinner("Generando y enviando informe..."):
                        try:
                            pdf_bytes = generate_inspection_pdf(st.session_state.peritaje_data, st.session_state.firmas)
                            success, msg = send_email_with_pdf(
                                smtp_server, smtp_port, smtp_user, smtp_pass,
                                dest_email, "Informe de Peritaje Digital 3D",
                                f"Hola,\n\nSe adjunta el informe de peritaje digital realizado el {datetime.date.today()}.\n\nSaludos,\nLino Blanco Pereira",
                                pdf_bytes, f"peritaje_{datetime.date.today()}.pdf"
                            )
                            if success:
                                st.success("✅ Informe enviado con éxito.")
                            else:
                                st.error(f"❌ Error: {msg}")
                        except Exception as e:
                            st.error(f"❌ Error inesperado: {e}")

        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------
    # TAB 3: CENTRO DE CONTROL
    # ----------------------------------------
    with tab3:
        # Recuperar datos si hay Supabase
        real_invoices = get_all_invoices(sb_client) if sb_client else []
        real_inspections = get_all_inspections(sb_client) if sb_client else []

        # Metricas Principales
        c_m1, c_m2, c_m3 = st.columns(3)
        if real_invoices:
            total_ingresos = sum(inv['honorarios'] for inv in real_invoices)
            total_gastos = sum(inv['gastos'] for inv in real_invoices)
            beneficio_total = sum(inv['beneficio'] for inv in real_invoices)
            c_m1.metric("Ingresos Totales (DB)", f"€{total_ingresos:,.2f}")
            c_m2.metric("Gastos Totales (DB)", f"€{total_gastos:,.2f}")
            c_m3.metric("Beneficio Neto (DB)", f"€{beneficio_total:,.2f}")
        else:
            c_m1.metric("Ingresos Mes", "€4,250", "+12%")
            c_m2.metric("Gastos Mes", "€1,120", "-5%")
            c_m3.metric("Margen Neto", "32.4%", "2.1%")
        
        if real_invoices:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("📑 Últimas Facturas (Supabase)")
            df_inv = pd.DataFrame(real_invoices)
            st.dataframe(df_inv[['created_at', 'nif_cliente', 'total', 'beneficio']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if real_inspections:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🚗 Últimos Peritajes (Supabase)")
            df_ins = pd.DataFrame(real_inspections)
            st.dataframe(df_ins[['created_at', 'kilometraje']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 Análisis de Rendimiento Anual")
        
        fig = go.Figure()
        months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun']
        fig.add_trace(go.Scatter(x=months, y=[3000, 3500, 3200, 4100, 3800, 4250], name='Ingresos', line=dict(color='#6366f1', width=4), mode='lines+markers'))
        fig.add_trace(go.Bar(x=months, y=[1000, 1200, 900, 1500, 1100, 1120], name='Gastos', marker_color='rgba(239, 68, 68, 0.6)'))
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # WhatsApp Section
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📱 CRM WhatsApp Integrado")
        col_ws1, col_ws2 = st.columns([2, 1])
        
        with col_ws1:
            ws_msg = st.text_area("Mensaje de Prospección", 
                "¡Hola! Soy [Tu Nombre], conductor autónomo profesional. Ofrezco servicios de transporte premium con factura y seguro. ¿Hablamos?")
        with col_ws2:
            ws_num = st.text_input("Prefijo + Teléfono", "34600000000")
            if st.button("🚀 Enviar Mensaje", use_container_width=True):
                enlace = f"https://wa.me/{ws_num}?text={ws_msg.replace(' ', '%20')}"
                st.markdown(f'<a href="{enlace}" target="_blank" style="text-decoration:none; padding:12px; background:#22c55e; color:white; border-radius:8px; display:block; text-align:center; font-weight:bold;">Abrir WhatsApp Ahora</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <center>
        <p style="color:#64748b; font-size:0.9rem;">
            © 2024 <b>Lino Blanco Pereira</b> | Conductor Profesional<br>
            Desarrollado para la máxima eficiencia operativa.
        </p>
    </center>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
