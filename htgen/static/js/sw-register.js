// Service Worker Registration and Message Handling
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register("/sw.js")
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
            })
            .catch(err => {
                console.log('ServiceWorker registration failed: ', err);
            });

        // Listen for messages from the service worker
        navigator.serviceWorker.addEventListener('message', event => {
            if (event.data.type === 'OFFLINE_STATE') {
                const { isOffline, message } = event.data.payload;
                const generateButton = document.querySelector('.generate-button');

                if (isOffline) {
                    // Disable generate button and show offline message
                    generateButton.disabled = true;
                    generateButton.style.opacity = '0.5';
                    showResult(message, false);
                } else {
                    // Re-enable generate button and show online message
                    generateButton.disabled = false;
                    generateButton.style.opacity = '1';
                    showResult(message, true);

                    // Clear the message after a delay
                    setTimeout(() => {
                        result.style.display = 'none';
                    }, 3000);
                }
            }
        });
    });
}
