/**
 * termynal.js
 * A lightweight, terminal-like animation library with no dependencies.
 * @author Ines Montani <ines@ines.io>
 * @version 0.0.1
 * @license MIT
 */

(function() {
    'use strict';

    /** Generate a terminal widget. */
    var Termynal = function(container, options) {
        if (!container) throw new Error('A container element is required');
        this.container = container;
        this.pfx = 'data-termynal-';
        this.startDelay = options && options.startDelay
            ? options.startDelay
            : 600;
        this.typeDelay = options && options.typeDelay
            ? options.typeDelay
            : 90;
        this.lineDelay = options && options.lineDelay
            ? options.lineDelay
            : 1500;
        this.progressLength = options && options.progressLength
            ? options.progressLength
            : 40;
        this.progressChar = options && options.progressChar
            ? options.progressChar
            : '█';
        this.progressPercent = options && options.progressPercent
            ? options.progressPercent
            : 100;
        this.cursor = options && options.cursor
            ? options.cursor
            : '▋';
        this.lineData = this.lineDataToElements(container);
        if (!this.lineData.length) return;
        this.init();
    };

    /**
     * Initialise the widget, get lines, clear container and start animation.
     */
    Termynal.prototype.init = function() {
        var self = this;
        var container = this.container;
        self.lines = Array.prototype.slice.call(container.querySelectorAll('[data-ty]'));
        container.setAttribute('data-termynal', '');
        self.container.innerHTML = '';
        self.start();
    };

    /**
     * Start the animation and rener the lines depending on their data attributes.
     */
    Termynal.prototype.start = function() {
        var self = this;
        var start = function() {
            self.lineData.forEach((line, index) => {
                setTimeout(() => {
                    self.container.appendChild(line.element);
                    line.cursor && self.container.appendChild(line.cursor);
                    scrollToBottom();
                    if (index < self.lineData.length - 1) {
                        line.cursor && setTimeout(() => {
                            line.cursor.parentNode.removeChild(line.cursor);
                        }, self.lineDelay);
                    }
                }, index * self.lineDelay);
            });
        };

        const scrollToBottom = () => {
            self.container.scrollTop = self.container.scrollHeight;
        };

        setTimeout(start, self.startDelay);
    };

    /**
     * Format the terminal lines according to their attributes.
     */
    Termynal.prototype.lineDataToElements = function(container) {
        var lines = Array.prototype.slice.call(container.querySelectorAll('[data-ty]'));
        var lineElements = [];

        lines.forEach((line, index) => {
            var lineData = {
                element: line,
                cursor: null
            };

            if (line.getAttribute(this.pfx + 'cursor')) {
                lineData.cursor = document.createElement('span');
                lineData.cursor.setAttribute('data-ty-cursor', line.getAttribute(this.pfx + 'cursor') || this.cursor);
            }

            lineElements.push(lineData);
        });

        return lineElements;
    };

    /**
     * Utility method to measure the width of a string in the page.
     */
    function strWidth(str) {
        if (!str) return 0;
        const el = document.createElement('div');
        el.style.position = 'absolute';
        el.style.visibility = 'hidden';
        el.style.whiteSpace = 'nowrap';
        el.textContent = str;
        document.body.appendChild(el);
        const width = window.getComputedStyle(el).width;
        document.body.removeChild(el);
        return parseInt(width, 10);
    }

    if (typeof exports != 'undefined') {
        exports.Termynal = Termynal;
    } else {
        window.Termynal = Termynal;
    }

}());
