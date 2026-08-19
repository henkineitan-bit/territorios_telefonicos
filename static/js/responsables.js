/**
 * static/js/responsables.js
 * -------------------------
 * Interactividad en tiempo real para el módulo de Responsables:
 * - Filtrado y búsqueda instantánea en vivo (por nombre, teléfono, email)
 * - Filtro reactivo por estado (Todos, Activos, Inactivos)
 * - Ordenamiento dinámico en el cliente
 * - Contador dinámico de resultados visibles
 * - Acciones en lote con selección masiva y contador reactivo
 * - Modal fluido para edición de responsable con atajo 'Escape'
 * - Atajos de teclado ('/' para buscar)
 */

document.addEventListener("DOMContentLoaded", () => {
    // Elementos del DOM
    const inputBuscador = document.getElementById("input-buscador-responsables");
    const selectEstado = document.getElementById("filtro-resp-estado");
    const selectOrden = document.getElementById("filtro-resp-orden");
    const btnLimpiar = document.getElementById("btn-limpiar-filtros-resp");
    const tabla = document.querySelector(".tabla-responsables");
    const tbody = tabla ? tabla.querySelector("tbody") : null;
    const sinResultadosEl = document.getElementById("sin-resultados-js");
    const paginacionInfo = document.querySelector(".paginacion-info");
    const contadorTotalHeader = document.querySelector(".header-tabla-responsables small");

    // Modal de edición
    const modalEditar = document.getElementById("modal-editar");
    const formEditar = document.getElementById("form-editar-responsable");
    const editNombre = document.getElementById("edit-nombre");
    const editTelefono = document.getElementById("edit-telefono");
    const editEmail = document.getElementById("edit-email");

    // Acciones en lote
    const checkTodos = document.getElementById("check-todos");
    const barraLote = document.getElementById("barra-lote");
    const contadorSeleccionados = document.getElementById("contador-seleccionados");
    const checkboxesResp = document.querySelectorAll(".check-responsable");

    const filas = Array.from(document.querySelectorAll(".fila-responsable"));
    const totalOriginal = filas.length;

    // --- FILTRADO Y BÚSQUEDA EN TIEMPO REAL ---
    function aplicarFiltrosEnVivo() {
        if (!tbody || filas.length === 0) return;

        const q = (inputBuscador?.value || "").trim().toLowerCase();
        const estadoFiltro = selectEstado?.value || "";

        let visibles = 0;

        filas.forEach((fila) => {
            const searchText = fila.dataset.search || "";
            const activo = fila.dataset.activo || "1";

            const coincideTexto = !q || searchText.includes(q);
            const coincideEstado = !estadoFiltro || activo === estadoFiltro;

            if (coincideTexto && coincideEstado) {
                fila.style.display = "";
                visibles++;
            } else {
                fila.style.display = "none";
                // Desmarcar checkbox si queda oculto
                const cb = fila.querySelector(".check-responsable");
                if (cb && cb.checked) {
                    cb.checked = false;
                }
            }
        });

        // Actualizar contador
        if (paginacionInfo) {
            paginacionInfo.innerHTML = `Mostrando <strong>${visibles}</strong> de <strong>${totalOriginal}</strong> responsables`;
        }
        if (contadorTotalHeader) {
            contadorTotalHeader.textContent = `(${visibles} en total)`;
        }

        // Estado sin resultados
        if (sinResultadosEl) {
            if (visibles === 0) {
                sinResultadosEl.classList.remove("oculto");
                if (tabla) tabla.classList.add("oculto");
            } else {
                sinResultadosEl.classList.add("oculto");
                if (tabla) tabla.classList.remove("oculto");
            }
        }

        actualizarSeleccion();
    }

    // --- ORDENAMIENTO EN EL CLIENTE ---
    function ordenarFilasEnVivo() {
        if (!tbody || filas.length === 0) return;
        const criterio = selectOrden?.value || "nombre_asc";

        const ordenadas = [...filas].sort((a, b) => {
            if (criterio === "nombre_asc") {
                return (a.dataset.nombre || "").localeCompare(b.dataset.nombre || "");
            } else if (criterio === "nombre_desc") {
                return (b.dataset.nombre || "").localeCompare(a.dataset.nombre || "");
            } else if (criterio === "territorios_desc") {
                const tA = parseInt(a.dataset.territorios, 10) || 0;
                const tB = parseInt(b.dataset.territorios, 10) || 0;
                return tB - tA;
            } else if (criterio === "fecha_desc") {
                return (b.dataset.fecha || "").localeCompare(a.dataset.fecha || "");
            } else if (criterio === "fecha_asc") {
                return (a.dataset.fecha || "").localeCompare(b.dataset.fecha || "");
            }
            return 0;
        });

        ordenadas.forEach((f) => tbody.appendChild(f));
    }

    // Eventos de filtros reactivos
    if (inputBuscador) {
        inputBuscador.addEventListener("input", aplicarFiltrosEnVivo);
    }

    if (selectEstado) {
        selectEstado.addEventListener("change", aplicarFiltrosEnVivo);
    }

    if (selectOrden) {
        selectOrden.addEventListener("change", () => {
            ordenarFilasEnVivo();
            aplicarFiltrosEnVivo();
        });
    }

    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", (e) => {
            if (inputBuscador) inputBuscador.value = "";
            if (selectEstado) selectEstado.value = "";
            if (selectOrden) selectOrden.value = "nombre_asc";
            ordenarFilasEnVivo();
            aplicarFiltrosEnVivo();
        });
    }

    // --- SELECCIÓN Y ACCIONES EN LOTE ---
    window.toggleSelectTodos = function(master) {
        const checkboxesVisibles = document.querySelectorAll('.fila-responsable:not([style*="display: none"]) .check-responsable');
        checkboxesVisibles.forEach(cb => cb.checked = master.checked);
        actualizarSeleccion();
    };

    window.actualizarSeleccion = function() {
        const seleccionados = document.querySelectorAll('.check-responsable:checked');
        const count = seleccionados.length;

        if (barraLote && contadorSeleccionados) {
            if (count > 0) {
                barraLote.classList.remove("oculto");
                contadorSeleccionados.textContent = `${count} seleccionado${count > 1 ? 's' : ''}`;
            } else {
                barraLote.classList.add("oculto");
            }
        }

        if (checkTodos) {
            const checkboxesVisibles = document.querySelectorAll('.fila-responsable:not([style*="display: none"]) .check-responsable');
            if (checkboxesVisibles.length > 0) {
                checkTodos.checked = (count === checkboxesVisibles.length && count > 0);
            } else {
                checkTodos.checked = false;
            }
        }
    };

    // --- MODAL DE EDICIÓN ---
    window.abrirModalEditarDesdeBoton = function(btn) {
        if (!modalEditar || !formEditar) return;
        const id = btn.dataset.id;
        const nombre = btn.dataset.nombre || '';
        const telefono = btn.dataset.telefono || '';
        const email = btn.dataset.email || '';

        formEditar.action = `/responsables/${id}/editar`;
        if (editNombre) editNombre.value = nombre;
        if (editTelefono) editTelefono.value = telefono;
        if (editEmail) editEmail.value = email;

        modalEditar.classList.remove('oculto');
        modalEditar.style.display = 'flex';
        document.body.classList.add('modal-abierto');
        setTimeout(() => {
            if (editNombre) editNombre.focus();
        }, 80);
    };

    window.cerrarModalEditar = function() {
        if (!modalEditar) return;
        modalEditar.classList.add('oculto');
        modalEditar.style.display = '';
        document.body.classList.remove('modal-abierto');
    };

    if (modalEditar) {
        modalEditar.addEventListener("click", (e) => {
            if (e.target === modalEditar) {
                cerrarModalEditar();
            }
        });
    }

    // --- ATAJOS DE TECLADO ---
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (modalEditar && !modalEditar.classList.contains("oculto") && modalEditar.style.display !== "none") {
                cerrarModalEditar();
            } else if (inputBuscador && document.activeElement === inputBuscador && inputBuscador.value) {
                inputBuscador.value = "";
                aplicarFiltrosEnVivo();
            }
        }

        if (e.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
            e.preventDefault();
            if (inputBuscador) {
                inputBuscador.focus();
                inputBuscador.select();
            }
        }
    });
});
