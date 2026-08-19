/**
 * static/js/core/modal.js
 * ------------------------
 * Utilidad reutilizable para modales tipo "backdrop" (fondo oscuro + diálogo).
 * Centraliza el patrón que se repetía por separado en territorios.js,
 * responsables.js y territorio-detalle.js: abrir/cerrar clases CSS,
 * cerrar al hacer click fuera del diálogo, foco automático al abrir, y una
 * forma simple de consultar si el modal está abierto.
 *
 * No usa módulos ES (import/export) para mantener compatibilidad con los
 * <script> planos que ya carga la app; expone su API en `window.AppModal`.
 * Debe cargarse antes que cualquier script de página que lo use (ver
 * templates/base.html).
 */
(function (window, document) {
    "use strict";

    /**
     * Crea un controlador para un modal ya presente en el DOM.
     *
     * @param {HTMLElement|null} modalEl  Elemento raíz del modal (backdrop).
     * @param {Object} [opciones]
     * @param {Function} [opciones.onOpen]   Callback ejecutado al abrir, antes de aplicar el foco.
     * @param {Function} [opciones.onClose]  Callback ejecutado al cerrar.
     * @param {string}  [opciones.focusSelector]  Selector (dentro del modal) del elemento a enfocar al abrir.
     * @param {boolean} [opciones.cerrarAlClickFuera=true]  Si se cierra al hacer click en el backdrop.
     * @returns {{open: Function, close: Function, isOpen: Function, el: (HTMLElement|null)}}
     */
    function crearModal(modalEl, opciones) {
        opciones = opciones || {};
        var onOpen = opciones.onOpen;
        var onClose = opciones.onClose;
        var focusSelector = opciones.focusSelector;
        var cerrarAlClickFuera = opciones.cerrarAlClickFuera !== false;

        if (!modalEl) {
            // Controlador "nulo": permite llamar open()/close()/isOpen() sin
            // tener que chequear existencia en cada página que lo usa.
            return {
                open: function () {},
                close: function () {},
                isOpen: function () { return false; },
                el: null
            };
        }

        function open() {
            modalEl.classList.remove("oculto");
            document.body.classList.add("modal-abierto");
            if (typeof onOpen === "function") onOpen();
            if (focusSelector) {
                var target = modalEl.querySelector(focusSelector);
                if (target) target.focus();
            }
        }

        function close() {
            modalEl.classList.add("oculto");
            document.body.classList.remove("modal-abierto");
            if (typeof onClose === "function") onClose();
        }

        function isOpen() {
            return !modalEl.classList.contains("oculto");
        }

        if (cerrarAlClickFuera) {
            modalEl.addEventListener("click", function (e) {
                if (e.target === modalEl) close();
            });
        }

        return { open: open, close: close, isOpen: isOpen, el: modalEl };
    }

    /**
     * Conecta botones "abrir" y "cerrar" a un controlador ya creado con
     * crearModal(), evitando repetir addEventListener por cada botón.
     *
     * @param {{open: Function, close: Function}} modal
     * @param {Object} [botones]
     * @param {Array<HTMLElement|null>} [botones.abrir]
     * @param {Array<HTMLElement|null>} [botones.cerrar]
     */
    function conectarBotones(modal, botones) {
        botones = botones || {};
        (botones.abrir || []).forEach(function (btn) {
            if (btn) btn.addEventListener("click", function () { modal.open(); });
        });
        (botones.cerrar || []).forEach(function (btn) {
            if (btn) btn.addEventListener("click", function () { modal.close(); });
        });
    }

    window.AppModal = {
        crear: crearModal,
        conectarBotones: conectarBotones
    };
})(window, document);
