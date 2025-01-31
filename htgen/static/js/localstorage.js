function saveToStorage(imageData, hashtags) {
    const entry = {
        timestamp: new Date().getTime(),
        image: imageData,
        hashtags: hashtags
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
