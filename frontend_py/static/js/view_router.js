document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    const viewContainers = document.querySelectorAll('.view-container');

    function switchView(viewName) {
        // Hide all view containers
        viewContainers.forEach(container => {
            if (container) {
                container.classList.add('d-none');
            }
        });

        // Show the target view
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.remove('d-none');
        } else {
            // If view doesn't exist, default to the configuration view
            const defaultConfigView = document.getElementById('configuration-view');
            if (defaultConfigView) {
                defaultConfigView.classList.remove('d-none');
            }
        }

        // Update the active state in the sidebar
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.view === viewName) {
                item.classList.add('active');
            }
        });
    }

    // Handle sidebar navigation clicks
    navItems.forEach(item => {
        item.addEventListener('click', (event) => {
            event.preventDefault();
            const viewName = item.dataset.view;
            window.location.hash = viewName;
        });
    });

    // Function to handle hash changes for routing
    function handleHashChange() {
        const viewName = window.location.hash.substring(1) || 'configuration';
        switchView(viewName);
    }

    // Listen for hash changes to switch views
    window.addEventListener('hashchange', handleHashChange);

    // Initial view setup on page load
    handleHashChange();
});
