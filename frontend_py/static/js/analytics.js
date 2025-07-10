document.addEventListener('DOMContentLoaded', function() {
    // Initialize date pickers with default values
    const today = new Date();
    const weekAgo = new Date();
    weekAgo.setDate(today.getDate() - 7);
    
    document.getElementById('startDate').valueAsDate = weekAgo;
    document.getElementById('endDate').valueAsDate = today;
    
    // Initial load
    loadAnalyticsData();
    
    // Event listeners for controls
    document.getElementById('timeRange').addEventListener('change', function() {
        // Disable custom date range when preset is selected
        const customRange = document.querySelector('.date-range-picker');
        if (this.value !== 'custom') {
            customRange.classList.add('disabled');
            loadAnalyticsData();
        } else {
            customRange.classList.remove('disabled');
        }
    });
    
    document.getElementById('applyDateRange').addEventListener('click', function() {
        document.getElementById('timeRange').value = 'custom';
        loadAnalyticsData();
    });
    
    document.getElementById('refreshAnalytics').addEventListener('click', loadAnalyticsData);
    
    document.getElementById('exportData').addEventListener('click', exportAnalyticsData);
    
    // Main function to load analytics data
    function loadAnalyticsData() {
        // Show loading state
        showLoading();
        
        // Determine date range
        let params = {};
        const timeRange = document.getElementById('timeRange').value;
        
        if (timeRange === 'custom') {
            params.start_date = document.getElementById('startDate').value;
            params.end_date = document.getElementById('endDate').value;
        } else {
            params.time_range = timeRange;
        }
        
        // Build query string
        const queryString = Object.keys(params)
            .map(key => `${key}=${encodeURIComponent(params[key])}`)
            .join('&');
        
        // Fetch analytics data
        fetch(`/api/analytics?${queryString}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                    hideLoading();
                    return;
                }
                
                // Update UI with data
                updateMetrics(data.metrics);
                updateCharts(data);
                updateAlerts(data.alerts);
                updateInsights(data.insights);
                
                hideLoading();
            })
            .catch(error => {
                console.error('Error fetching analytics:', error);
                showNotification('Failed to load analytics data. Please try again.', 'error');
                hideLoading();
                
                // Load placeholder data for demonstration
                loadPlaceholderData();
            });
    }
    
    function updateMetrics(metrics) {
        // If no metrics data, use placeholders
        if (!metrics) {
            metrics = {
                device_count: 12,
                device_trend: 8.3,
                alert_count: 7,
                alert_trend: 15.2,
                bandwidth_avg: 267.4,
                bandwidth_trend: 5.7,
                ai_query_count: 124,
                ai_query_trend: 23.8
            };
        }
        
        // Update device metrics
        document.getElementById('deviceCount').textContent = metrics.device_count || '0';
        updateTrend('deviceTrend', metrics.device_trend || 0);
        
        // Update alert metrics
        document.getElementById('alertCount').textContent = metrics.alert_count || '0';
        updateTrend('alertTrend', metrics.alert_trend || 0);
        
        // Update bandwidth metrics
        document.getElementById('bandwidthAvg').textContent = `${metrics.bandwidth_avg || '0'} Mbps`;
        updateTrend('bandwidthTrend', metrics.bandwidth_trend || 0);
        
        // Update AI query metrics
        document.getElementById('aiQueryCount').textContent = metrics.ai_query_count || '0';
        updateTrend('aiQueryTrend', metrics.ai_query_trend || 0);
    }
    
    function updateTrend(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        // Format the percentage
        element.textContent = `${Math.abs(value).toFixed(1)}%`;
        
        // Set the appropriate trend class and icon
        const parentElement = element.parentElement;
        if (value > 0) {
            parentElement.className = 'metric-trend positive';
            parentElement.innerHTML = `<i class="fas fa-arrow-up"></i> <span id="${elementId}">${Math.abs(value).toFixed(1)}%</span>`;
        } else if (value < 0) {
            parentElement.className = 'metric-trend negative';
            parentElement.innerHTML = `<i class="fas fa-arrow-down"></i> <span id="${elementId}">${Math.abs(value).toFixed(1)}%</span>`;
        } else {
            parentElement.className = 'metric-trend neutral';
            parentElement.innerHTML = `<i class="fas fa-minus"></i> <span id="${elementId}">${Math.abs(value).toFixed(1)}%</span>`;
        }
    }
    
    function updateCharts(data) {
        // Network Traffic Chart
        updateNetworkTrafficChart(data.network_traffic || createPlaceholderTrafficData());
        
        // Device Health Chart
        updateDeviceHealthChart(data.device_health || createPlaceholderHealthData());
        
        // AI Usage Chart
        updateAiUsageChart(data.ai_usage || createPlaceholderAiUsageData());
    }
    
    function updateNetworkTrafficChart(trafficData) {
        const ctx = document.getElementById('networkTrafficChart').getContext('2d');
        
        // Destroy previous chart instance if it exists
        if (window.networkTrafficChart) {
            window.networkTrafficChart.destroy();
        }
        
        // Create labels (dates/times)
        const labels = trafficData.labels || [];
        
        // Create datasets
        const datasets = [];
        
        // Inbound traffic dataset
        if (trafficData.inbound) {
            datasets.push({
                label: 'Inbound',
                data: trafficData.inbound,
                borderColor: '#36b37e',
                backgroundColor: 'rgba(54, 179, 126, 0.1)',
                tension: 0.4,
                fill: true
            });
        }
        
        // Outbound traffic dataset
        if (trafficData.outbound) {
            datasets.push({
                label: 'Outbound',
                data: trafficData.outbound,
                borderColor: '#4c9aff',
                backgroundColor: 'rgba(76, 154, 255, 0.1)',
                tension: 0.4,
                fill: true
            });
        }
        
        // Create chart
        window.networkTrafficChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Traffic (Mbps)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }
    
    function updateDeviceHealthChart(healthData) {
        const ctx = document.getElementById('deviceHealthChart').getContext('2d');
        
        // Destroy previous chart instance if it exists
        if (window.deviceHealthChart) {
            window.deviceHealthChart.destroy();
        }
        
        // Create chart
        window.deviceHealthChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: healthData.devices || [],
                datasets: [{
                    label: 'Health Score',
                    data: healthData.scores || [],
                    backgroundColor: function(context) {
                        const score = context.raw;
                        if (score >= 80) return 'rgba(54, 179, 126, 0.7)'; // Green for good
                        if (score >= 60) return 'rgba(255, 204, 0, 0.7)';  // Yellow for caution
                        return 'rgba(255, 86, 48, 0.7)'; // Red for poor
                    },
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Health Score (%)'
                        }
                    }
                }
            }
        });
    }
    
    function updateAiUsageChart(aiData) {
        const ctx = document.getElementById('aiUsageChart').getContext('2d');
        
        // Destroy previous chart instance if it exists
        if (window.aiUsageChart) {
            window.aiUsageChart.destroy();
        }
        
        // Create chart
        window.aiUsageChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Chat Queries', 'Network Analysis', 'Document Assistance'],
                datasets: [{
                    data: [
                        aiData.chat_queries || 0,
                        aiData.network_analysis || 0,
                        aiData.document_assistance || 0
                    ],
                    backgroundColor: [
                        '#4c9aff', // Blue
                        '#36b37e', // Green
                        '#ff5630'  // Red
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // We have custom legend below chart
                    }
                }
            }
        });
    }
    
    function updateAlerts(alerts) {
        const tbody = document.getElementById('alertRows');
        
        // If no alert data, keep sample data
        if (!alerts || alerts.length === 0) return;
        
        tbody.innerHTML = ''; // Clear existing rows
        
        alerts.forEach(alert => {
            const row = document.createElement('tr');
            
            // Severity
            const severityCell = document.createElement('td');
            const severityBadge = document.createElement('span');
            severityBadge.className = `alert-badge ${alert.severity.toLowerCase()}`;
            severityBadge.textContent = alert.severity;
            severityCell.appendChild(severityBadge);
            row.appendChild(severityCell);
            
            // Device
            const deviceCell = document.createElement('td');
            deviceCell.textContent = alert.device;
            row.appendChild(deviceCell);
            
            // Alert Type
            const typeCell = document.createElement('td');
            typeCell.textContent = alert.type;
            row.appendChild(typeCell);
            
            // Time
            const timeCell = document.createElement('td');
            timeCell.textContent = formatTimeAgo(alert.timestamp);
            row.appendChild(timeCell);
            
            // Status
            const statusCell = document.createElement('td');
            const statusBadge = document.createElement('span');
            statusBadge.className = `status-badge ${alert.status.toLowerCase()}`;
            statusBadge.textContent = alert.status;
            statusCell.appendChild(statusBadge);
            row.appendChild(statusCell);
            
            tbody.appendChild(row);
        });
    }
    
    function updateInsights(insights) {
        const container = document.getElementById('insightsContainer');
        
        // If no insights data, keep sample insights
        if (!insights || insights.length === 0) return;
        
        container.innerHTML = ''; // Clear existing cards
        
        insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'insight-card';
            
            const icon = document.createElement('div');
            icon.className = 'insight-icon';
            icon.innerHTML = '<i class="fas fa-lightbulb"></i>';
            
            const content = document.createElement('div');
            content.className = 'insight-content';
            
            const title = document.createElement('h4');
            title.textContent = insight.title;
            
            const description = document.createElement('p');
            description.textContent = insight.description;
            
            content.appendChild(title);
            content.appendChild(description);
            
            card.appendChild(icon);
            card.appendChild(content);
            
            container.appendChild(card);
        });
    }
    
    function exportAnalyticsData() {
        // Start loading indicator
        const btn = document.getElementById('exportData');
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
        
        // Determine date range
        let params = {};
        const timeRange = document.getElementById('timeRange').value;
        
        if (timeRange === 'custom') {
            params.start_date = document.getElementById('startDate').value;
            params.end_date = document.getElementById('endDate').value;
        } else {
            params.time_range = timeRange;
        }
        
        // Add export format
        params.format = 'csv';
        
        // Build query string
        const queryString = Object.keys(params)
            .map(key => `${key}=${encodeURIComponent(params[key])}`)
            .join('&');
        
        // Create a temporary download link
        const link = document.createElement('a');
        link.href = `/api/analytics/export?${queryString}`;
        link.download = `network_analytics_export_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Restore button state
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }, 1000);
    }
    
    // Helper functions
    function showLoading() {
        const panels = document.querySelectorAll('.chart-container');
        panels.forEach(panel => {
            panel.classList.add('loading');
        });
    }
    
    function hideLoading() {
        const panels = document.querySelectorAll('.chart-container');
        panels.forEach(panel => {
            panel.classList.remove('loading');
        });
    }
    
    function formatTimeAgo(timestamp) {
        if (!timestamp) return 'Unknown';
        
        const date = new Date(timestamp);
        const now = new Date();
        const diffSeconds = Math.floor((now - date) / 1000);
        
        if (diffSeconds < 60) return 'Just now';
        if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)} minutes ago`;
        if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)} hours ago`;
        if (diffSeconds < 604800) return `${Math.floor(diffSeconds / 86400)} days ago`;
        
        return date.toLocaleDateString();
    }
    
    function loadPlaceholderData() {
        // Update metrics with placeholder data
        updateMetrics({
            device_count: 12,
            device_trend: 8.3,
            alert_count: 7,
            alert_trend: 15.2,
            bandwidth_avg: 267.4,
            bandwidth_trend: 5.7,
            ai_query_count: 124,
            ai_query_trend: 23.8
        });
        
        // Update charts with placeholder data
        updateCharts({
            network_traffic: createPlaceholderTrafficData(),
            device_health: createPlaceholderHealthData(),
            ai_usage: createPlaceholderAiUsageData()
        });
    }
    
    function createPlaceholderTrafficData() {
        // Create labels for the past week
        const labels = [];
        const inbound = [];
        const outbound = [];
        
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
            
            // Generate random traffic values with a trend
            inbound.push(Math.floor(Math.random() * 300) + 200);
            outbound.push(Math.floor(Math.random() * 200) + 100);
        }
        
        return {
            labels: labels,
            inbound: inbound,
            outbound: outbound
        };
    }
    
    function createPlaceholderHealthData() {
        return {
            devices: ['Router1', 'Switch2', 'Firewall1', 'Switch3', 'Router2', 'AP1'],
            scores: [95, 87, 76, 63, 91, 82]
        };
    }
    
    function createPlaceholderAiUsageData() {
        return {
            chat_queries: 65,
            network_analysis: 25,
            document_assistance: 10
        };
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
