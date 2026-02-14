from flask import Blueprint, render_template, session, request,flash,redirect,url_for
from datetime import datetime, timedelta # Añadimos timedelta
from utils.reservations import cargar_reservas, cargar_config, guardar_reservas, CONFIG_PATH
import json


admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/agenda')
def agenda():
    reservas = cargar_reservas()
    ahora = datetime.now()
    
    hoy = ahora.strftime("%Y-%m-%d")
    manana = (ahora + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 1. Filtramos las citas que sean de hoy O de mañana
    citas_proximas = [r for r in reservas if r.get('date') in [hoy, manana]]
    
    # 2. Ordenamos primero por fecha y luego por hora (formato 24h para ordenar bien)
    citas_proximas.sort(key=lambda x: (x['date'], x['hora']))

    # 3. --- CONVERSIÓN A 12 HORAS ---
    for cita in citas_proximas:
        try:
            # Tomamos la hora original (ej: "14:30")
            hora_obj = datetime.strptime(cita['hora'], "%H:%M")
            # Creamos el nuevo campo formateado (ej: "02:30 PM")
            cita['hora_formato_12'] = hora_obj.strftime("%I:%M %p")
        except Exception:
            # En caso de error, usamos la original como respaldo
            cita['hora_formato_12'] = cita['hora']

    return render_template('admin_agenda.html', 
                           citas=citas_proximas, 
                           hoy=hoy, 
                           manana=manana)


@admin_bp.route('/admin/config', methods=['GET', 'POST'])
def edit_config():
    config = cargar_config()
    
    # 1. VERIFICACIÓN DE ACCESO
    if not session.get('admin_logged_in'):
        if request.method == 'POST':
            password_ingresada = request.form.get('password')
            if password_ingresada == config.get('admin_password'):
                session['admin_logged_in'] = True
                flash("Sesión iniciada correctamente", "success")
                return redirect(url_for('admin.edit_config'))
            else:
                flash("Contraseña incorrecta", "danger")
        return render_template('admin_login.html')

    # 2. PROCESAR ACTUALIZACIÓN (POST)
# 2. PROCESAR ACTUALIZACIÓN (POST)
    if request.method == 'POST':
        try:
            # Capturamos servicios dinámicos
            nombres = request.form.getlist('srv_nombre[]')
            duraciones = request.form.getlist('srv_duracion[]')
            
            nuevos_servicios = {}
            for n, d in zip(nombres, duraciones):
                if n.strip():
                    nuevos_servicios[n.strip()] = int(d) if d else 60

            # CONSTRUCCIÓN CORRECTA DE LA ESTRUCTURA
            nueva_config = {
                "admin_password": request.form.get('admin_password') or config.get('admin_password'),
                "empresa": request.form.get('empresa'),
                "email_admin": request.form.get('email_admin'),
                "whatsapp": request.form.get('whatsapp'),
                "hora_cierre": request.form.get('hora_cierre', '17:00'), # Va afuera del almuerzo
                "almuerzo": {
                    "inicio": request.form.get('almuerzo_inicio', '12:00'),
                    "fin": request.form.get('almuerzo_fin', '13:00')
                },
                "smtp": {
                    "server": request.form.get('smtp_server'),
                    "port": int(request.form.get('smtp_port', 587)),
                    "email": request.form.get('smtp_email'),
                    "password": request.form.get('smtp_password')
                },
                "horarios_base": [h.strip() for h in request.form.get('horarios', '').split(',') if h.strip()],
                "servicios": nuevos_servicios
            }
            
            # Guardado Seguro
            contenido_json = json.dumps(nueva_config, indent=4, ensure_ascii=False)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(contenido_json)
            
            flash("¡Configuración actualizada con éxito!", "success")
            return redirect(url_for('admin.edit_config'))
            
        except Exception as e:
            flash(f"Error al guardar: {str(e)}", "danger")
            return redirect(url_for('admin.edit_config'))

    # 3. MOSTRAR PANEL (GET)
    return render_template('admin_config.html', config=config)


@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    flash("Has cerrado sesión", "info")
    return redirect(url_for('admin.edit_config'))