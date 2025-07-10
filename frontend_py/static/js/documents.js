document.addEventListener('DOMContentLoaded', () => {
    const listContainer = document.querySelector('.document-list');
    const uploadBtn = document.getElementById('upload-doc-btn');
    const fileInput = document.getElementById('doc-upload-input');

    async function loadDocuments() {
        try {
            const resp = await fetch('/api/rag/list');
            const data = await resp.json();
            listContainer.innerHTML = '';
            if (Array.isArray(data.documents) && data.documents.length) {
                data.documents.forEach(name => {
                    const div = document.createElement('div');
                    div.className = 'doc-item';
                    div.textContent = name;
                    listContainer.appendChild(div);
                });
            } else {
                listContainer.innerHTML = '<p>No documents uploaded.</p>';
            }
        } catch (e) {
            console.error('Error loading documents', e);
            listContainer.innerHTML = '<p class="error">Failed to load documents</p>';
        }
    }

    uploadBtn?.addEventListener('click', () => fileInput.click());

    fileInput?.addEventListener('change', async () => {
        if (!fileInput.files.length) return;
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        try {
            const resp = await fetch('/api/rag/upload', { method: 'POST', body: formData });
            const data = await resp.json();
            if (resp.ok) {
                alert(data.message || 'Uploaded successfully');
                loadDocuments();
            } else {
                alert(data.error || 'Upload failed');
            }
        } catch (e) {
            alert('Upload failed');
        } finally {
            fileInput.value = '';
        }
    });

    // initial load when documents view is shown via router
    window.addEventListener('hashchange', () => {
        if (window.location.hash === '#documents') loadDocuments();
    });
    if (window.location.hash === '#documents') loadDocuments();
});
