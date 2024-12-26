// Function to handle single file upload
function uploadSingleFile() {
    const singleFileInput = document.getElementById('singleFile');
    if (singleFileInput.files.length === 0) {
        alert('Please select a file to upload!');
        return;
    }

    const formData = new FormData();
    formData.append('singleFile', singleFileInput.files[0]);

    fetch('/upload/syllabus', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
    })
    .catch(error => {
        console.error('Error uploading syllabus file:', error);
        alert('Failed to upload syllabus file. Check console for details.');
    });
}


// Function to handle multiple files upload
function uploadMultipleFiles() {
    const multipleFilesInput = document.getElementById('multipleFiles');
    if (multipleFilesInput.files.length === 0) {
        alert('Please select files to upload!');
        return;
    }

    const formData = new FormData();
    for (const file of multipleFilesInput.files) {
        formData.append('multipleFiles', file);
    }

    fetch('/upload/questions', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        alert(`Files uploaded: ${data.files.join(', ')}`);
    })
    .catch(error => {
        console.error('Error uploading question files:', error);
        alert('Failed to upload question files. Check console for details.');
    });
}


function processFiles() {
    fetch('/process', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        alert(`Syllabus Files: ${data.syllabus_files.join(', ')}\nQuestion Files: ${data.question_files.join(', ')}`);
        window.location.href = "/process";
    })
    .catch(error => {
        console.error('Error processing files:', error);
        alert('Failed to process files. Check console for details.');
    });
}

async function fetchUserId() {
    const response = await fetch('/get-user-id');
    
    if (response.ok) {
        const data = await response.json();
        const userId = data.user_id;

        // Store the user_id in localStorage for later use
        localStorage.setItem('userId', userId);
    } else {
        console.error('Failed to fetch user ID');
    }
}

// Call the function when the page loads
window.onload = fetchUserId;

async function saveApiKey() {
    const apiKey = document.getElementById('gemini_api_key').value;

    if (!apiKey) {
        alert('Please enter your GEMINI API Key.');
        return;
    }

    // Fetch the userId from localStorage
    const userId = localStorage.getItem('userId');
    if (!userId) {
        alert('User ID not found. Please refresh the page.');
        return;
    }

    // Send the API key and user ID to the server
    const response = await fetch('/save-api-key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            apiKey: apiKey,
            userId: userId,
        }),
    });

    if (response.ok) {
        const data = await response.json();
        alert(data.message);
    } else {
        alert('Failed to save API key. Please try again.');
    }
}
