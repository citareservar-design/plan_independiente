from datetime import datetime, timedelta
from utils.reservations import (
    cargar_reservas, 
    guardar_reservas, 
    DURACION_SERVICIOS, 
    format_google_calendar_datetime, 
    enviar_correo_confirmacion,
    enviar_correo_reagendacion,
    enviar_correo_cancelacion, # Nueva importación
    HORAS_DISPONIBLES,
    formatear_hora_12h,
    cargar_config, get_horas_ocupadas_por_superposicion
)


from datetime import datetime, timedelta
import pytz


def obtener_horas_disponibles(reservas, fecha_a_mostrar, duracion_servicio=30):
    from utils.reservations import get_horas_ocupadas_por_superposicion, cargar_config
    
    # 1. Cargar configuración y definir variables
    config = cargar_config()
    horarios_base = config.get("horarios_base", []) # AQUÍ SE DEFINE
    almuerzo = config.get('almuerzo', {"inicio": "12:00", "fin": "13:00"})
    hora_cierre_str = config.get('hora_cierre', '18:00')
    
    # 2. HORA ACTUAL COLOMBIA
    tz = pytz.timezone('America/Bogota')
    ahora_local = datetime.now(tz)
    fecha_hoy = ahora_local.strftime("%Y-%m-%d")
    hora_actual_obj = ahora_local.time()

    # 3. RESERVAS EXISTENTES
    horas_ocupadas = get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar)
    
    horas_libres = []
    formato = "%H:%M"
    
    try:
        hora_cierre_dt = datetime.strptime(hora_cierre_str, formato)
    except:
        hora_cierre_dt = datetime.strptime("18:00", formato)

    # --- EL BUCLE DEBE ESTAR AQUÍ ADENTRO (INDENTADO) ---
    for h in horarios_base:
        try:
            h = h.strip()
            inicio_dt = datetime.strptime(h, formato)
            fin_dt = inicio_dt + timedelta(minutes=int(duracion_servicio))
            
            es_posible = True

            # Filtro A: Pasó la hora
            if str(fecha_a_mostrar) == str(fecha_hoy):
                if inicio_dt.time() < hora_actual_obj:
                    es_posible = False

            # Filtro B: Cierre
            if es_posible and fin_dt > hora_cierre_dt:
                es_posible = False

            # Filtro C: Citas y Almuerzo
            if es_posible:
                pasos = (int(duracion_servicio) + 29) // 30
                for i in range(pasos):
                    bloque_chk = (inicio_dt + timedelta(minutes=i*30)).strftime(formato)
                    if bloque_chk in horas_ocupadas:
                        es_posible = False
                        break
                    if almuerzo['inicio'] <= bloque_chk < almuerzo['fin']:
                        es_posible = False
                        break

            if es_posible:
                horas_libres.append({
                    'valor': h, 
                    'texto': inicio_dt.strftime("%I:%M %p")
                })
        except:
            continue
            
    return horas_libres



def obtener_horas_libres_reagendar(fecha):
    return obtener_horas_disponibles(cargar_reservas(), fecha)

def crear_cita(data, host_url):
    # 1. Cargamos las reservas y la configuración actual
    from utils.reservations import cargar_reservas, guardar_reservas, cargar_config
    
    reservas = cargar_reservas()
    config = cargar_config()
    
    # 2. Obtenemos el diccionario de servicios del JSON
    # Si no existe en el JSON, usamos un diccionario vacío {}
    servicios_config = config.get('servicios', {})
    
    # Extraer variables necesarias del diccionario 'data'
    fecha = data.get('date')
    hora = data.get('hora')
    servicio = data.get('tipo_una')
    
    # 3. CAMBIO CLAVE: Buscamos la duración en el JSON. 
    # Si el servicio no existe allí, le damos 60 minutos por defecto.
    duracion = servicios_config.get(servicio, 60)
    
    timestamp = str(datetime.now().timestamp()).replace('.', '')

    nueva_cita = {
        'nombre': data.get('nombre'), 
        'email': data.get('email'), 
        'telefono': data.get('telefono'),
        'date': fecha, 
        'hora': hora, 
        'tipo_una': servicio, 
        'duracion': duracion, # Ahora esta duración es la del JSON
        'notes': data.get('notes', ''), 
        'timestamp': timestamp
    }
    
    reservas.append(nueva_cita)
    guardar_reservas(reservas)
    
    # Generar links
    start, end = format_google_calendar_datetime(fecha, hora, duracion)
    cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Nails&dates={start}/{end}"
    citas_link = f"{host_url}citas?email_cliente={nueva_cita['email']}"
    
    # Enviar correo
    enviar_correo_confirmacion(nueva_cita, cal_link, citas_link)
    
    return {"status": "success"}

def cancelar_cita_por_id(id_cita):
    """Busca la cita, envía correo de cancelación y luego la elimina."""
    reservas = cargar_reservas()
    cita_a_cancelar = next((r for r in reservas if r.get('timestamp') == id_cita), None)
    
    if cita_a_cancelar:
        # 1. Enviar correo antes de borrarla de la list
        enviar_correo_cancelacion(cita_a_cancelar)
        
        # 2. Filtrar la lista para eliminarla
        nuevas_reservas = [r for r in reservas if r.get('timestamp') != id_cita]
        guardar_reservas(nuevas_reservas)
        return {"status": "success", "message": "Cita cancelada y notificada"}
    
    return {"status": "error", "message": "No se encontró la cita"}

def reagendar_cita_por_id(id_cita, nueva_fecha, nueva_hora):
    reservas = cargar_reservas()
    cita_modificada = None
    for cita in reservas:
        if cita.get('timestamp') == id_cita:
            cita['date'], cita['hora'] = nueva_fecha, nueva_hora
            cita_modificada = cita
            break

    if cita_modificada:
        guardar_reservas(reservas)
        start, end = format_google_calendar_datetime(nueva_fecha, nueva_hora, cita_modificada.get('duracion', 60))
        nuevo_cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Reagendada&dates={start}/{end}"
        
        # LLAMADA REVERTIDA: Solo pasamos reserva y el link de calendario
        enviar_correo_reagendacion(cita_modificada, nuevo_cal_link) 
        
        return {"status": "success", "message": "Cita reagendada"}