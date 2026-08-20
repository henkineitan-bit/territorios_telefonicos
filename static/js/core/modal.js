/**
 * static/js/core/modal.js
 * ------------------------
 * Utilidad reutilizable para modales tipo "backdrop" (fondo oscuro + diálogo).
 * Centraliza el patrón que se repetía por separado en territorios.js,
 * responsables.js y territorio-detalle.js: abrir/cerrar clases CSS,
 * cerrar al hacer click fuera del diálogo, foco automático al abrir, y una
 * forma simple de consultar si el modal está abierto.
 *
 * Accesibilidad (ver docs/Plan_de_Refactorización_y_Arquitectura.pdf,
 * sección 1.5): todo modal creado acá queda automáticamente con
 * role="dialog" y aria-modal="true", con el foco atrapado dentro mientras
 * está abierto (Tab/Shift+Tab no se escapan al resto de la página), y al
 * cerrarse devuelve el foco al elemento que lo abrió. No hace falta hacer
 * nada de esto por página: es responsabilidad de este módulo para
 * cualquier modal que se cree con AppModal.crear().
 *
 * No usa módulos ES (import/export) para mantener compatibilidad con los
 * <script> planos que ya carga la app; expone su API en `window.AppModal`.
 * Debe cargarse antes que cualquier script de página que lo use (ver
 * templates/base.html).
 */
(function (window, document) {
    "use strict";

    // Elementos que cuentan como "enfocables" dentro de un modal, para el
    // atrapado de foco (focus trap) y para el foco inicial por defecto.
    var SELECTOR_ENFOCABLES =
        'a[href], button:not([disabled]), textarea:not([disabled]), ' +
        'input:not([disabled]):not([type="hidden"]), select:not([disabled]), ' +
        '[tabindex]:not([tabindex="-1"])';

    /**
     * Crea un controlador para un modal ya presente en el DOM.
     *
     * @param {HTMLElement|null} modalEl  Elemento raíz del modal (backdrop).
     * @param {Object} [opciones]
     * @param {Function} [opciones.onOpen]   Callback ejecutado al abrir, antes de aplicar el foco.
     * @param {Function} [opciones.onClose]  Callback ejecutado al cerrar.
     * @param {string}  [opciones.focusSelector]  Selector (dentro del modal) del elemento a enfocar al abrir. Si no se indica, se enfoca el primer elemento enfocable del modal.
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

        // Atributos ARIA de diálogo modal. Se aplican una sola vez, acá,
        // en vez de tener que repetirlos a mano en cada template.
        if (!modalEl.hasAttribute("role")) {
            modalEl.setAttribute("role", "dialog");
        }
        modalEl.setAttribute("aria-modal", "true");

        // Elemento que tenía el foco (o que disparó la apertura) antes de
        // abrir el modal, para devolvérselo al cerrar.
        var elementoDisparador = null;

        function obtenerEnfocables() {
            var nodos = modalEl.querySelectorAll(SELECTOR_ENFOCABLES);
            return Array.prototype.filter.call(nodos, function (el) {
                // offsetParent es null en elementos con display:none o en
                // ancestros ocultos; filtra lo que no es realmente visible.
                return el.offsetParent !== null;
            });
        }

        function enfocarAlAbrir() {
            var target = focusSelector ? modalEl.querySelector(focusSelector) : null;
            if (!target) {
                target = obtenerEnfocables()[0];
            }
            if (target) target.focus();
        }

        // Focus trap: Tab en el último elemento enfocable vuelve al
        // primero, y Shift+Tab en el primero va al último. Así el foco
        // nunca se escapa del modal mientras está abierto.
        function manejarTabDentroDelModal(e) {
            if (e.key !== "Tab") return;
            var enfocables = obtenerEnfocables();
            if (enfocables.length === 0) return;

            var primero = enfocables[0];
            var ultimo = enfocables[enfocables.length - 1];

            if (e.shiftKey && document.activeElement === primero) {
                e.preventDefault();
                ultimo.focus();
            } else if (!e.shiftKey && document.activeElement === ultimo) {
                e.preventDefault();
                primero.focus();
            }
        }
        modalEl.addEventListener("keydown", manejarTabDentroDelModal);

        /**
         * Abre el modal.
         * @param {HTMLElement} [trigger]  Elemento que disparó la apertura
         *   (normalmente el botón clickeado). Recibe el foco de vuelta al
         *   cerrar el modal. Si no se pasa, se usa el elemento que tenía
         *   el foco en ese momento.
         */
        function open(trigger) {
            elementoDisparador = trigger || document.activeElement;
            modalEl.classList.remove("oculto");
            document.body.classList.add("modal-abierto");
            if (typeof onOpen === "function") onOpen();
            enfocarAlAbrir();
        }

        function close() {
            modalEl.classList.add("oculto");
            document.body.classList.remove("modal-abierto");
            if (typeof onClose === "function") onClose();
            if (elementoDisparador && typeof elementoDisparador.focus === "function") {
                elementoDisparador.focus();
            }
            elementoDisparador = null;
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
     * crearModal(), evitando repetir addEventListener por cada botón. Los
     * botones "abrir" quedan registrados como disparadores: al cerrar el
     * modal, el foco vuelve automáticamente al botón que lo abrió.
     *
     * @param {{open: Function, close: Function}} modal
     * @param {Object} [botones]
     * @param {Array<HTMLElement|null>} [botones.abrir]
     * @param {Array<HTMLElement|null>} [botones.cerrar]
     */
    function conectarBotones(modal, botones) {
        botones = botones || {};
        (botones.abrir || []).forEach(function (btn) {
            if (btn) btn.addEventListener("click", function () { modal.open(btn); });
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
