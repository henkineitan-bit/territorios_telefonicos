/**
 * static/js/core/actions.js
 * ---------------------------
 * Delegación de eventos genérica basada en atributos `data-action`,
 * `data-change-action` y `data-submit-action`, en reemplazo de los
 * handlers inline (onclick/onchange/onsubmit) y de las funciones que
 * antes se exponían en `window` solo para poder invocarse desde HTML.
 *
 * Cada página registra sus acciones por nombre con `AppActions.on(...)`.
 * Este módulo instala UN ÚNICO listener por tipo de evento a nivel de
 * `document` (delegación), que resuelve qué handler ejecutar según el
 * atributo data-* del elemento más cercano al que disparó el evento.
 * Como la delegación es a nivel de `document`, funciona también con
 * elementos agregados dinámicamente al DOM (por ejemplo filas de tabla)
 * sin necesidad de volver a "cablear" nada.
 *
 * No usa módulos ES (ver core/modal.js). Expone su API en `window.AppActions`.
 * Debe cargarse antes que cualquier script de página que lo use (ver
 * templates/base.html) — como usa delegación sobre `document`, puede
 * cargarse al principio del <body> sin depender de que el resto del DOM
 * ya esté armado.
 */
(function (window, document) {
    "use strict";

    var ATRIBUTOS = {
        click: "data-action",
        change: "data-change-action",
        submit: "data-submit-action"
    };

    var handlers = { click: {}, change: {}, submit: {} };

    /**
     * Registra un handler para una acción.
     *
     * @param {"click"|"change"|"submit"} tipo
     * @param {string} nombre  Valor del atributo data-action / data-change-action / data-submit-action.
     * @param {Function} handler  Recibe (elemento, evento). Para "submit", si
     *   devuelve `false` se cancela el envío del formulario (equivalente a
     *   `onsubmit="return ...">`).
     */
    function on(tipo, nombre, handler) {
        if (!handlers[tipo]) {
            throw new Error("AppActions: tipo de evento no soportado: " + tipo);
        }
        handlers[tipo][nombre] = handler;
    }

    function despachar(tipo, e) {
        var atributo = ATRIBUTOS[tipo];
        var el = e.target.closest ? e.target.closest("[" + atributo + "]") : null;
        if (!el) return;

        var nombre = el.getAttribute(atributo);
        var handler = handlers[tipo][nombre];
        if (!handler) return;

        var resultado = handler(el, e);
        if (tipo === "submit" && resultado === false) {
            e.preventDefault();
        }
    }

    document.addEventListener("click", function (e) { despachar("click", e); });
    document.addEventListener("change", function (e) { despachar("change", e); });
    document.addEventListener("submit", function (e) { despachar("submit", e); });

    window.AppActions = { on: on };
})(window, document);
