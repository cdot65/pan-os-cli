/**
 * custom_termynal.js
 * Initialize all termynal instances on page load
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all elements with the 'data-termynal' attribute
    var elements = document.querySelectorAll('[data-termynal]');

    // Initialize Termynal for each element
    Array.from(elements).forEach(element => {
        new Termynal(element, {
            typeDelay: 40,
            lineDelay: 700,
            progressLength: 30,
            progressChar: '█',
            cursor: '▋',
            startDelay: 600
        });
    });

    // For elements created after initial page load (e.g., within tabs)
    var observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes && mutation.addedNodes.length > 0) {
                for (var i = 0; i < mutation.addedNodes.length; i++) {
                    var node = mutation.addedNodes[i];
                    if (node.nodeType === 1 && node.matches('[data-termynal]:not([data-termynal-initialized])')) {
                        new Termynal(node, {
                            typeDelay: 40,
                            lineDelay: 700,
                            progressLength: 30,
                            progressChar: '█',
                            cursor: '▋',
                            startDelay: 600
                        });
                        node.setAttribute('data-termynal-initialized', 'true');
                    }
                }
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});
