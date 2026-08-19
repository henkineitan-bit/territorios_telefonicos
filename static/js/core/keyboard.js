/**
 * static/js/core/keyboard.js
 * ---------------------------
 * Manejo centralizado del atajo 'Escape' para cerrar el modal que esté
 * abierto en un momento dado. Reemplaza los listeners de 'keydown'
 * casi idénticos que se repetían en cada página con modales.
 *
 * No usa módulos ES (ver core/modal.js). Expone su API en `window.AppKeyboard`.
 * Debe cargarse antes que cualquier script de página que lo use (ver
 * templates/base.html).
 */
(function (window, document) {
    "use strict";

    /**
     * Registra un único listener de 'Escape' que recorre la lista de
     * controladores de modal (creados con AppModal.crear) en orden y
     * cierra el primero que esté abierto. Se corta en el primero para no
     * disparar cierres en cascada si por error hubiera más de un modal
     * abierto a la vez.
     *
     * @param {Array<{isOpen: Function, close: Function}>} modales
     */
    function registrarEscapeParaModales(modales) {
        document.addEventListener("keydown", function (e) {
            if (e.key !== "Escape") return;
            for (var i = 0; i < modales.length; i++) {
                var modal = modales[i];
                if (modal && typeof modal.isOpen === "function" && modal.isOpen()) {
                    modal.close();
                    break;
                }
            }
        });
    }

    window.AppKeyboard = {
        registrarEscapeParaModales: registrarEscapeParaModales
    };
})(window, document);
