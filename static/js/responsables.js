/**
 * static/js/responsables.js
 * -------------------------
 * Interactividad en tiempo real para el módulo de Responsables:
 * - Filtrado y búsqueda instantánea en vivo (por nombre, teléfono, email)
 * - Filtro reactivo por estado (Todos, Activos, Inactivos)
 * - Ordenamiento dinámico en el cliente
 * - Paginación 100% en cliente, sobre el total ya filtrado y ordenado
 * - Contador dinámico de resultados visibles
 * - Acciones en lote con selección masiva y contador reactivo
 * - Modal fluido para edición de responsable con atajo 'Escape'
 * - Atajos de teclado ('/' para buscar)
 *
 * PAGINACIÓN: hasta la sección 1.4 del plan de refactorización, la
 * paginación era server-side (el backend devolvía una sola página de
 * filas), pero el filtro/orden del cliente solo operaba sobre esas filas
 * ya recortadas — cambiar el filtro de Estado, por ejemplo, no consideraba
 * responsables de otras páginas. Con el volumen real de datos (< 100
 * responsables) no hace falta paginar en el servidor: ahora el backend
 * entrega la lista completa una sola vez y esta página resuelve filtro,
 * orden y paginación en conjunto, siempre sobre el total real.
 *
 * Todas las acciones que antes se invocaban desde atributos inline
 * (onclick/onchange/onsubmit) en responsables.html se registran acá
 * mediante `AppActions.on(...)` y se disparan por delegación de eventos
 * (ver core/actions.js). No hay funciones expuestas en `window` para uso
 * exclusivo del HTML.
 */

document.addEventListener("DOMContentLoaded", () => {
    // Elementos del DOM
    const inputBuscador = document.getElementById("input-buscador-responsables");
    const selectEstado = document.getElementById("filtro-resp-estado");
    const selectOrden = document.getElementById("filtro-resp-orden");
    const selectPorPagina = document.getElementById("filtro-resp-per-page");
    const btnLimpiar = document.getElementById("btn-limpiar-filtros-resp");
    const tabla = document.querySelector(".tabla-responsables");
    const tbody = tabla ? tabla.querySelector("tbody") : null;
    const sinResultadosEl = document.getElementById("sin-resultados-js");
    const paginacionContainer = document.getElementById("paginacion-container");
    const paginacionInfo = document.getElementById("paginacion-info");
    const paginacionControles = document.getElementById("paginacion-controles");
    const headerTabla = document.querySelector(".header-tabla-responsables");
    const contadorTotalHeader = headerTabla ? headerTabla.querySelector("small") : null;

    // Modal de edición (controlador reutilizable, ver core/modal.js).
    // Se conserva el toggle manual de style.display porque el CSS de este
    // modal lo usaba además de la clase "oculto" (quirk existente).
    const modalEditarEl = document.getElementById("modal-editar");
    const formEditar = document.getElementById("form-editar-responsable");
    const editNombre = document.getElementById("edit-nombre");
    const editTelefono = document.getElementById("edit-telefono");
    const editEmail = document.getElementById("edit-email");

    // Acciones en lote
    const checkTodos = document.getElementById("check-todos");
    const barraLote = document.getElementById("barra-lote");
    const contadorSeleccionados = document.getElementById("contador-seleccionados");
    const formLote = document.getElementById("form-lote");
    const loteAccionInput = document.getElementById("lote-accion");
    const loteInputsContainer = document.getElementById("lote-inputs-container");

    const filas = Array.from(document.querySelectorAll(".fila-responsable"));

    // Página inicial: la que venía en la URL (?page=N), para que un link
    // compartido siga apuntando más o menos al mismo lugar. Ver el bloqueo
    // de rango dentro de aplicarPaginacion() si esa página ya no existe.
    let paginaActual = headerTabla
        ? parseInt(headerTabla.dataset.paginaInicial, 10) || 1
        : 1;

    function obtenerPorPagina() {
        const val = selectPorPagina?.value || "10";
        return val === "todos" ? Infinity : parseInt(val, 10) || 10;
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

    // --- FILTRADO EN TIEMPO REAL (sobre el total, no sobre una página) ---
    function aplicarFiltrosEnVivo(opciones) {
        opciones = opciones || {};
        if (!tbody || filas.length === 0) return;

        const q = (inputBuscador?.value || "").trim().toLowerCase();
        const estadoFiltro = selectEstado?.value || "";

        const coincidentes = [];

        filas.forEach((fila) => {
            const searchText = fila.dataset.search || "";
            const activo = fila.dataset.activo || "1";

            const coincideTexto = !q || searchText.includes(q);
            const coincideEstado = !estadoFiltro || activo === estadoFiltro;

            if (coincideTexto && coincideEstado) {
                coincidentes.push(fila);
            } else {
                fila.style.display = "none";
                // Desmarcar checkbox si queda oculta por el filtro
                const cb = fila.querySelector(".check-responsable");
                if (cb && cb.checked) {
                    cb.checked = false;
                }
            }
        });

        if (opciones.resetearPagina) {
            paginaActual = 1;
        }

        aplicarPaginacion(coincidentes);
    }

    // --- PAGINACIÓN EN EL CLIENTE (sobre las filas ya filtradas) ---
    function aplicarPaginacion(coincidentes) {
        const porPagina = obtenerPorPagina();
        const total = coincidentes.length;
        const totalPaginas = porPagina === Infinity ? 1 : Math.max(1, Math.ceil(total / porPagina));

        if (paginaActual > totalPaginas) paginaActual = totalPaginas;
        if (paginaActual < 1) paginaActual = 1;

        const inicio = porPagina === Infinity ? 0 : (paginaActual - 1) * porPagina;
        const fin = porPagina === Infinity ? total : inicio + porPagina;

        coincidentes.forEach((fila, idx) => {
            fila.style.display = idx >= inicio && idx < fin ? "" : "none";
        });

        if (contadorTotalHeader) {
            contadorTotalHeader.textContent = `(${total} en total)`;
        }

        if (sinResultadosEl) {
            if (total === 0) {
                sinResultadosEl.classList.remove("oculto");
                if (tabla) tabla.classList.add("oculto");
            } else {
                sinResultadosEl.classList.add("oculto");
                if (tabla) tabla.classList.remove("oculto");
            }
        }

        if (paginacionContainer) {
            paginacionContainer.classList.toggle("oculto", total === 0);
        }

        renderizarPaginacion(total, totalPaginas, inicio, Math.min(fin, total));
        actualizarSeleccion();
    }

    function renderizarPaginacion(total, totalPaginas, inicio, fin) {
        if (paginacionInfo) {
            paginacionInfo.innerHTML =
                total === 0
                    ? ""
                    : `Mostrando <strong>${inicio + 1}</strong> a <strong>${fin}</strong> de <strong>${total}</strong> responsables`;
        }

        if (!paginacionControles) return;

        if (totalPaginas <= 1) {
            paginacionControles.innerHTML = "";
            return;
        }

        let html = "";

        html +=
            paginaActual > 1
                ? `<button type="button" class="btn-pag" data-action="cambiar-pagina" data-pagina="${paginaActual - 1}">« Anterior</button>`
                : `<span class="btn-pag disabled">« Anterior</span>`;

        for (let p = 1; p <= totalPaginas; p++) {
            if (p === paginaActual) {
                html += `<span class="btn-pag active">${p}</span>`;
            } else if (p <= 3 || p >= totalPaginas - 2 || (p >= paginaActual - 1 && p <= paginaActual + 1)) {
                html += `<button type="button" class="btn-pag" data-action="cambiar-pagina" data-pagina="${p}">${p}</button>`;
            } else if (p === 4 || p === totalPaginas - 3) {
                html += `<span class="btn-pag-ellipsis">...</span>`;
            }
        }

        html +=
            paginaActual < totalPaginas
                ? `<button type="button" class="btn-pag" data-action="cambiar-pagina" data-pagina="${paginaActual + 1}">Siguiente »</button>`
                : `<span class="btn-pag disabled">Siguiente »</span>`;

        paginacionControles.innerHTML = html;
    }

    window.AppActions.on("click", "cambiar-pagina", (btn) => {
        const nuevaPagina = parseInt(btn.dataset.pagina, 10);
        if (!nuevaPagina || nuevaPagina === paginaActual) return;
        paginaActual = nuevaPagina;
        aplicarFiltrosEnVivo();
    });

    // Eventos de filtros reactivos. Cambiar el texto de búsqueda, el estado
    // o cuántos responsables mostrar por página vuelve a la página 1;
    // reordenar mantiene la página actual.
    if (inputBuscador) {
        inputBuscador.addEventListener("input", () => aplicarFiltrosEnVivo({ resetearPagina: true }));
    }

    if (selectEstado) {
        selectEstado.addEventListener("change", () => aplicarFiltrosEnVivo({ resetearPagina: true }));
    }

    if (selectOrden) {
        selectOrden.addEventListener("change", () => {
            ordenarFilasEnVivo();
            aplicarFiltrosEnVivo();
        });
    }

    window.AppActions.on("change", "cambiar-por-pagina", () => {
        aplicarFiltrosEnVivo({ resetearPagina: true });
    });

    if (btnLimpiar) {
        btnLimpiar.addEventListener("click", () => {
            if (inputBuscador) inputBuscador.value = "";
            if (selectEstado) selectEstado.value = "";
            if (selectOrden) selectOrden.value = "nombre_asc";
            ordenarFilasEnVivo();
            aplicarFiltrosEnVivo({ resetearPagina: true });
        });
    }

    // El formulario de filtros no debe recargar la página: cada control
    // reacciona en vivo por su cuenta (input/change de arriba).
    window.AppActions.on("submit", "prevenir-envio-filtros", () => false);

    // --- SELECCIÓN Y ACCIONES EN LOTE ---
    // Operan sobre ".check-responsable" no ocultos: como el filtro y la
    // paginación ocultan filas con el mismo mecanismo (style.display),
    // esto ya representa "visible en esta página y coincide con el
    // filtro" sin ningún cambio adicional.
    function toggleSelectTodos(master) {
        const checkboxesVisibles = document.querySelectorAll(
            '.fila-responsable:not([style*="display: none"]) .check-responsable'
        );
        checkboxesVisibles.forEach((cb) => (cb.checked = master.checked));
        actualizarSeleccion();
    }

    function actualizarSeleccion() {
        const seleccionados = document.querySelectorAll(".check-responsable:checked");
        const count = seleccionados.length;

        if (barraLote && contadorSeleccionados) {
            if (count > 0) {
                barraLote.classList.remove("oculto");
                contadorSeleccionados.textContent = `${count} seleccionado${count > 1 ? "s" : ""}`;
            } else {
                barraLote.classList.add("oculto");
            }
        }

        if (checkTodos) {
            const checkboxesVisibles = document.querySelectorAll(
                '.fila-responsable:not([style*="display: none"]) .check-responsable'
            );
            if (checkboxesVisibles.length > 0) {
                checkTodos.checked = count === checkboxesVisibles.length && count > 0;
            } else {
                checkTodos.checked = false;
            }
        }
    }

    function ejecutarAccionLote(accion) {
        const seleccionados = document.querySelectorAll(".check-responsable:checked");
        if (seleccionados.length === 0 || !formLote || !loteAccionInput || !loteInputsContainer) return;

        const accionTexto = accion === "desactivar" ? "desactivar" : "reactivar";
        if (!confirm(`¿Estás seguro de que deseas ${accionTexto} a los ${seleccionados.length} responsables seleccionados?`)) {
            return;
        }

        loteAccionInput.value = accion;
        loteInputsContainer.innerHTML = "";

        seleccionados.forEach((cb) => {
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = "responsables_ids";
            input.value = cb.value;
            loteInputsContainer.appendChild(input);
        });

        formLote.submit();
    }

    window.AppActions.on("change", "seleccionar-todos", toggleSelectTodos);
    window.AppActions.on("change", "actualizar-seleccion-lote", actualizarSeleccion);
    window.AppActions.on("click", "lote-desactivar", () => ejecutarAccionLote("desactivar"));
    window.AppActions.on("click", "lote-activar", () => ejecutarAccionLote("activar"));

    // --- MODAL DE EDICIÓN ---
    const modalEditar = window.AppModal.crear(modalEditarEl, {
        onOpen: () => {
            if (modalEditarEl) modalEditarEl.style.display = "flex";
            setTimeout(() => {
                if (editNombre) editNombre.focus();
            }, 80);
        },
        onClose: () => {
            if (modalEditarEl) modalEditarEl.style.display = "";
        },
    });

    window.AppActions.on("click", "abrir-editar-responsable", (btn) => {
        if (!modalEditarEl || !formEditar) return;
        const id = btn.dataset.id;
        const nombre = btn.dataset.nombre || "";
        const telefono = btn.dataset.telefono || "";
        const email = btn.dataset.email || "";

        formEditar.action = `/responsables/${id}/editar`;
        if (editNombre) editNombre.value = nombre;
        if (editTelefono) editTelefono.value = telefono;
        if (editEmail) editEmail.value = email;

        modalEditar.open(btn);
    });

    window.AppActions.on("click", "cerrar-modal-editar", () => {
        modalEditar.close();
    });

    // --- CONFIRMACIÓN AL DESACTIVAR ---
    window.AppActions.on("submit", "confirmar-desactivacion", (form) => {
        const nombre = form.dataset.nombre || "este responsable";
        return confirm(`¿Estás seguro de que deseas desactivar a ${nombre}?`);
    });

    // --- ATAJOS DE TECLADO ---
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            if (modalEditar.isOpen()) {
                modalEditar.close();
            } else if (inputBuscador && document.activeElement === inputBuscador && inputBuscador.value) {
                inputBuscador.value = "";
                aplicarFiltrosEnVivo({ resetearPagina: true });
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

    // Inicialización: el orden ya viene correcto desde el servidor (misma
    // lógica de ORDER BY que el <select> de orden refleja), así que solo
    // hace falta aplicar filtro + paginación para pintar los contadores y
    // los controles de paginación al cargar la página.
    aplicarFiltrosEnVivo();
});
