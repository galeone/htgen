const form = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const result = document.getElementById('result');
const spinner = document.getElementById('spinner');
const languageSelect = document.getElementById('languageSelect');
const topicInput = document.getElementById('topicInput');

function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}

function showNotification(message, isError = false) {
    const notificationContainer = document.getElementById('notificationContainer');
    notificationContainer.style.backgroundColor = isError ? '#dc3545' : '#28a745';
    notificationContainer.textContent = message;
    notificationContainer.style.transform = 'translateX(0)';
    setTimeout(() => {
        notificationContainer.style.transform = 'translateX(150%)';
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Get browser language (e.g., "en-US" -> "en")
    const browserLang = navigator.language.split('-')[0];
    // Check if we support this language
    const supportedLangs = Array.from(languageSelect.options).map(opt => opt.value);
    if (supportedLangs.includes(browserLang)) {
        languageSelect.value = browserLang;
    }
    // Load history
    const history = getFromStorage();
    showHistory(history);

    // Check URL parameters for section=history
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('section') === 'history') {
        // Show history section
        document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));
        document.getElementById('historySection').classList.add('active');

        // Update menu items
        document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
        document.querySelector('.menu-item[data-section="historySection"]').classList.add('active');
    }

    // Show initial connection status if offline
    if (!navigator.onLine) {
        showNotification('You are offline.', true);
        const generateButton = document.querySelector('.generate-button');
        generateButton.disabled = true;
        generateButton.style.opacity = '0.5';
    }
});

// Menu handling
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', () => {
        // Update active menu item
        document.querySelectorAll('.menu-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        // Show corresponding section
        document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));
        const sectionId = item.getAttribute('data-section');
        document.getElementById(sectionId).classList.add('active');

        // Update URL based on section
        const url = new URL(window.location);
        if (sectionId === 'homeSection') {
            url.searchParams.delete('section');
        } else if (sectionId === 'historySection') {
            url.searchParams.set('section', 'history');
        }
        history.pushState({}, '', url);
    });
});

// Function to remove selected image
function removeImage() {
    document.getElementById('preview').src = '';
    document.getElementById('imagePreview').style.display = 'none';
    document.getElementById('cameraPlaceholder').style.display = 'flex';
    fileInput.value = ''; // Clear the file input
}

// Click handler for camera placeholder
document.getElementById('cameraPlaceholder').addEventListener('click', () => {
    fileInput.click();
});

const ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "webp", "heic", "heif"];

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        if (!ALLOWED_EXTENSIONS.includes(file.name.split('.').pop().toLowerCase())) {
            showNotification('Please select a valid image file.', true);
            fileInput.value = '';
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('preview').src = e.target.result;
            document.getElementById('imagePreview').style.display = 'block';
            document.getElementById('cameraPlaceholder').style.display = 'none';
        };
        reader.readAsDataURL(file);
    }
});

// Track last submission parameters to prevent duplicate submissions
let lastSubmission = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData();
    const file = fileInput.files[0];

    if (!file) {
        showResult('Please select an image file.', false);
        return;
    }

    // Create a submission signature
    const currentSubmission = {
        fileName: file.name,
        fileSize: file.size,
        fileLastModified: file.lastModified,
        language: languageSelect.value,
        topic: topicInput.value.trim()
    };

    // Get current image data
    const reader = new FileReader();
    reader.readAsDataURL(file);

    await new Promise((resolve, reject) => {
        reader.onload = () => resolve();
        reader.onerror = () => reject(reader.error);
    });

    // Check history for matching submission
    const history = getFromStorage();
    const matchingEntry = history.find(entry =>
        entry.image === reader.result &&
        entry.language === currentSubmission.language &&
        // entry.topic can be stored as null or "" in case of no topic
        (entry.topic === currentSubmission.topic || (!entry.topic && !currentSubmission.topic))
    );

    if (matchingEntry) {
        showHashtagsWithCopy(matchingEntry.hashtags.join(' '));
        return;
    }

    // Update last submission
    lastSubmission = currentSubmission;

    // Disable button, hide button text, show spinner, and hide previous results
    const generateButton = form.querySelector('.generate-button');
    generateButton.disabled = true;
    generateButton.style.opacity = '0';
    spinner.style.display = 'block';
    result.style.display = 'none';
    formData.append('file', file);
    formData.append('language', languageSelect.value);
    if (topicInput.value.trim()) {
        formData.append('topic', topicInput.value.trim());
    }

    try {
        const response = await fetch('/hashtags', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (!data.error) {
            const hashtags = data.hashtags.join(' ');
            showHashtagsWithCopy(hashtags);
            // Save to localStorage after successful generation
            const imageData = preview.src;
            saveToStorage(imageData, data.hashtags, languageSelect.value, topicInput.value.trim());
            // Update history section
            const history = getFromStorage();
            if (history.length > 0) {
                showHistory(history);
            }
        } else {
            showResult('Error: ' + data.error, false);
        }
    } catch (error) {
        showResult('Error: ' + error, false);
    } finally {
        // Hide spinner, show button and re-enable it
        spinner.style.display = 'none';
        generateButton.style.opacity = '1';
        generateButton.disabled = false;
    }
});

function showHashtagsWithCopy(hashtags) {
    result.innerHTML = `
        <div class="hashtags-container success" style="margin-top: 20px;">
            <div class="hashtags-text">${hashtags}</div>
            <button class="copy-button" onclick="copyHashtags(this)">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
                <svg class="check" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
            </button>
        </div>
    `;
    result.style.display = 'block';
    result.className = ''; // Reset class - remove error/success

    // Scroll to the result
    result.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

function copyHashtags(button) {
    const hashtagsText = button.parentElement.querySelector('.hashtags-text').textContent;
    navigator.clipboard.writeText(hashtagsText).then(() => {
        button.classList.add('copied');
        setTimeout(() => {
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy text: ', err);
    });
}

function showResult(message, isSuccess) {
    result.textContent = message;
    result.style.display = 'block';
    result.className = isSuccess ? 'success' : 'error';

    // Scroll to error messages too
    result.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest'
    });
}

function showHistory(entries) {
    let content;
    if (entries.length === 0) {
        content = `
            <div class="empty-history">
                <p>Your generated hashtags will appear here!</p>
                <p>Upload an image in the Home section to get started.</p>
            </div>
        `;
    } else {
        content = entries.map(entry => {
            const date = new Date(entry.timestamp);
            const formattedDate = date.toLocaleString();
            return `
            <div class="history-entry">
                <button class="remove-history" onclick="deleteHistoryEntry(${entry.timestamp})">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
                <img src="${entry.image}" class="history-thumbnail">
                <div class="entry-meta">
                    <div class="meta-info">
                        <span class="timestamp">${formattedDate}</span>
                        <span class="language-tag">${capitalizeFirstLetter(entry.language)}</span>
                        ${entry.topic ? `<span class="topic-tag">Topic: ${entry.topic}</span>` : ''}
                    </div>
                </div>
                <div class="hashtags-container success">
                    <div class="hashtags-text">${entry.hashtags.join(' ')}</div>
                    <button class="copy-button" onclick="copyHashtags(this)">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                        <svg class="check" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
            `;
        }).join('');
    }

    document.getElementById('historySection').innerHTML = `
        <h2>Previous Generations</h2>
        ${content}
    `;
}

// Delete history entry
function deleteHistoryEntry(timestamp) {
    const history = deleteFromStorage(timestamp);
    showHistory(history);
}