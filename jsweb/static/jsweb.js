// This script gives JsWeb forms a modern, no-reload experience by default.
// A user can opt-out of this by adding `data-jsweb-no-ajax="true"` to a form.

document.addEventListener('DOMContentLoaded', function() {

    document.body.addEventListener('submit', async function(event) {
        const form = event.target;

        // Make sure we're dealing with a form, and that AJAX hasn't been disabled.
        if (form.tagName !== 'FORM' || form.getAttribute('data-jsweb-no-ajax') === 'true') {
            return;
        }

        // Stop the browser's default behavior of a full-page reload.
        event.preventDefault();

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action, {
                method: form.method,
                body: formData,
                headers: {
                    // Let the server know this is an AJAX request.
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            // If the server sent a redirect, we'll follow it.
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const html = await response.text();
            const targetSelector = form.getAttribute('hx-target');

            // If the form has an `hx-target`, we'll update that specific element.
            // This is for more advanced use cases.
            if (targetSelector) {
                const targetElement = document.querySelector(targetSelector);
                if (targetElement) {
                    const swapStrategy = form.getAttribute('hx-swap') || 'innerHTML';
                    if (swapStrategy === 'outerHTML') {
                        targetElement.outerHTML = html;
                    } else {
                        targetElement.innerHTML = html;
                    }
                } else {
                    console.error(`JsWeb AJAX Error: Target element "${targetSelector}" not found.`);
                }
            } else {
                // By default, we swap the entire body. This makes the page update
                // seamlessly without a full reload.
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newBody = doc.querySelector('body');

                if (newBody) {
                    document.body.innerHTML = newBody.innerHTML;
                } else {
                    console.error('JsWeb AJAX Error: Could not find <body> tag in the server response. Page content not updated.');
                }
            }

        } catch (error) {
            console.error('JsWeb AJAX Error:', error);
        }
    });
});
