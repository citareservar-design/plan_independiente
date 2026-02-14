import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from flask import Flask, render_template, request, url_for # <--- Agrega 'request' aquí


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'reservas.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'config.json')

# --- Funciones de Configuración y I/O ---


def formatear_hora_12h(hora_24):
    """Convierte '14:00' a '02:00 PM'"""
    try:
        dt = datetime.strptime(hora_24, "%H:%M")
        return dt.strftime("%I:%M %p")
    except:
        return hora_24
    

# --- MODIFICACIÓN EN CARGAR_CONFIG ---
def cargar_config():
    """Carga la configuración desde el JSON o devuelve valores por defecto."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando config: {e}")
    
    # Valores de respaldo por si el archivo no existe o está mal escrito
    return {
        "empresa": "Mi Negocio", 
        "email_admin": "admin@mail.com",
        "horarios_base": ["08:00", "09:00", "10:00"],
        "servicios": {"General": 60}
    }

# --- ESTAS VARIABLES AHORA SON DINÁMICAS ---
# Reemplaza donde uses HORAS_DISPONIBLES y DURACION_SERVICIOS por esto:
config_data = cargar_config()
HORAS_DISPONIBLES = config_data.get("horarios_base", [])
DURACION_SERVICIOS = config_data.get("servicios", {})

# --- MODIFICACIÓN EN LAS FUNCIONES DE CORREO ---
def enviar_correo_generico(msg, config):
    """Función auxiliar para no repetir código de envío"""
    smtp_conf = config.get('smtp', {})
    try:
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error SMTP: {e}")
        return False

# Ejemplo de cómo queda ahora enviar_correo_confirmacion:
def enviar_correo_confirmacion(reserva, calendar_link, citas_link):
    config = cargar_config()
    empresa = config.get('empresa')
    smtp_conf = config.get('smtp', {})
    
    destinatario = reserva.get('email')
    
    try:
        msg = MIMEMultipart("alternative")
        # Usamos el email configurado en el JSON
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>" 
        msg['To'] = destinatario
        msg['Subject'] = f'📌 ¡Cita Confirmada! - {empresa}'
        
        # ... (aquí va tu html_body igual que antes) ...
        
        return enviar_correo_generico(msg, config)
    except:
        return False

def cargar_reservas():
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Error al cargar: {e}")
            return []
    return []

def guardar_reservas(reservas):
    try:
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(reservas, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Error al guardar reservas: {e}")

# --- Funciones de Utilidad ---
def format_google_calendar_datetime(date_str, time_str, duration_minutes):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start = dt.strftime("%Y%m%dT%H%M%S")
        end = (dt + timedelta(minutes=duration_minutes)).strftime("%Y%m%dT%H%M%S")
        return start, end
    except: return "", ""

def get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar):
    from datetime import datetime, timedelta
    
    horas_ocupadas = set()
    reservas_del_dia = [r for r in reservas if r.get("date") == str(fecha_a_mostrar)]
    
    for r in reservas_del_dia:
        try:
            # Hora en que inicia la cita (ej: 08:00)
            inicio = datetime.strptime(r['hora'], "%H:%M")
            # Cuánto dura (si no trae, por defecto 30 para ser coherentes ahora)
            duracion = int(r.get("duracion", 30)) 
            fin = inicio + timedelta(minutes=duracion)
            
            # Marcamos bloques de 30 minutos como ocupados dentro de ese rango
            check = inicio
            while check < fin:
                horas_ocupadas.add(check.strftime("%H:%M"))
                check += timedelta(minutes=30)
                
        except Exception as e:
            print(f"Error procesando reserva: {e}")
            continue
            
    return horas_ocupadas

# --- CORREOS ---



def enviar_correo_confirmacion(reserva, calendar_link, citas_link):
    
    
    base_url = request.host_url.rstrip('/')

    # Creamos las rutas completas para el email
    url_gif = f"{base_url}/static/gif/reagendar_cancelar.gif"
    email_cliente = reserva.get('email')
    # Construimos el link de gestión (ajusta la ruta /mis-citas si es diferente en tu app)
    url_gestionar = f"{base_url}/citas?email_cliente={email_cliente}"


    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    wpp = config.get('whatsapp', '')
    smtp_conf = config.get('smtp', {})
    
    # --- CONVERSIÓN DE HORA A FORMATO 12H ---
    try:
        hora_24 = reserva.get('hora', '00:00')
        hora_obj = datetime.strptime(hora_24, "%H:%M")
        # %I es hora 12h, %p es AM/PM. 
        # Usamos .lstrip("0") para que no diga "08:00 AM" sino "8:00 AM"
        hora_12h = hora_obj.strftime("%I:%M %p").lstrip("0")
    except Exception:
        hora_12h = reserva.get('hora') # Backup por si falla la conversión

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = reserva.get('email')
        
        email_admin = config.get('email_admin')
        if email_admin and email_admin != smtp_conf.get('email'):
            msg['Cc'] = email_admin
        
        msg['Subject'] = f'📌 ¡Cita Confirmada! - {empresa}'
        
        html_body = f"""
        <div style="font-family:sans-serif; padding:20px; background:#f1f5f9;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #e2e8f0; overflow:hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                
                <div style="background:#0ea5e9; padding:25px; text-align:center; color:white;">
                    <h2 style="margin:0; font-size:24px;">¡Todo listo!</h2>
                    <p style="margin:5px 0 0 0; opacity:0.9;">Tu cita ha sido confirmada</p>
                </div>

                <div style="padding:30px; color:#1e293b;">
                    <p style="font-size:16px;">Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p style="font-size:15px; line-height:1.6;">Tu cita para el servicio de <b>{reserva.get('tipo_una')}</b> se ha agendado correctamente.</p>
                    
                    <div style="background:#f8fafc; border-radius:12px; padding:20px; margin:25px 0; border:1px solid #f1f5f9;">
                        <p style="margin:0; font-size:15px; color:#64748b;">DETALLES DE LA RESERVA:</p>
                        <p style="margin:10px 0 5px 0; font-size:18px;">📅 <b>Día:</b> {reserva.get('date')}</p>
                        <p style="margin:0; font-size:18px;">⏰ <b>Hora:</b> {hora_12h}</p>
                    </div>
                    
                    <div style="text-align:center; margin:30px 0;">
                        <a href="{calendar_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block; margin-bottom:10px; width:80%;">📅 Agendar en mi Calendario</a><br>
                        <a href="{citas_link}" style="background:#64748b; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block; width:80%;">📋 Ver mis citas</a>
                    </div>
                    

<div style="margin-top: 30px; background-color: #f8fafc; border-radius: 24px; border: 1px solid #e2e8f0; overflow: hidden;">
    <div style="padding: 12px 20px; background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0; text-align: center;">
        <p style="margin: 0; font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">
            🎥 Así reagendas o cancelas
        </p>
    </div>

    <div style="padding: 20px; text-align: center;">
        <img src="{url_gif}" 
             alt="Tutorial de uso" 
             style="width: 100%; max-width: 350px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 4px solid white;">
        
        <div style="margin-top: 20px;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; font-weight: 500;">
                ¿Quieres reagendar o cancelar ahora?
            </p>
            <a href="{url_gestionar}" 
               style="color: #0ea5e9; font-size: 15px; font-weight: 800; text-decoration: none; border-bottom: 2px solid #0ea5e9; padding-bottom: 2px;">
                Gestionar mi cita aquí →
            </a>
        </div>
    </div>
</div>
                    
                    

                    <div style="margin-top:25px; padding:20px; background-color: #fff9f0; border-left: 4px solid #f59e0b; border-radius: 12px; color: #92400e;">
                        <p style="margin: 0 0 10px 0; font-size: 15px; font-weight: 800;">⏰ REGLAS DE ORO</p>
                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                            Para brindarte la mejor experiencia, por favor <b>llega 15 minutos antes</b> de tu cita. Si tienes algún inconveniente, avísanos de inmediato.
                        </p>
                        <div style="margin-top: 15px;">
                            <a href="https://wa.me/{wpp}" style="display: inline-block; background: #25d366; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px;">
                                📱 Escribir por WhatsApp
                            </a>
                        </div>
                    </div>

                    <div style="margin-top: 40px; text-align: center; border-top: 2px dashed #e2e8f0; padding-top: 30px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; margin-bottom: 10px;">¿Te gusta cómo reservaste?</p>
                        <div style="background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); padding: 25px; border-radius: 15px; color: white;">
                            <p style="margin: 0; font-weight: 900; font-size: 20px;">✨ AgendApp</p>
                            <p style="margin: 5px 0 20px 0; font-size: 13px; opacity: 0.9;">Lleva tu negocio al siguiente nivel con reservas automáticas.</p>
                            <a href="https://agendapp.co" style="background: white; color: #2563eb; padding: 10px 20px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block;">
                                🚀 CREAR MI SISTEMA - CONTACTANOS
                            </a>
                        </div>
                        <p style="margin-top: 20px; color: #94a3b8; font-size: 11px;">
                            © 2026 AgendApp 
                        </p>
                    </div>
                </div>
            </div>
        </div>"""
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port')) as server:
            server.starttls()
            server.login(smtp_conf.get('email'), smtp_conf.get('password'))
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False

def enviar_correo_reagendacion(reserva, calendar_link, citas_link=None):
    
    base_url = request.host_url.rstrip('/')

    # Creamos las rutas completas para el email
    url_gif = f"{base_url}/static/gif/reagendar_cancelar.gif"
    email_cliente = reserva.get('email')
    # Construimos el link de gestión (ajusta la ruta /mis-citas si es diferente en tu app)
    url_gestionar = f"{base_url}/citas?email_cliente={email_cliente}"
    
    
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    smtp_conf = config.get('smtp', {})
    wpp = config.get('whatsapp', '')
    
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        hora_24 = reserva.get('hora', '00:00')
        hora_obj = datetime.strptime(hora_24, "%H:%M")
        # %I es hora 12h, %p es AM/PM. 
        # Usamos .lstrip("0") para que no diga "08:00 AM" sino "8:00 AM"
        hora_12h = hora_obj.strftime("%I:%M %p").lstrip("0")
    except Exception:
            hora_12h = reserva.get('hora') # Backup por si falla la conversión
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'Cita Reagendada - {empresa}'

        html_body = f"""<div style="font-family:sans-serif; padding:20px; background:#fff7ed;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #fed7aa; overflow:hidden;">
                <div style="background:#f59e0b; padding:20px; text-align:center; color:white;"><h2>Cita Reagendada</h2></div>
                <div style="padding:20px;">
                     <p>Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p>Tu cita en <b>{empresa}</b> fue reprogramada con éxito. Te esperamos el <b>{reserva.get('date')}</b> a las <b>{hora_12h}</b>.</p>
                        <div style="text-align:center; margin:25px 0;">
                        <a href="{calendar_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;">
                           📅 Agregar a Google Calendar
                        </a>
                    </div>
                    <p style="margin-top:20px; font-size:12px; color:#94a3b8;">Si no solicitaste este cambio, por favor comunícate con nosotros.</p>
                </div>
                
                    <div style="margin-top: 30px; background-color: #f8fafc; border-radius: 24px; border: 1px solid #e2e8f0; overflow: hidden;">
                    <div style="padding: 12px 20px; background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0; text-align: center;">
                        <p style="margin: 0; font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">
                            🎥 Así reagendas o cancelas
                        </p>
                    </div>

<div style="margin-top: 30px; background-color: #f8fafc; border-radius: 24px; border: 1px solid #e2e8f0; overflow: hidden;">
    <div style="padding: 12px 20px; background-color: #f1f5f9; border-bottom: 1px solid #e2e8f0; text-align: center;">
        <p style="margin: 0; font-size: 11px; font-weight: 800; color: #475569; text-transform: uppercase; letter-spacing: 0.05em;">
            🎥 Así reagendas o cancelas
        </p>
    </div>

    <div style="padding: 20px; text-align: center;">
        <img src="{url_gif}" 
             alt="Tutorial de uso" 
             style="width: 100%; max-width: 350px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 4px solid white;">
        
        <div style="margin-top: 20px;">
            <p style="margin: 0 0 10px 0; font-size: 14px; color: #64748b; font-weight: 500;">
                ¿Quieres reagendar o cancelar ahora?
            </p>
            <a href="{url_gestionar}" 
               style="color: #0ea5e9; font-size: 15px; font-weight: 800; text-decoration: none; border-bottom: 2px solid #0ea5e9; padding-bottom: 2px;">
                Gestionar mi cita aquí →
            </a>
        </div>
    </div>
</div>


                    <div style="margin-top:25px; padding:20px; background-color: #fff9f0; border-left: 4px solid #f59e0b; border-radius: 12px; color: #92400e;">
                        <p style="margin: 0 0 10px 0; font-size: 15px; font-weight: 800;">⏰ REGLAS DE ORO</p>
                        <p style="margin: 0; font-size: 14px; line-height: 1.5;">
                            Para brindarte la mejor experiencia, por favor <b>llega 15 minutos antes</b> de tu cita. Si tienes algún inconveniente, avísanos de inmediato.
                        </p>
                        <div style="margin-top: 15px;">
                            <a href="https://wa.me/{wpp}" style="display: inline-block; background: #25d366; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 13px;">
                                📱 Escribir por WhatsApp
                            </a>
                        </div>
                    </div>

                     <div style="margin-top: 40px; text-align: center; border-top: 2px dashed #e2e8f0; padding-top: 30px;">
                        <p style="margin: 0; color: #64748b; font-size: 12px; text-transform: uppercase; margin-bottom: 10px;">¿Te gusta cómo reservaste?</p>
                        <div style="background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%); padding: 25px; border-radius: 15px; color: white;">
                            <p style="margin: 0; font-weight: 900; font-size: 20px;">✨ AgendApp</p>
                            <p style="margin: 5px 0 20px 0; font-size: 13px; opacity: 0.9;">Lleva tu negocio al siguiente nivel con reservas automáticas.</p>
                            <a href="https://agendapp.co" style="background: white; color: #2563eb; padding: 10px 20px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 12px; display: inline-block;">
                                🚀 CREAR MI SISTEMA - CONTACTANOS
                            </a>
                        </div>
                        <p style="margin-top: 20px; color: #94a3b8; font-size: 11px;">
                            © 2026 AgendApp 
                        </p>
                    </div>



            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))

        # Conexión SMTP dinámica
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error reagendando: {e}")
        return False

def enviar_correo_cancelacion(reserva):
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    smtp_conf = config.get('smtp', {})
    
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'Cita Cancelada - {empresa}'
        
        html_body = f"""
        <div style="font-family:sans-serif; padding:20px; background:#fef2f2;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #fecaca; overflow:hidden;">
                <div style="background:#ef4444; padding:20px; text-align:center; color:white;"><h2 style="margin:0;">Cita Cancelada</h2></div>
                <div style="padding:30px; color:#475569;">
                    <p>Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p>Te informamos que tu cita en <b>{empresa}</b> para el día <b>{reserva.get('date')}</b> ha sido <b>cancelada</b>.</p>
                    <div style="background:#f8fafc; padding:15px; border-radius:10px; margin-top:20px;">
                        <p style="margin:0;"><b>Servicio:</b> {reserva.get('tipo_una')}</p>
                    </div>
                    <div style="text-align:center; background:#f0f9ff; padding:15px; border-radius:12px; border:1px solid #e0f2fe;">
                <p style="margin:0; font-weight:bold; color:#0ea5e9; font-size:14px;">✨ Potenciado por AgendApp</p>
                <p style="margin:5px 0 10px 0; font-size:12px; color:#64748b;">¿Quieres un sistema de reservas como este?</p>
                <a href="https://agendapp.co" style="background:#0ea5e9; color:white; padding:6px 15px; text-decoration:none; border-radius:8px; font-size:11px; font-weight:bold; display:inline-block;">
                    🚀 Visítanos en agendapp.co
                </a>
            </div>
            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
                </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))

        # Conexión SMTP dinámica
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error cancelando: {e}")
        return False