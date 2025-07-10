document.addEventListener('DOMContentLoaded', function() {
    // Tab navigation
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the tab to show from the data attribute
            const tabToShow = this.getAttribute('data-tab');
            
            // Find parent container (either config-tabs or operations-tabs)
            const isConfigTab = this.closest('.config-tabs') !== null;
            
            // Get all tabs in the same container
            const tabContainer = isConfigTab ? '.config-content' : '.operations-content';
            const tabs = document.querySelectorAll(`${tabContainer} .tab-content`);
            
            // Hide all tabs
            tabs.forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show the selected tab
            document.getElementById(tabToShow).classList.add('active');
            
            // Update active state on buttons
            const buttonsContainer = isConfigTab ? '.config-tabs' : '.operations-tabs';
            const buttons = document.querySelectorAll(`${buttonsContainer} .tab-btn`);
            buttons.forEach(btn => {
                btn.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
    
    // Modal handling
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.modal .close, .modal .btn-cancel');
    
    // Open modal functions
    document.getElementById('addDeviceBtn').addEventListener('click', function() {
        document.getElementById('addDeviceModal').style.display = 'block';
    });
    
    document.getElementById('proposeChangeBtn').addEventListener('click', function() {
        document.getElementById('proposeChangeModal').style.display = 'block';
    });
    
    // Close modal functions
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Close modal when clicking outside of it
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Device list functions
    loadDevices();
    
    document.getElementById('refreshDevicesBtn').addEventListener('click', function() {
        loadDevices();
    });
    
    document.getElementById('searchDevicesBtn').addEventListener('click', function() {
        const searchQuery = document.getElementById('deviceSearch').value.trim();
        loadDevices(searchQuery);
    });
    
    document.getElementById('deviceSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const searchQuery = this.value.trim();
            loadDevices(searchQuery);
        }
    });
    
    // Add device form submission
    document.getElementById('addDeviceForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const deviceData = {
            hostname: document.getElementById('deviceHostname').value,
            ip_address: document.getElementById('deviceIp').value,
            device_type: document.getElementById('deviceType').value,
            vendor: document.getElementById('deviceVendor').value,
            credential_profile: document.getElementById('deviceCredentials').value
        };
        
        // Disable submit button and show loading state
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
        
        fetch('/api/devices', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(deviceData)
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification('Device added successfully!', 'success');
                document.getElementById('addDeviceModal').style.display = 'none';
                
                // Reset the form
                document.getElementById('addDeviceForm').reset();
                
                // Refresh device list
                loadDevices();
            }
        })
        .catch(error => {
            console.error('Error adding device:', error);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            showNotification('An error occurred while adding the device.', 'error');
        });
    });
    
    // Propose change form submission
    document.getElementById('proposeChangeForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const currentDevice = document.getElementById('selectedDeviceTitle').textContent;
        if (!currentDevice || currentDevice === 'Device Name') {
            showNotification('No device selected.', 'error');
            return;
        }
        
        const proposalData = {
            hostname: currentDevice,
            proposed_config: document.getElementById('configChanges').value,
            description: document.getElementById('changeDescription').value
        };
        
        // Disable submit button and show loading state
        const submitBtn = this.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        
        fetch('/api/proposals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(proposalData)
        })
        .then(response => response.json())
        .then(data => {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            
            if (data.error) {
                showNotification(data.error, 'error');
            } else {
                showNotification('Change proposal submitted successfully!', 'success');
                document.getElementById('proposeChangeModal').style.display = 'none';
                
                // Reset the form
                document.getElementById('proposeChangeForm').reset();
                
                // Load the proposals tab
                document.querySelector('.config-tabs [data-tab="proposed-changes"]').click();
                loadProposals(currentDevice);
            }
        })
        .catch(error => {
            console.error('Error submitting proposal:', error);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            showNotification('An error occurred while submitting the proposal.', 'error');
        });
    });
    
    // Network AI Assistant
    document.getElementById('sendNetworkQueryBtn').addEventListener('click', sendNetworkQuery);
    document.getElementById('networkAiInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendNetworkQuery();
        }
    });
    
    // Initialize Chart for network stats
    const ctx = document.getElementById('networkChart').getContext('2d');
    const networkChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [], // Will be populated with timestamps
            datasets: [{
                label: 'Traffic (Mbps)',
                data: [], // Will be populated with data points
                borderColor: '#4c9aff',
                backgroundColor: 'rgba(76, 154, 255, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Network Traffic (Mbps)'
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
    
    // Functions for loading data
    function loadDevices(searchQuery = '') {
        const tbody = document.getElementById('deviceRows');
        tbody.innerHTML = '<tr class="loading-row"><td colspan="5"><i class="fas fa-spinner fa-spin"></i> Loading devices...</td></tr>';
        
        let url = '/api/devices';
        if (searchQuery) {
            url += `?search=${encodeURIComponent(searchQuery)}`;
        }
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                tbody.innerHTML = '';
                
                if (!data || data.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5">No devices found.</td></tr>';
                    return;
                }
                
                data.forEach(device => {
                    const row = document.createElement('tr');
                    
                    // Hostname
                    const hostname = document.createElement('td');
                    hostname.textContent = device.hostname;
                    row.appendChild(hostname);
                    
                    // IP Address
                    const ip = document.createElement('td');
                    ip.textContent = device.ip_address;
                    row.appendChild(ip);
                    
                    // Type
                    const type = document.createElement('td');
                    type.textContent = formatDeviceType(device.device_type);
                    row.appendChild(type);
                    
                    // Status
                    const status = document.createElement('td');
                    const statusIndicator = document.createElement('span');
                    statusIndicator.className = `status-indicator ${device.status ? 'online' : 'offline'}`;
                    status.appendChild(statusIndicator);
                    status.appendChild(document.createTextNode(device.status ? 'Online' : 'Offline'));
                    row.appendChild(status);
                    
                    // Actions
                    const actions = document.createElement('td');
                    actions.className = 'device-actions';
                    
                    // View button
                    const viewBtn = document.createElement('button');
                    viewBtn.className = 'btn-icon';
                    viewBtn.innerHTML = '<i class="fas fa-eye"></i>';
                    viewBtn.title = 'View Configuration';
                    viewBtn.addEventListener('click', () => selectDevice(device.hostname));
                    actions.appendChild(viewBtn);
                    
                    // Edit button
                    const editBtn = document.createElement('button');
                    editBtn.className = 'btn-icon';
                    editBtn.innerHTML = '<i class="fas fa-edit"></i>';
                    editBtn.title = 'Edit Device';
                    editBtn.addEventListener('click', () => editDevice(device.hostname));
                    actions.appendChild(editBtn);
                    
                    // Delete button
                    const deleteBtn = document.createElement('button');
                    deleteBtn.className = 'btn-icon delete';
                    deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
                    deleteBtn.title = 'Delete Device';
                    deleteBtn.addEventListener('click', () => deleteDevice(device.hostname));
                    actions.appendChild(deleteBtn);
                    
                    row.appendChild(actions);
                    tbody.appendChild(row);
                });
            })
            .catch(error => {
                console.error('Error loading devices:', error);
                tbody.innerHTML = '<tr><td colspan="5">Error loading devices. Please try again.</td></tr>';
            });
    }
    
    function selectDevice(hostname) {
        // Show device details panel
        document.querySelector('.no-device-selected').style.display = 'none';
        document.querySelector('.device-detail').style.display = 'block';
        
        // Set device title
        document.getElementById('selectedDeviceTitle').textContent = hostname;
        
        // Show loading state for config
        document.getElementById('configOutput').textContent = 'Loading configuration...';
        
        // Make API call to get device details and configuration
        fetch(`/api/devices/${encodeURIComponent(hostname)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                    document.getElementById('configOutput').textContent = 'Error loading configuration.';
                } else {
                    // Update device type badge
                    document.getElementById('deviceTypeBadge').textContent = formatDeviceType(data.device_type);
                    
                    // Update status badge
                    const statusBadge = document.getElementById('deviceStatusBadge');
                    statusBadge.textContent = data.status ? 'Online' : 'Offline';
                    statusBadge.className = `badge ${data.status ? 'status-online' : 'status-offline'}`;
                    
                    // Update configuration display
                    document.getElementById('configOutput').textContent = data.config || 'No configuration available.';
                    
                    // Load device stats
                    loadDeviceStats(hostname);
                    
                    // Load proposals for this device
                    loadProposals(hostname);
                }
            })
            .catch(error => {
                console.error('Error loading device details:', error);
                document.getElementById('configOutput').textContent = 'Error loading configuration. Please try again.';
                showNotification('An error occurred while loading device details.', 'error');
            });
    }
    
    function loadDeviceStats(hostname) {
        // Make API call to get device statistics
        fetch(`/api/devices/${encodeURIComponent(hostname)}/stats`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error('Error loading stats:', data.error);
                } else {
                    // Update stats display
                    document.getElementById('uptimeStat').textContent = formatUptime(data.uptime);
                    document.getElementById('cpuStat').textContent = `${data.cpu_usage}%`;
                    document.getElementById('memoryStat').textContent = `${data.memory_usage}%`;
                    document.getElementById('interfacesStat').textContent = `${data.active_interfaces}/${data.total_interfaces}`;
                    
                    // Update chart with traffic data
                    updateTrafficChart(networkChart, data.traffic_history);
                }
            })
            .catch(error => {
                console.error('Error loading device stats:', error);
            });
    }
    
    function loadProposals(hostname) {
        const proposalsList = document.getElementById('proposalsList');
        proposalsList.innerHTML = '<p><i class="fas fa-spinner fa-spin"></i> Loading proposals...</p>';
        
        fetch(`/api/proposals?hostname=${encodeURIComponent(hostname)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error || !data.proposals || data.proposals.length === 0) {
                    proposalsList.innerHTML = '<p>No proposed changes for this device.</p>';
                    return;
                }
                
                proposalsList.innerHTML = '';
                data.proposals.forEach(proposal => {
                    const proposalCard = document.createElement('div');
                    proposalCard.className = 'proposal-card';
                    
                    const header = document.createElement('div');
                    header.className = 'proposal-header';
                    
                    const title = document.createElement('h4');
                    title.textContent = proposal.description || 'Unnamed proposal';
                    header.appendChild(title);
                    
                    const date = document.createElement('span');
                    date.className = 'proposal-date';
                    date.textContent = formatDate(proposal.created_at);
                    header.appendChild(date);
                    
                    const content = document.createElement('pre');
                    content.className = 'proposal-content';
                    content.textContent = proposal.proposed_config;
                    
                    const actions = document.createElement('div');
                    actions.className = 'proposal-actions';
                    
                    const approveBtn = document.createElement('button');
                    approveBtn.className = 'btn btn-success';
                    approveBtn.textContent = 'Approve';
                    approveBtn.addEventListener('click', () => approveProposal(proposal.id));
                    actions.appendChild(approveBtn);
                    
                    const rejectBtn = document.createElement('button');
                    rejectBtn.className = 'btn btn-danger';
                    rejectBtn.textContent = 'Reject';
                    rejectBtn.addEventListener('click', () => rejectProposal(proposal.id));
                    actions.appendChild(rejectBtn);
                    
                    proposalCard.appendChild(header);
                    proposalCard.appendChild(content);
                    proposalCard.appendChild(actions);
                    proposalsList.appendChild(proposalCard);
                });
            })
            .catch(error => {
                console.error('Error loading proposals:', error);
                proposalsList.innerHTML = '<p>Error loading proposals. Please try again.</p>';
            });
    }
    
    function approveProposal(proposalId) {
        if (confirm('Are you sure you want to approve this configuration change?')) {
            fetch(`/api/proposals/${proposalId}/approve`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification('Proposal approved successfully!', 'success');
                    // Refresh proposals list for the current device
                    loadProposals(document.getElementById('selectedDeviceTitle').textContent);
                }
            })
            .catch(error => {
                console.error('Error approving proposal:', error);
                showNotification('An error occurred while approving the proposal.', 'error');
            });
        }
    }
    
    function rejectProposal(proposalId) {
        if (confirm('Are you sure you want to reject this configuration change?')) {
            fetch(`/api/proposals/${proposalId}/reject`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification('Proposal rejected.', 'success');
                    // Refresh proposals list for the current device
                    loadProposals(document.getElementById('selectedDeviceTitle').textContent);
                }
            })
            .catch(error => {
                console.error('Error rejecting proposal:', error);
                showNotification('An error occurred while rejecting the proposal.', 'error');
            });
        }
    }
    
    function editDevice(hostname) {
        // TODO: Implement device editing functionality
        alert(`Edit device functionality for ${hostname} not yet implemented.`);
    }
    
    function deleteDevice(hostname) {
        if (confirm(`Are you sure you want to delete the device "${hostname}"?`)) {
            fetch(`/api/devices/${encodeURIComponent(hostname)}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    showNotification(data.error, 'error');
                } else {
                    showNotification(`Device "${hostname}" deleted successfully.`, 'success');
                    loadDevices();
                    
                    // If the deleted device was selected, clear the details panel
                    if (document.getElementById('selectedDeviceTitle').textContent === hostname) {
                        document.querySelector('.no-device-selected').style.display = 'block';
                        document.querySelector('.device-detail').style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('Error deleting device:', error);
                showNotification('An error occurred while deleting the device.', 'error');
            });
        }
    }
    
    function sendNetworkQuery() {
        const input = document.getElementById('networkAiInput');
        const query = input.value.trim();
        if (query === '') return;
        
        const networkAiHistory = document.getElementById('networkAiHistory');
        
        // Add user message
        const userMessage = document.createElement('div');
        userMessage.className = 'network-ai-message user-message';
        userMessage.textContent = query;
        networkAiHistory.appendChild(userMessage);
        
        // Add typing indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'network-ai-message ai-message typing-indicator';
        typingIndicator.innerHTML = '<span></span><span></span><span></span>';
        networkAiHistory.appendChild(typingIndicator);
        
        // Clear input
        input.value = '';
        
        // Scroll to bottom
        networkAiHistory.scrollTop = networkAiHistory.scrollHeight;
        
        // Make API call to get AI response
        fetch('/api/network/ai', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add AI response
            const aiMessage = document.createElement('div');
            aiMessage.className = 'network-ai-message ai-message';
            aiMessage.textContent = data.response || 'Sorry, I was unable to process that request.';
            networkAiHistory.appendChild(aiMessage);
            
            // Scroll to bottom
            networkAiHistory.scrollTop = networkAiHistory.scrollHeight;
        })
        .catch(error => {
            console.error('Error getting AI response:', error);
            
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'network-ai-message ai-message error';
            errorMessage.textContent = 'Sorry, an error occurred while processing your request.';
            networkAiHistory.appendChild(errorMessage);
            
            // Scroll to bottom
            networkAiHistory.scrollTop = networkAiHistory.scrollHeight;
        });
    }
    
    // Helper functions
    function formatDeviceType(type) {
        if (!type) return 'Unknown';
        return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ');
    }
    
    function formatUptime(seconds) {
        if (!seconds && seconds !== 0) return 'Unknown';
        
        const days = Math.floor(seconds / (24 * 3600));
        seconds %= (24 * 3600);
        const hours = Math.floor(seconds / 3600);
        seconds %= 3600;
        const minutes = Math.floor(seconds / 60);
        seconds %= 60;
        
        let result = '';
        if (days > 0) result += `${days}d `;
        if (hours > 0 || days > 0) result += `${hours}h `;
        if (minutes > 0 || hours > 0 || days > 0) result += `${minutes}m `;
        result += `${seconds}s`;
        
        return result;
    }
    
    function formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleString();
    }
    
    function updateTrafficChart(chart, trafficData) {
        if (!trafficData || !Array.isArray(trafficData) || trafficData.length === 0) {
            // No data, clear chart
            chart.data.labels = [];
            chart.data.datasets[0].data = [];
            chart.update();
            return;
        }
        
        const labels = trafficData.map(point => {
            const date = new Date(point.timestamp);
            return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        });
        
        const data = trafficData.map(point => point.mbps);
        
        chart.data.labels = labels;
        chart.data.datasets[0].data = data;
        chart.update();
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
