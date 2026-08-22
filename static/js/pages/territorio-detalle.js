/**
 * static/js/pages/territorio-detalle.js
 * --------------------------------------
 * Lógica de interacción para la vista de detalle de un territorio
 * (templates/territorio.html):
 *   - Modal "Editar Registro Telefónico"
 *   - Modal "Nuevo Registro Telefónico"
 *   - Modal "Confirmar Eliminación de Territorio"
 *
 * El manejo de abrir/cerrar/click-fuera de cada modal y el atajo 'Esc' se
 * delegan a los módulos reutilizables core/modal.js y core/keyboard.js
 * (deben estar cargados antes que este archivo; ver templates/base.html).
 *
 * El número de territorio se recibe vía data-attribute en el contenedor
 * .header-detalle-territorio (data-territorio-numero) en lugar de quedar
 * embebido como literal de Jinja dentro del JS.
 */

document.addEventListener("DOMContentLoaded", () => {
    // ------------------------------------------------------------------
    // Modal: Editar Registro Telefónico
    // ------------------------------------------------------------------
    const editId = document.getElementById("edit_registro_id");
    const editDir = document.getElementById("edit_direccion");
    const editTel = document.getElementById("edit_telefono");
    const editObs = document.getElementById("edit_observaciones");
    const editNoLlamar = document.getElementById("edit_no_llamar");
    const editFunc = document.getElementById("edit_funcionan");
    const editNotas = document.getElementById("edit_notas_internas");

    const modalEditar = window.AppModal.crear(
        document.getElementById("modal-editar-registro"),
        { focusSelector: "#edit_telefono" }
    );

    document.querySelectorAll(".btn-editar-reg").forEach((btn) => {
        btn.addEventListener("click", () => {
            editId.value = btn.dataset.id;
            editDir.value = btn.dataset.direccion || "";
            editTel.value = btn.dataset.telefono || "";
            editObs.value = btn.dataset.observaciones || "";
            editNoLlamar.checked = btn.dataset.noLlamar === "1";
            editFunc.value = btn.dataset.funcionan;
            editNotas.value = btn.dataset.notasInternas || "";
            modalEditar.open(btn);
        });
    });

    window.AppModal.conectarBotones(modalEditar, {
        cerrar: [
            document.getElementById("btn-cerrar-modal-editar"),
            document.getElementById("btn-cancelar-modal-editar"),
        ],
    });

    // ------------------------------------------------------------------
    // Modal: Nuevo Registro Telefónico
    // ------------------------------------------------------------------
    const modalNuevo = window.AppModal.crear(
        document.getElementById("modal-nuevo-registro"),
        { focusSelector: "#nuevo_telefono" }
    );

    window.AppModal.conectarBotones(modalNuevo, {
        abrir: [
            document.getElementById("btn-abrir-nuevo-reg"),
            document.getElementById("btn-crear-primer-reg"),
        ],
        cerrar: [
            document.getElementById("btn-cerrar-modal-nuevo"),
            document.getElementById("btn-cancelar-modal-nuevo"),
        ],
    });

    // ------------------------------------------------------------------
    // Modal: Confirmar Eliminación de Territorio
    // ------------------------------------------------------------------
    const contenedorTerritorio = document.querySelector("[data-territorio-numero]");
    const numeroTerritorio = contenedorTerritorio
        ? contenedorTerritorio.dataset.territorioNumero
        : "";

    const inputConfirmarNumero = document.getElementById("confirmar-numero-territorio");
    const errorConfirmarEliminar = document.getElementById("error-confirmar-eliminar");
    const btnConfirmarEliminar = document.getElementById("btn-confirmar-eliminar-territorio");

    const modalEliminar = window.AppModal.crear(
        document.getElementById("modal-eliminar-territorio"),
        {
            focusSelector: "#confirmar-numero-territorio",
            onOpen: () => {
                inputConfirmarNumero.value = "";
                errorConfirmarEliminar.classList.add("oculto");
            },
        }
    );

    window.AppModal.conectarBotones(modalEliminar, {
        abrir: [document.getElementById("btn-abrir-eliminar-territorio")],
        cerrar: [
            document.getElementById("btn-cerrar-modal-eliminar"),
            document.getElementById("btn-cancelar-modal-eliminar"),
        ],
    });

    if (inputConfirmarNumero) {
        inputConfirmarNumero.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                btnConfirmarEliminar.click();
            }
        });
    }

    if (btnConfirmarEliminar) {
        btnConfirmarEliminar.addEventListener("click", () => {
            if (inputConfirmarNumero.value.trim() !== numeroTerritorio) {
                errorConfirmarEliminar.classList.remove("oculto");
                inputConfirmarNumero.focus();
                return;
            }
            document.getElementById("form-eliminar-territorio").submit();
        });
    }

    // ------------------------------------------------------------------
    // Esc cierra el modal que esté abierto (editar > nuevo > eliminar)
    // ------------------------------------------------------------------
    window.AppKeyboard.registrarEscapeParaModales([modalEditar, modalNuevo, modalEliminar]);

    // ------------------------------------------------------------------
    // Confirmación antes de finalizar el trabajo del territorio
    // ------------------------------------------------------------------
    window.AppActions.on("submit", "confirmar-finalizar-territorio", () => {
        return confirm("¿Confirmás que deseás finalizar el trabajo de este territorio?");
    });

    const fechaFinalizacion = document.getElementById("fecha_finalizacion");
    if (fechaFinalizacion && !fechaFinalizacion.value) {
        const hoy = new Date();
        const anio = hoy.getFullYear();
        const mes = String(hoy.getMonth() + 1).padStart(2, "0");
        const dia = String(hoy.getDate()).padStart(2, "0");
        fechaFinalizacion.value = `${anio}-${mes}-${dia}`;
    }
});
