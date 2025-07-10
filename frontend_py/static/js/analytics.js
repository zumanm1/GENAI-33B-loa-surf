document.addEventListener('DOMContentLoaded', () => {
    const queriesPerHourEl = document.querySelector('#analytics-view .stat-card:nth-child(1) h4');
    const avgResponseEl = document.querySelector('#analytics-view .stat-card:nth-child(2) h4');
    const accuracyEl = document.querySelector('#analytics-view .stat-card:nth-child(3) h4');

    async function fetchAnalytics() {
        try {
            const resp = await fetch('/api/analytics');
            if (!resp.ok) throw new Error('HTTP ' + resp.status);
            const data = await resp.json();

            if (queriesPerHourEl) queriesPerHourEl.textContent = data.queries_per_hour || 'N/A';
            if (avgResponseEl) avgResponseEl.textContent = (data.avg_response_ms || 'N/A') + 'ms';
            if (accuracyEl) accuracyEl.textContent = (data.accuracy_percent || 'N/A') + '%';

        } catch (e) {
            console.error('Failed to fetch analytics data', e);
            if (queriesPerHourEl) queriesPerHourEl.textContent = 'Error';
            if (avgResponseEl) avgResponseEl.textContent = 'Error';
            if (accuracyEl) accuracyEl.textContent = 'Error';
        }
    }

    // Poll for analytics data when the view is visible
    function maybePollAnalytics() {
        if (window.location.hash === '#analytics') {
            fetchAnalytics();
        }
    }

    // Set up polling and initial load
    window.addEventListener('hashchange', maybePollAnalytics);
    if (window.location.hash === '#analytics') {
        fetchAnalytics(); // Initial load if starting on the page
    }
    setInterval(maybePollAnalytics, 5000); // Poll every 5 seconds
});
