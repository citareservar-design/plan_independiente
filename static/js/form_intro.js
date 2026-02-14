
console.log("form_intro.js cargadooooooo correctamente");

    // --- 1. ELEMENTOS DE LA INTRO ---
    const progressBar = document.getElementById('progress-bar');
    const counter = document.getElementById('counter');
    const intro = document.getElementById('intro-screen');
    const main = document.getElementById('main-content');

    // --- 2. ELEMENTOS DEL FORMULARIO ---
    // Usamos el selector por nombre para coincidir con tu HTML dinámico
    const selectServicio = document.querySelector('select[name="tipo_una"]'); 
    const inputFecha = document.getElementById('fecha');
    const selectHoras = document.querySelector('select[name="hora"]');

    // --- 3. LÓGICA DE LA INTRO (ORIGINAL) ---
    function marcarCambiandoFecha() {
        sessionStorage.setItem('saltarIntro', 'true');
    }

    window.onload = function() {
        if (sessionStorage.getItem('saltarIntro') === 'true') {
            if(intro) intro.style.display = 'none';
            if(main) main.classList.add('show-content');
            sessionStorage.removeItem('saltarIntro');
            
            // Si ya hay datos cargados (por ejemplo al volver atrás), actualizar horas
            if(inputFecha && inputFecha.value) {
                validarYEnviar();
            }
        } else {
            ejecutarIntro();
        }
    };

    function ejecutarIntro() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 15) + 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                setTimeout(() => {
                    if(intro) intro.classList.add('fade-out');
                    setTimeout(() => {
                        if(intro) intro.style.display = 'none';
                        if(main) main.classList.add('show-content');
                    }, 800);
                }, 400);
            }
            if(progressBar) progressBar.style.width = progress + '%';
            if(counter) counter.innerText = progress + '%';
        }, 150);
    }

    // --- 4. LÓGICA DE VALIDACIÓN Y HORAS INTELIGENTES ---
async function validarYEnviar() {
    const inputFecha = document.getElementById('date'); 
    const selectServicio = document.getElementById('servicio');
    // IMPORTANTE: Ahora apuntamos al contenedor de los botones y al input oculto
    const contenedorHoras = document.getElementById('contenedor-horas');
    const inputHoraOculto = document.getElementById('hora-seleccionada');

    if (!inputFecha || !selectServicio || !contenedorHoras) return;

    const fechaVal = inputFecha.value;
    const servicioVal = selectServicio.value;

    // --- BLOQUEO DE DOMINGOS ---
    if (fechaVal) {
        const fechaObj = new Date(fechaVal + 'T00:00:00');
        if (fechaObj.getDay() === 0) { 
            Swal.fire({
                title: '<span style="color: #0f172a; font-weight: 900;">DÍA NO LABORAL</span>',
                text: 'Lo sentimos, los domingos no estamos disponibles.',
                icon: 'warning',
                confirmButtonColor: '#0ea5e9',
                customClass: { popup: 'rounded-3xl' }
            });
            inputFecha.value = ""; 
            contenedorHoras.innerHTML = '<p class="col-span-2 text-center text-slate-400 text-xs py-4">Selecciona una fecha válida...</p>';
            return; 
        }
    }

    // Limpieza previa (Estado de carga)
    contenedorHoras.innerHTML = '<p class="col-span-2 text-center text-sky-500 animate-pulse font-bold py-4">Buscando turnos...</p>';
    inputHoraOculto.value = ""; // Resetear hora seleccionada

    if (!fechaVal || !servicioVal) {
        contenedorHoras.innerHTML = '<p class="col-span-2 text-center text-slate-400 text-xs py-4">Selecciona fecha y servicio</p>';
        return;
    }

    try {
        const url = `/api/horas-disponibles/${fechaVal}?servicio=${encodeURIComponent(servicioVal.toLowerCase())}`;
        const response = await fetch(url);
        const horas = await response.json();

        contenedorHoras.innerHTML = ''; 

        if (horas.length === 0) {
            contenedorHoras.innerHTML = '<p class="col-span-2 text-center text-red-400 font-bold py-4">Sin turnos disponibles</p>';
            Swal.fire({
                title: '<span style="color: #0f172a; font-weight: 900;">¡SIN TURNOS!</span>',
                text: 'No hay horarios disponibles para esta combinación.',
                icon: 'info',
                confirmButtonColor: '#0ea5e9',
                customClass: { popup: 'rounded-3xl' }
            });
        } else {
            // --- INSERTAMOS LOS BOTONES EN 2 COLUMNAS ---
            horas.forEach(h => {
                const btn = document.createElement('button');
                btn.type = 'button'; // Evita que el botón envíe el form
                // Estilo Mobile-First: 2 columnas, texto legible, bordes redondeados
                btn.className = "py-3 px-2 bg-white border-2 border-slate-100 rounded-xl text-slate-900 font-bold hover:border-sky-500 transition-all text-sm shadow-sm flex items-center justify-center";
                btn.innerText = h.texto; // Ejemplo: "08:30 AM"

                btn.onclick = () => {
                    // 1. Quitar estilos a los demás botones
                    document.querySelectorAll('#contenedor-horas button').forEach(b => {
                        b.classList.remove('border-sky-500', 'bg-sky-50', 'text-sky-600');
                        b.classList.add('border-slate-100', 'bg-white', 'text-slate-900');
                    });
                    
                    // 2. Aplicar estilo "Activo" al botón seleccionado
                    btn.classList.remove('border-slate-100', 'bg-white', 'text-slate-900');
                    btn.classList.add('border-sky-500', 'bg-sky-50', 'text-sky-600');
                    
                    // 3. Guardar el valor en el input oculto que Flask leerá
                    inputHoraOculto.value = h.valor;
                };

                contenedorHoras.appendChild(btn);
            });
        }
    } catch (error) {
        console.error("Error:", error);
        contenedorHoras.innerHTML = '<p class="col-span-2 text-center text-red-500 py-4">Error de conexión</p>';
    }
}


async function confirmarReservaFinal() {
    const horaSeleccionada = document.getElementById('hora-seleccionada')?.value;


    if (!horaSeleccionada || horaSeleccionada === "") {
        // Usamos SweetAlert para que se vea pro como el resto de tu app
        Swal.fire({
            title: '<span style="color: #0f172a; font-weight: 900;">¿Y LA HORA?</span>',
            text: 'Por favor, selecciona un turno disponible antes de confirmar.',
            icon: 'warning',
            confirmButtonColor: '#0ea5e9',
            customClass: { popup: 'rounded-3xl' }
        });
        
        // Resaltamos el contenedor para llamar la atención
        const contenedor = document.getElementById('contenedor-horas');
        contenedor.classList.add('border-red-400', 'bg-red-50');
        setTimeout(() => {
            contenedor.classList.remove('border-red-400', 'bg-red-50');
        }, 2000);
        
        return; // DETIENE TODO AQUÍ, no sigue con la reserva
    }


    const checkboxDatos = document.getElementById('acepta_datos');
    if (!checkboxDatos.checked) {
        Swal.fire({
            title: '<span style="color: #0f172a; font-weight: 900;">¡ATENCIÓN!</span>',
            text: 'Debes aceptar el tratamiento de datos para poder agendar tu cita.',
            icon: 'info',
            confirmButtonColor: '#0ea5e9',
            customClass: { popup: 'rounded-3xl' }
        });
        
        // Efecto visual para que el usuario vea dónde está el error
        checkboxDatos.parentElement.parentElement.classList.add('border-sky-300', 'bg-sky-50');
        return; // Detiene el envío
    }


    const loader = document.getElementById('loader-agendapp');
    const btn = document.getElementById('btn-confirmar');
    const progressBar = document.getElementById('progress-bar');
    const loaderMsg = document.getElementById('loader-msg');
    
    // 1. Mostrar el loader
    if (loader) loader.style.display = 'flex';

    // 2. Deshabilitar botón para evitar doble reserva
    if (btn) {
        btn.disabled = true;
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
    }

    // 3. Obtener los datos del formulario (IDs validados)
    const datos = {
        nombre: document.getElementById('nombre')?.value,
        email: document.getElementById('email')?.value,
        telefono: document.getElementById('telefono')?.value,
        tipo_una: document.getElementById('servicio')?.value,
        date: document.getElementById('date')?.value,
        hora: document.getElementById('hora-seleccionada')?.value,
        notes: document.getElementById('notas')?.value
    };

    console.log("Datos capturados para enviar:", datos);

    // Animación visual de la barra mientras esperamos al servidor
    if (progressBar && loaderMsg) {
        setTimeout(() => { progressBar.style.width = "40%"; loaderMsg.innerText = "Validando disponibilidad..."; }, 200);
        setTimeout(() => { progressBar.style.width = "70%"; loaderMsg.innerText = "Asegurando tu cupo en AgendApp..."; }, 1000);
    }

    try {
        const response = await fetch('/confirmar-reserva', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });

        const contentType = response.headers.get("content-type");
        
        if (contentType && contentType.includes("application/json")) {
            const resultado = await response.json();
            
            if (response.ok) {
                // Éxito total
                if (progressBar) progressBar.style.width = "100%";
                if (loaderMsg) loaderMsg.innerText = "¡Cita confirmada! Redireccionando...";
                
                setTimeout(() => {
                    window.location.href = "/reserva_exitosa"; 
                }, 800);
            } else {
                throw new Error(resultado.message || "Error en el servidor");
            }
        } else {
            const errorHtml = await response.text();
            console.error("DEBUG DEL ERROR (HTML):", errorHtml);
            throw new Error("El servidor respondió con un error de página. Revisa la consola de Flask.");
        }

    } catch (error) {
        console.error("Error detallado:", error);
        alert("❌ No se pudo confirmar: " + error.message);
        
        // Resetear en caso de fallo
        if (loader) loader.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = "1";
            btn.style.cursor = "pointer";
        }
    }
}


// Ejecutar la carga de horas si ya hay valores al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    const inputFecha = document.getElementById('date');
    const selectServicio = document.getElementById('servicio');
    
    if (inputFecha.value && selectServicio.value) {
        validarYEnviar();
    }
});

