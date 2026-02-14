from flask import Flask, render_template
import os

# Importamos los Blueprints (asegúrate que los archivos estén en la carpeta 'routes')
from routes.appointment_routes import appointment_bp
from routes.admin_routes import admin_bp 
from utils.reservations import cargar_config, CONFIG_PATH

app = Flask(__name__)

# LLAVE SECRETA: Necesaria para que el login del admin mantenga la sesión
app.secret_key = 'agendapp_secret_key_2026_nails'

# REGISTRO DE BLUEPRINTS
# He quitado el url_prefix para que las rutas funcionen exactamente como las definiste en los archivos
app.register_blueprint(appointment_bp)
app.register_blueprint(admin_bp)

# Inyector de configuración para que el nombre de la empresa y otros datos
# estén disponibles en todos los HTML automáticamente
@app.context_processor
def inject_config():
    try:
        from utils.reservations import cargar_config
        return dict(config=cargar_config())
    except Exception as e:
        print(f"Error al inyectar config: {e}")
        return dict(config={})
    
    
@app.route('/reserva_exitosa')
def reserva_exitosa():
    # Esta ruta servirá para mostrar que todo salió bien
    return render_template('reserva_exitosa.html')

if __name__ == '__main__':
    # host='0.0.0.0' permite el acceso desde tu móvil a la IP 192.168.1.65
    app.run(host='0.0.0.0', port=5000, debug=True)