/**
 * static/js/territorios.js
 * ------------------------
 * Interactividad y optimizaciones en tiempo real para el panel de territorios:
 * - Búsqueda instantánea en tiempo real sin recargar página
 * - Filtros combinados por estado, responsable y ordenamiento dinámico
 * - Chips de filtros rápidos por estado y responsable
 * - Contador dinámico de resultados visibles
 * - Modal reactivo para creación de nuevos territorios
 * - Accesibilidad por teclado (atajos '/' para buscar, 'Esc' para limpiar/cerrar)
 */

document.addEventListener("DOMContentLoaded", () => {
    // Referencias al DOM
    const inputBuscador = document.getElementById("input-buscador-territorios");
    const btnLimpiarBusqueda = document.getElementById("btn-limpiar-busqueda");
    const selectEstado = document.getElementById("filtro-estado");
    const selectResponsable = document.getElementById("filtro-responsable");
    const selectOrden = document.getElementById("filtro-orden");
    const tbody = document.getElementById("tbody-territorios");
    const noResultados = document.getElementById("no-resultados");
    const btnResetFiltros = document.getElementById("btn-reset-filtros");
    const numMostradosEl = document.getElementById("num-mostrados");
    const chipButtons = document.querySelectorAll(".chip-tag");

    // Modal nuevo territorio
    const modalNuevo = document.getElementById("modal-nuevo-territorio");
    const btnAbrirModal = document.getElementById("btn-nuevo-territorio");
    const btnCerrarModal = document.getElementById("btn-cerrar-modal");
    const btnCancelarModal = document.getElementById("btn-cancelar-modal");
    const inputNuevoNumero = document.getElementById("nuevo_numero");

    const filas = Array.from(document.querySelectorAll(".fila-territorio"));

    // --- FUNCIÓN DE FILTRADO Y BÚSQUEDA REACTIVA ---
    function aplicarFiltros() {
        const query = (inputBuscador?.value || "").trim().toLowerCase();
        const estadoFiltro = selectEstado?.value || "";
        const respFiltro = selectResponsable?.value || "";

        // Mostrar / ocultar botón de limpiar búsqueda
        if (btnLimpiarBusqueda) {
            if (query.length > 0) {
                btnLimpiarBusqueda.classList.remove("oculto");
            } else {
                btnLimpiarBusqueda.classList.add("oculto");
            }
        }

        // Actualizar estado activo en los chips rápidos
        chipButtons.forEach((chip) => {
            const tagVal = (chip.dataset.tag || "").toLowerCase();
            const tagEstado = chip.dataset.tagEstado || "";

            if (tagEstado && estadoFiltro === tagEstado) {
                chip.classList.add("activo");
            } else if (tagVal && query && query.includes(tagVal)) {
                chip.classList.add("activo");
            } else {
                chip.classList.remove("activo");
            }
        });

        let visibles = 0;

        filas.forEach((fila) => {
            const searchText = fila.dataset.search || "";
            const filaEstado = fila.dataset.estado || "";
            const filaRespId = fila.dataset.responsableId || "";

            // Coincidencia de texto (número o responsable)
            const coincideTexto = !query || searchText.includes(query);

            // Coincidencia de estado
            const coincideEstado = !estadoFiltro || filaEstado === estadoFiltro;

            // Coincidencia de responsable
            const coincideResp = !respFiltro || filaRespId === respFiltro;

            if (coincideTexto && coincideEstado && coincideResp) {
                fila.style.display = "";
                visibles++;
            } else {
                fila.style.display = "none";
            }
        });

        // Actualizar contador
        if (numMostradosEl) {
            numMostradosEl.textContent = visibles;
        }

        // Mostrar u ocultar mensaje de "sin resultados"
        if (noResultados) {
            if (visibles === 0) {
                noResultados.classList.remove("oculto");
                if (tbody) tbody.classList.add("oculto");
            } else {
                noResultados.classList.add("oculto");
                if (tbody) tbody.classList.remove("oculto");
            }
        }
    }

    // --- ORDENAMIENTO DINÁMICO EN EL CLIENTE ---
    function ordenarFilas() {
        if (!tbody) return;
        const criterio = selectOrden?.value || "numero";

        const filasOrdenadas = [...filas].sort((a, b) => {
            if (criterio === "numero") {
                const numA = parseFloat(a.dataset.numero) || 0;
                const numB = parseFloat(b.dataset.numero) || 0;
                if (numA !== numB) return numA - numB;
                return a.dataset.numero.localeCompare(b.dataset.numero);
            } else if (criterio === "antiguos") {
                const diasA = parseInt(a.dataset.dias, 10);
                const diasB = parseInt(b.dataset.dias, 10);
                if (diasA === -1 && diasB === -1) return 0;
                if (diasA === -1) return 1;
                if (diasB === -1) return -1;
                return diasB - diasA; // Más días asignado = más antiguo primero
            } else if (criterio === "recientes") {
                const diasA = parseInt(a.dataset.dias, 10);
                const diasB = parseInt(b.dataset.dias, 10);
                if (diasA === -1 && diasB === -1) return 0;
                if (diasA === -1) return 1;
                if (diasB === -1) return -1;
                return diasA - diasB; // Menos días asignado = más reciente primero
            } else if (criterio === "lineas") {
                const linA = parseInt(a.dataset.lineas, 10) || 0;
                const linB = parseInt(b.dataset.lineas, 10) || 0;
                return linB - linA;
            }
            return 0;
        });

        // Reinsertar en el DOM en el nuevo orden
        filasOrdenadas.forEach((f) => tbody.appendChild(f));
    }

    // --- EVENT LISTENERS ---
    if (inputBuscador) {
        inputBuscador.addEventListener("input", aplicarFiltros);
    }

    if (btnLimpiarBusqueda) {
        btnLimpiarBusqueda.addEventListener("click", () => {
            if (inputBuscador) {
                inputBuscador.value = "";
                inputBuscador.focus();
            }
            aplicarFiltros();
        });
    }

    if (selectEstado) {
        selectEstado.addEventListener("change", aplicarFiltros);
    }

    if (selectResponsable) {
        selectResponsable.addEventListener("change", aplicarFiltros);
    }

    if (selectOrden) {
        selectOrden.addEventListener("change", () => {
            ordenarFilas();
            aplicarFiltros();
        });
    }

    if (btnResetFiltros) {
        btnResetFiltros.addEventListener("click", () => {
            if (inputBuscador) inputBuscador.value = "";
            if (selectEstado) selectEstado.value = "";
            if (selectResponsable) selectResponsable.value = "";
            if (selectOrden) selectOrden.value = "numero";
            ordenarFilas();
            aplicarFiltros();
        });
    }

    // Chips de filtrado rápido
    chipButtons.forEach((chip) => {
        chip.addEventListener("click", () => {
            const tagEstado = chip.dataset.tagEstado;
            const tagNombre = chip.dataset.tag;

            if (tagEstado) {
                if (selectEstado) {
                    if (selectEstado.value === tagEstado) {
                        selectEstado.value = "";
                    } else {
                        selectEstado.value = tagEstado;
                    }
                }
            } else if (tagNombre && inputBuscador) {
                if (inputBuscador.value.trim().toLowerCase() === tagNombre.toLowerCase()) {
                    inputBuscador.value = "";
                } else {
                    inputBuscador.value = tagNombre;
                }
                inputBuscador.focus();
            }

            aplicarFiltros();
        });
    });

    // --- MODAL NUEVO TERRITORIO ---
    function abrirModal() {
        if (!modalNuevo) return;
        modalNuevo.classList.remove("oculto");
        document.body.classList.add("modal-abierto");
        setTimeout(() => {
            if (inputNuevoNumero) inputNuevoNumero.focus();
        }, 100);
    }

    function cerrarModal() {
        if (!modalNuevo) return;
        modalNuevo.classList.add("oculto");
        document.body.classList.remove("modal-abierto");
    }

    if (btnAbrirModal) {
        btnAbrirModal.addEventListener("click", abrirModal);
    }

    if (btnCerrarModal) {
        btnCerrarModal.addEventListener("click", cerrarModal);
    }

    if (btnCancelarModal) {
        btnCancelarModal.addEventListener("click", cerrarModal);
    }

    if (modalNuevo) {
        modalNuevo.addEventListener("click", (e) => {
            if (e.target === modalNuevo) {
                cerrarModal();
            }
        });
    }

    // --- ATAJOS DE TECLADO ---
    document.addEventListener("keydown", (e) => {
        // 'Esc' para cerrar modal o limpiar búsqueda
        if (e.key === "Escape") {
            if (modalNuevo && !modalNuevo.classList.contains("oculto")) {
                cerrarModal();
            } else if (inputBuscador && document.activeElement === inputBuscador && inputBuscador.value) {
                inputBuscador.value = "";
                aplicarFiltros();
            }
        }

        // '/' para enfocar el buscador principal si no se está escribiendo en un input
        if (e.key === "/" && !["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName)) {
            e.preventDefault();
            if (inputBuscador) {
                inputBuscador.focus();
                inputBuscador.select();
            }
        }
    });

    // Inicialización al cargar la página
    aplicarFiltros();
});
