console.log("Admin Agenda JS cargado");


/**
 * AgendApp - JS Administrativo Separado
 */

// 1. WhatsApp con mensaje personalizado

const empresa = cliente
const cliente = negocio


function enviarWhatsApp(telefono, empresa, cliente, servicio, fecha, hora) {
    const telLimpio = telefono.replace(/\D/g, ''); 
    const fechaMejorada = fecha.split('-').reverse().join('/');

    // Conversión a formato 12 horas (por si acaso)
    let hora12 = hora;
    if (hora.includes(':') && !hora.toUpperCase().includes('AM') && !hora.toUpperCase().includes('PM')) {
        let [hh, mm] = hora.split(':');
        let suffix = hh >= 12 ? "PM" : "AM";
        hh = hh % 12 || 12;
        hora12 = `${hh}:${mm} ${suffix}`;
    }

    // --- MENSAJE ACTUALIZADO ---
    const texto = `Hola *${cliente}*, te saludamos de *${empresa}*. %0A%0A` +
                  `Te recordamos tu cita programada:%0A` +
                  `*Servicio:* ${servicio}%0A` +
                  `*Fecha:* ${fechaMejorada}%0A` +
                  `*Hora:* ${hora12}%0A%0A` +
                  `¿Me podrías confirmar si asistes para ser atendido o si deseas cancelarla? %0A%0A` +
                  `¡Quedamos atentos!`;

    window.open(`https://wa.me/57${telLimpio}?text=${texto}`, '_blank');
}

function confirmarEliminar(timestamp) {
    const loader = document.getElementById('loader-agendapp');
    const progressBar = document.getElementById('progress-bar');
    const loaderMsg = document.getElementById('loader-msg');

    Swal.fire({
        title: '¿ELIMINAR CITA?',
        text: "Esta acción liberará el espacio en la agenda.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#f43f5e',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'SÍ, ELIMINAR',
        cancelButtonText: 'CANCELAR',
        customClass: { popup: 'rounded-[2.5rem]' }
    }).then((result) => {
        if (result.isConfirmed) {
            // 1. ACTIVAR SPINNER
            if (loader) {
                loader.style.display = 'flex';
                if (progressBar) progressBar.style.width = "0%";
                if (loaderMsg) loaderMsg.innerText = "Eliminando de la agenda...";
            }

            // 2. EJECUTAR LLAMADO
            // Agregamos ?from=admin para que tu Python sepa que debe redirigir a /agenda
            fetch(`/cancelar/${timestamp}?from=admin`, { 
                method: 'POST',
                redirect: 'follow' 
            })
            .then(response => {
                if (response.ok || response.redirected) {
                    if (progressBar) progressBar.style.width = "100%";
                    if (loaderMsg) loaderMsg.innerText = "¡Cita borrada!";
                    
                    setTimeout(() => {
                        // FUERZA LA REDIRECCIÓN A TU RUTA DE AGENDA
                        // Esto ignora cualquier error de Flask y te deja donde quieres estar
                        window.location.href = "/agenda"; 
                    }, 1000);
                } else {
                    throw new Error('Error en el servidor');
                }
            })
            .catch(err => {
                if (loader) loader.style.display = 'none';
                console.error("Error:", err);
                Swal.fire('Error', 'No se pudo eliminar la cita.', 'error');
            });
        }
    });
}

// --- Lógica del Buscador en Tiempo Real ---
document.addEventListener('DOMContentLoaded', () => {
    const buscador = document.getElementById('buscador-citas');
    const statusBusqueda = document.getElementById('status-busqueda');

    buscador.addEventListener('input', (e) => {
        const termino = e.target.value.toLowerCase().trim();
        const tarjetas = document.querySelectorAll('.neon-card, .bg-white.p-6.rounded-\\[2\\.5rem\\]'); // Selecciona tus tarjetas
        let encontrados = 0;

        tarjetas.forEach(tarjeta => {
            // Buscamos el nombre dentro del H2 de la tarjeta
            const nombreCliente = tarjeta.querySelector('h2').textContent.toLowerCase();
            
            if (nombreCliente.includes(termino)) {
                tarjeta.style.display = "block";
                tarjeta.style.animation = "fadeIn 0.3s ease";
                encontrados++;
            } else {
                tarjeta.style.display = "none";
            }
        });

        // Mostrar/Ocultar contador de resultados
        if (termino.length > 0) {
            statusBusqueda.classList.remove('hidden');
            statusBusqueda.textContent = `${encontrados} encontrados`;
        } else {
            statusBusqueda.classList.add('hidden');
        }
    });
});

// Pequeña animación para que aparezcan suavemente
const style = document.createElement('style');
style.innerHTML = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);



// --- Función para Copiar Resumen al Portapapeles ---
function copiarResumen(nombre, hora, servicio, fecha) {
    // 1. Texto a copiar
    const texto = `📌 RESUMEN DE CITA\n👤 Cliente: ${nombre}\n⏰ Hora: ${hora}\n📅 Fecha: ${fecha}\n✨ Servicio: ${servicio}`;

    // 2. Crear elemento invisible para copiar
    const el = document.createElement('textarea');
    el.value = texto;
    el.setAttribute('readonly', '');
    el.style.position = 'absolute';
    el.style.left = '-9999px';
    document.body.appendChild(el);
    
    el.select();
    const success = document.execCommand('copy');
    document.body.removeChild(el);

    // 3. ¡EL MENSAJE QUE TE FALTA!
    if (success) {
        Swal.fire({
            icon: 'success',
            title: '¡Copiado al portapapeles!',
            text: 'Ya puedes pegarlo en WhatsApp o notas.',
            timer: 2000,
            showConfirmButton: false,
            background: '#ffffff',
            customClass: {
                popup: 'rounded-[2rem]',
                title: 'text-slate-800 font-black',
                htmlContainer: 'text-slate-500 font-bold'
            }
        });
    } else {
        alert("No se pudo copiar automáticamente.");
    }
}


function reagendarAdmin(timestamp, servicio) {
    let nombreServicio = servicio ? servicio.trim() : "";
    const hoy = new Date().toISOString().split('T')[0];

    // Capturamos los elementos de tu nuevo HTML
    const loader = document.getElementById('loader-agendapp');
    const progressBar = document.getElementById('progress-bar');
    const loaderMsg = document.getElementById('loader-msg');

    Swal.fire({
        title: 'REAGENDAR CITA',
        html: `
            <div style="text-align: left;">
                <p style="font-size: 10px; background: #f0f9ff; padding: 8px; border-radius: 12px; color: #0369a1; font-weight: 800; margin-bottom: 15px; border: 1px solid #e0f2fe; text-transform: uppercase;">
                    <i class="fa-solid fa-tag mr-1"></i> MODO: ${nombreServicio.toUpperCase()}
                </p>
                <label style="font-size: 11px; font-weight: bold; color: #64748b;">NUEVA FECHA</label>
                <input type="date" id="new_date" min="${hoy}" value="${hoy}" style="width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 10px;">
                
                <label style="font-size: 11px; font-weight: bold; color: #64748b;">HORARIO DISPONIBLE</label>
                <select id="new_hour" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px;">
                    <option value="">Cargando horas...</option>
                </select>
            </div>
        `,
        showCancelButton: true,
        confirmButtonText: 'Confirmar Cambio',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: '#0ea5e9',
        customClass: { popup: 'rounded-[2rem]' },
        preConfirm: () => {
            const fecha = document.getElementById('new_date').value;
            const hora = document.getElementById('new_hour').value;
            if (!fecha || !hora) {
                Swal.showValidationMessage('Selecciona fecha y hora');
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
                            hourSelect.innerHTML = `<option value="">No hay disponibilidad</option>`;
                        }
                    });
            };
            dateInput.addEventListener('change', (e) => cargar(e.target.value));
            cargar(dateInput.value);
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // --- 1. MOSTRAR TU SPINNER PERSONALIZADO ---
            if (loader) {
                loader.style.display = 'flex';
                if (progressBar) progressBar.style.width = "0%";
                if (loaderMsg) loaderMsg.innerText = "Conectando con AgendApp...";
            }

            // --- 2. SECUENCIA DE ANIMACIÓN (Simulada para que se vea genial) ---
            setTimeout(() => { 
                if (progressBar) progressBar.style.width = "35%"; 
                if (loaderMsg) loaderMsg.innerText = "Validando nuevo horario..."; 
            }, 300);

            setTimeout(() => { 
                if (progressBar) progressBar.style.width = "70%"; 
                if (loaderMsg) loaderMsg.innerText = "Actualizando tu agenda..."; 
            }, 900);

            // --- 3. EJECUTAR EL CAMBIO REAL ---
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
                if (data && data.status === 'success') {
                    // ÉXITO TOTAL
                    if (progressBar) progressBar.style.width = "100%";
                    if (loaderMsg) loaderMsg.innerText = "¡Cita reprogramada con éxito!";
                    
                    setTimeout(() => {
                        location.reload();
                    }, 1200);
                } else {
                    throw new Error(data.message || 'Error al guardar');
                }
            })
            .catch(err => {
                // SI ALGO FALLA, OCULTAMOS EL SPINNER PARA VER EL ERROR
                if (loader) loader.style.display = 'none';
                Swal.fire('Atención', err.message, 'error');
            });
        }
    });
}