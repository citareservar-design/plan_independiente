console.log("Citas.js cargado");

// --- 1. CANCELAR CITA ---
const confirmarCancelacion = (timestamp) => {
    Swal.fire({
        title: '¿Eliminar cita?',
        text: "Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Sí, cancelar',
        cancelButtonText: 'No, volver'
    }).then((result) => {
        if (result.isConfirmed) {
            const loader = document.getElementById('loader-agendapp');
            const progressBar = document.getElementById('progress-bar');
            const loaderMsg = document.getElementById('loader-msg');

            if (loader) loader.style.display = 'flex';
            if (progressBar) progressBar.style.width = "50%";
            if (loaderMsg) loaderMsg.innerText = "Cancelando tu cupo...";

            fetch(`/api/cancelar/${timestamp}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' || data.message.includes("éxito")) {
                        if (progressBar) progressBar.style.width = "100%";
                        if (loaderMsg) loaderMsg.innerText = "Cita eliminada correctamente.";
                        setTimeout(() => { location.reload(); }, 1000);
                    } else {
                        if (loader) loader.style.display = 'none';
                        Swal.fire('Error', data.message || 'No se pudo cancelar', 'error');
                    }
                })
                .catch(err => {
                    if (loader) loader.style.display = 'none';
                    Swal.fire('Error', 'Error de conexión', 'error');
                });
        }
    });
};

// --- 2. REAGENDAR CITA ---
function prepararReagendar(timestamp, servicio) {
    let nombreServicio = servicio ? servicio.trim() : "";
    const hoy = new Date().toISOString().split('T')[0];

    // Elementos del Loader (asegúrate de que existan en el HTML)
    const loader = document.getElementById('loader-agendapp');
    const progressBar = document.getElementById('progress-bar');
    const loaderMsg = document.getElementById('loader-msg');

    Swal.fire({
        title: 'Reagendar Cita',
        html: `
            <div style="text-align: left;">
                <p style="font-size: 11px; background: #f1f5f9; padding: 5px; border-radius: 5px; color: #1e293b; font-weight: bold; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                    MODO: ${nombreServicio.toUpperCase()}
                </p>
                <label style="font-size: 10px; font-weight: bold; color: #64748b;">NUEVA FECHA</label>
                <input type="date" id="new_date" min="${hoy}" value="${hoy}" style="width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 10px;">
                
                <label style="font-size: 10px; font-weight: bold; color: #64748b;">HORARIO DISPONIBLE</label>
                <select id="new_hour" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px;">
                    <option value="">Cargando horas...</option>
                </select>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Confirmar Cambio',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#0ea5e9',
        preConfirm: () => {
            const fecha = document.getElementById('new_date').value;
            const hora = document.getElementById('new_hour').value;
            if (!fecha || !hora) {
                Swal.showValidationMessage('Por favor selecciona fecha y hora');
                return false;
            }
            return { timestamp: timestamp, nueva_fecha: fecha, nueva_hora: hora };
        },
        didOpen: () => {
            const dateInput = document.getElementById('new_date');
            const hourSelect = document.getElementById('new_hour');
            const cargar = (fecha) => {
                hourSelect.innerHTML = '<option value="">Buscando bloques...</option>';
                fetch(`/api/horas-disponibles/${fecha}?servicio=${encodeURIComponent(nombreServicio)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.length > 0) {
                            hourSelect.innerHTML = data.map(h => `<option value="${h.valor}">${h.texto}</option>`).join('');
                        } else {
                            hourSelect.innerHTML = `<option value="">No hay espacio suficiente</option>`;
                        }
                    });
            };
            dateInput.addEventListener('change', (e) => cargar(e.target.value));
            cargar(dateInput.value);
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // 1. ACTIVAR TU LOADER PERSONALIZADO
            if (loader) loader.style.display = 'flex';
            if (progressBar) progressBar.style.width = "0%";
            
            // Secuencia de mensajes igual a tu reserva original
            setTimeout(() => { 
                if (progressBar) progressBar.style.width = "40%"; 
                if (loaderMsg) loaderMsg.innerText = "Validando disponibilidad..."; 
            }, 200);

            setTimeout(() => { 
                if (progressBar) progressBar.style.width = "70%"; 
                if (loaderMsg) loaderMsg.innerText = "Asegurando tu cupo en AgendApp..."; 
            }, 1000);

            // 2. EJECUTAR EL FETCH
            fetch(`/api/reagendar/${result.value.timestamp}`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nueva_fecha: result.value.nueva_fecha,
                    nueva_hora: result.value.nueva_hora
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Error en el servidor');
                return response.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    // Éxito: Barra al 100% y recargar
                    if (progressBar) progressBar.style.width = "100%";
                    if (loaderMsg) loaderMsg.innerText = "¡Cita reprogramada! Actualizando...";
                    
                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                } else {
                    throw new Error(data.message || 'Error al reagendar');
                }
            })
            .catch(err => {
                // Ocultar loader si hay error para mostrar el mensaje
                if (loader) loader.style.display = 'none';
                Swal.fire('Error', err.message, 'error');
            });
        }
    });
}