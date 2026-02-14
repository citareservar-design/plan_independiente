console.log("admin_config.js cargado correctamente.");

function actualizarReloj(input) {
    const minutos = parseInt(input.value) || 0;
    // Buscamos el visor que está dentro del mismo bloque de servicio
    const contenedorPadre = input.closest('.flex-col');
    const spanTexto = contenedorPadre.querySelector('.texto-horas');
    const visorDiv = contenedorPadre.querySelector('.visor-tiempo');

    if (minutos <= 0) {
        spanTexto.textContent = "0 min";
        visorDiv.classList.replace('bg-sky-500', 'bg-slate-300');
        return;
    } else {
        visorDiv.classList.replace('bg-slate-300', 'bg-sky-500');
    }

    const horas = Math.floor(minutos / 60);
    const minRestantes = minutos % 60;

    let resultado = "";
    if (horas > 0) {
        resultado += `${horas} ${horas === 1 ? 'HORA' : 'HORAS'}`;
    }
    if (minRestantes > 0) {
        resultado += ` ${minRestantes} MIN`;
    }
    if (horas === 0 && minRestantes > 0) {
        resultado = `${minRestantes} MINUTOS`;
    }

    spanTexto.textContent = resultado;
}

// Actualizamos la función para crear nuevos servicios con este mismo diseño
function agregarServicio() {
    const contenedor = document.getElementById('contenedor-servicios');
    const nuevoDiv = document.createElement('div');
    nuevoDiv.className = "flex flex-col p-4 bg-slate-50/50 rounded-2xl border border-slate-100 group";
    nuevoDiv.innerHTML = `
        <div class="flex gap-3 items-center">
            <div class="flex-1">
                <label class="text-[9px] font-black text-slate-400 uppercase ml-2 mb-1 block">Nombre del Servicio</label>
                <input type="text" name="srv_nombre[]" placeholder="Ej: Nuevo Servicio" class="w-full p-3 bg-white border-2 border-slate-100 rounded-xl text-sm font-bold focus:border-sky-400 outline-none transition-all">
            </div>
            <div class="w-24">
                <label class="text-[9px] font-black text-slate-400 uppercase text-center mb-1 block">Minutos</label>
                <input type="number" name="srv_duracion[]" placeholder="0" oninput="actualizarReloj(this)" class="w-full p-3 bg-white border-2 border-sky-200 rounded-xl text-sm font-black text-center text-sky-600 outline-none focus:border-sky-500 transition-all">
            </div>
            <button type="button" onclick="this.closest('.flex-col').remove()" class="mt-5 text-slate-300 hover:text-red-500 p-2 transition-colors">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        </div>
        <div class="mt-3 flex items-center">
            <div class="visor-tiempo bg-slate-300 text-white px-4 py-1.5 rounded-full text-[11px] font-black uppercase tracking-widest shadow-sm">
                <i class="fa-regular fa-clock mr-1"></i>
                <span class="texto-horas">0 min</span>
            </div>
        </div>
    `;
    contenedor.appendChild(nuevoDiv);
}


function rellenarHorarios() {
    const area = document.getElementById('area-horarios');
    
    if (!area) return;

    const sugeridos = [
"08:00", "08:30", 
    "09:00", "09:30", 
    "10:00", "10:30", 
    "11:00", "11:30", 
    "12:00", "12:30", 
    "13:00", "13:30", 
    "14:00", "14:30", 
    "15:00", "15:30", 
    "16:00", "16:30", 
    "17:00", "17:30", 
    "18:00", "18:30", 
    "19:00", "19:30", 
    "20:00"
    ];

    Swal.fire({
        title: '<span style="color: #0f172a; font-weight: 900;">¿RELLENAR HORARIOS?</span>',
        text: "Se pondrán turnos cada hora de 8 AM a 8 PM en formato 24 Hrs.",
        icon: 'question',
        iconColor: '#0ea5e9', // Azul
        showCancelButton: true,
        confirmButtonColor: '#0ea5e9', // Azul
        cancelButtonColor: '#64748b',
        confirmButtonText: 'SÍ, RELLENAR',
        cancelButtonText: 'CANCELAR',
        background: '#ffffff',
        customClass: {
            popup: 'rounded-3xl',
            confirmButton: 'rounded-xl font-bold uppercase text-xs px-6 py-3',
            cancelButton: 'rounded-xl font-bold uppercase text-xs px-6 py-3'
        }
    }).then((result) => {
        if (result.isConfirmed) {
            area.value = sugeridos.join(', ');
            
            // Efecto visual de éxito en azul
            area.style.borderColor = "#0ea5e9";
            area.style.backgroundColor = "#f0f9ff"; 
            
            setTimeout(() => {
                area.style.borderColor = "#f1f5f9"; 
                area.style.backgroundColor = "#f8fafc";
            }, 1500);
        }
    });
}