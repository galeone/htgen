function saveToStorage(imageData, hashtags, language, topic) {
    const entry = {
        timestamp: new Date().getTime(),
        image: imageData,
        hashtags: hashtags,
        language: language,
        topic: topic || null
    };

    // Get existing entries or initialize array
    const history = JSON.parse(localStorage.getItem('htgenHistory') || '[]');
    history.push(entry);

    // Save updated array. Localstorage is limited in space, so we try to set the item
    // and if an exception is thrown, we pop the first element and try again.
    let attempts = 0;
    while (attempts < 3) {
        try {
            localStorage.setItem('htgenHistory', JSON.stringify(history));
            return;
        } catch (e) {
            history.shift();
            attempts++;
        }
    }
}

function getFromStorage() {
    return JSON.parse(localStorage.getItem('htgenHistory') || '[]').reverse();
}

function deleteFromStorage(timestamp) {
    let history = JSON.parse(localStorage.getItem('htgenHistory') || '[]');
    history = history.filter(entry => entry.timestamp !== timestamp);
    localStorage.setItem('htgenHistory', JSON.stringify(history));
    return history.reverse();
}