// Simple view router for genai_networks_engineer single-page interface
(function () {
    const views = ['configuration', 'chat', 'documents', 'network-ops', 'analytics'];

    function $id(id) { return document.getElementById(id); }

    function updateSidebarActiveState(view) {
        document.querySelectorAll('.sidebar .nav-item').forEach(el => {
            if (el.dataset.view === view) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });
    }

    function showView(view) {
        views.forEach(v => {
            const el = $id(`${v}-view`);
            if (el) el.style.display = v === view ? 'flex' : 'none';
        });
        updateSidebarActiveState(view);
        sessionStorage.setItem('activeView', view);
    }

    function init() {
        // attach click listeners
        document.querySelectorAll('.sidebar .nav-item').forEach(el => {
            el.addEventListener('click', (e) => {
                const view = el.dataset.view;
                if (view) {
                    e.preventDefault();
                    window.location.hash = view; // bookmarkable
                    showView(view);
                }
            });
        });

        // initial view
        const hashView = window.location.hash.slice(1);
        const saved = sessionStorage.getItem('activeView');
        const initial = views.includes(hashView) ? hashView : (views.includes(saved) ? saved : 'configuration');
        showView(initial);

        // respond to hash changes (back/forward buttons)
        window.addEventListener('hashchange', () => {
            const hv = window.location.hash.slice(1);
            if (views.includes(hv)) showView(hv);
        });
    }

    document.addEventListener('DOMContentLoaded', init);
})();
