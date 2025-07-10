document.addEventListener('DOMContentLoaded', function() {
    // Document upload form handler
    const uploadForm = document.getElementById('uploadForm');
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        
        // Add the category and description
        const category = document.getElementById('documentCategory').value;
        const description = document.getElementById('documentDescription').value;
        formData.append('category', category);
        formData.append('description', description);
        
        // Show upload progress indicator
        const submitButton = this.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
        
        fetch('/api/upload_document', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Reset the button
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification(data.message || 'Document uploaded successfully!', 'success');
                // Clear the form
                document.getElementById('fileInput').value = '';
                document.getElementById('documentDescription').value = '';
                // Refresh the document list
                loadDocuments();
            }
        })
        .catch(error => {
            console.error('Upload error:', error);
            submitButton.disabled = false;
            submitButton.textContent = originalText;
            showNotification('An error occurred during upload.', 'error');
        });
    });
    
    // Load documents when page loads
    loadDocuments();
    
    // Refresh button handler
    document.getElementById('refreshDocumentsBtn').addEventListener('click', function() {
        loadDocuments();
    });
    
    // Reindex button handler
    document.getElementById('reindexBtn').addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Reindexing...';
        
        fetch('/api/documents/reindex', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification(data.message || 'Vector store reindexed successfully!', 'success');
                loadDocuments(); // Refresh to get updated stats
            }
        })
        .catch(error => {
            console.error('Reindex error:', error);
            btn.disabled = false;
            btn.innerHTML = originalText;
            showNotification('An error occurred while reindexing.', 'error');
        });
    });
    
    // Search functionality
    document.getElementById('searchBtn').addEventListener('click', function() {
        const searchTerm = document.getElementById('documentSearch').value.trim();
        loadDocuments(searchTerm, document.getElementById('categoryFilter').value);
    });
    
    document.getElementById('documentSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchTerm = this.value.trim();
            loadDocuments(searchTerm, document.getElementById('categoryFilter').value);
        }
    });
    
    // Category filter
    document.getElementById('categoryFilter').addEventListener('change', function() {
        const searchTerm = document.getElementById('documentSearch').value.trim();
        loadDocuments(searchTerm, this.value);
    });
    
    function loadDocuments(searchTerm = '', category = 'all') {
        const tbody = document.getElementById('documentRows');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="5"><i class="fas fa-spinner fa-spin"></i> Loading documents...</td></tr>';
        
        // Create query string with filters
        let url = '/api/documents';
        const params = [];
        if (searchTerm) params.push(`search=${encodeURIComponent(searchTerm)}`);
        if (category !== 'all') params.push(`category=${encodeURIComponent(category)}`);
        if (params.length > 0) url += `?${params.join('&')}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                // Update stats
                document.getElementById('totalDocuments').textContent = data.total_documents || 0;
                document.getElementById('vectorStoreSize').textContent = formatFileSize(data.vector_store_size || 0);
                
                // Create document list
                tbody.innerHTML = '';
                
                if (!data.documents || data.documents.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5">No documents found.</td></tr>';
                    return;
                }
                
                data.documents.forEach(doc => {
                    const row = document.createElement('tr');
                    
                    // File name cell
                    const nameCell = document.createElement('td');
                    nameCell.textContent = doc.filename;
                    nameCell.title = doc.description || '';
                    row.appendChild(nameCell);
                    
                    // Category cell
                    const categoryCell = document.createElement('td');
                    categoryCell.textContent = formatCategory(doc.category);
                    row.appendChild(categoryCell);
                    
                    // Upload date cell
                    const dateCell = document.createElement('td');
                    dateCell.textContent = formatDate(doc.upload_date);
                    row.appendChild(dateCell);
                    
                    // Size cell
                    const sizeCell = document.createElement('td');
                    sizeCell.textContent = formatFileSize(doc.size);
                    row.appendChild(sizeCell);
                    
                    // Actions cell
                    const actionsCell = document.createElement('td');
                    actionsCell.className = 'document-actions';
                    
                    // View button
                    const viewBtn = document.createElement('button');
                    viewBtn.className = 'btn-icon';
                    viewBtn.innerHTML = '<i class="fas fa-eye"></i>';
                    viewBtn.title = 'View Document';
                    viewBtn.addEventListener('click', () => viewDocument(doc.id));
                    actionsCell.appendChild(viewBtn);
                    
                    // Delete button
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'btn-icon delete';
                    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                    deleteBtn.title = 'Delete Document';
                    deleteBtn.addEventListener('click', () => deleteDocument(doc.id, doc.filename));
                    actionsCell.appendChild(deleteBtn);
                    
                    row.appendChild(actionsCell);
                    tbody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error loading documents:', error);
                tbody.innerHTML = '<tr><td colspan="5">Error loading documents. Please try again.</td></tr>';
            });
    }
    
    function viewDocument(docId) {
        window.open(`/api/documents/${docId}/view`, '_blank');
    }
    
    function deleteDocument(docId, filename) {
        if (confirm(`Are you sure you want to delete the document "${filename}"?`)) {
            fetch(`/api/documents/${docId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(data.message || 'Document deleted successfully.', 'success');
                    loadDocuments();
                }
            })
            .catch(error => {
                console.error('Delete error:', error);
                showNotification('An error occurred while deleting the document.', 'error');
            });
        }
    }
    
    function formatFileSize(sizeInBytes) {
        if (sizeInBytes < 1024) return sizeInBytes + ' B';
        else if (sizeInBytes < 1024 * 1024) return (sizeInBytes / 1024).toFixed(2) + ' KB';
        else if (sizeInBytes < 1024 * 1024 * 1024) return (sizeInBytes / (1024 * 1024)).toFixed(2) + ' MB';
        else return (sizeInBytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    function formatCategory(category) {
        if (!category) return 'Other';
        
        // Convert snake_case to Title Case
        return category
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
});
