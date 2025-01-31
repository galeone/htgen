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
    
    // Save updated array
    localStorage.setItem('htgenHistory', JSON.stringify(history));
}

function getFromStorage() {
    return JSON.parse(localStorage.getItem('htgenHistory') || '[]').reverse();
}
