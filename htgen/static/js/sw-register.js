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
    });

    // Handle online/offline events
    window.addEventListener('online', () => {
        showNotification('You are back online!');
        const generateButton = document.querySelector('.generate-button');
        // Re-enable generate button and show online message
        generateButton.disabled = false;
        generateButton.style.opacity = '1';
    });

    window.addEventListener('offline', () => {
        showNotification('You are offline. Changes will be saved locally.', true);
        const generateButton = document.querySelector('.generate-button');
        // Disable generate button and show offline message
        generateButton.disabled = true;
        generateButton.style.opacity = '0.5';
    });
}
