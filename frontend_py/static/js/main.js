document.addEventListener('DOMContentLoaded', function() {
    // Get elements for sidebar toggle
    const sidebar = document.querySelector('.sidebar');
    
    // Check if the toggle button already exists to avoid duplicating it
    if (!document.querySelector('.sidebar-toggle')) {
        // Create toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.innerHTML = '<i class="fas fa-bars"></i>';
        toggleBtn.style.position = 'absolute';
        toggleBtn.style.top = '20px';
        toggleBtn.style.left = sidebar ? (sidebar.offsetWidth + 10) + 'px' : '250px';
        toggleBtn.style.zIndex = '1000';
        toggleBtn.style.background = '#1a1c23';
        toggleBtn.style.border = 'none';
        toggleBtn.style.color = '#fff';
        toggleBtn.style.padding = '8px 12px';
        toggleBtn.style.borderRadius = '4px';
        toggleBtn.style.cursor = 'pointer';
        toggleBtn.style.transition = 'left 0.3s ease';
        
        document.body.appendChild(toggleBtn);
        
        // Toggle sidebar on button click
        toggleBtn.addEventListener('click', function() {
            if (sidebar) {
                sidebar.classList.toggle('collapsed');
                
                // Update button position
                if (sidebar.classList.contains('collapsed')) {
                    toggleBtn.style.left = (sidebar.offsetWidth + 10) + 'px';
                } else {
                    toggleBtn.style.left = (sidebar.offsetWidth + 10) + 'px';
                }
            }
        });
    }
});
