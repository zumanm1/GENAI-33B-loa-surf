document.addEventListener('DOMContentLoaded', () => {
    const configPushView = document.getElementById('config-push-view');
    const deviceSelect = document.getElementById('device-select');
    const promptInput = document.getElementById('natural-language-prompt');
    const generateBtn = document.getElementById('generate-config-btn');
    const configOutput = document.getElementById('generated-config-output');
    const pushBtn = document.getElementById('push-config-btn');

    async function fetchDevices() {
        try {
            const response = await fetch('/api/network/devices');
            if (!response.ok) {
                throw new Error('Failed to fetch devices');
            }
            const devices = await response.json();
            deviceSelect.innerHTML = devices.map(device => `<option value="${device.name}">${device.name} (${device.ip})</option>`).join('');
        } catch (error) {
            console.error('Error fetching devices:', error);
            deviceSelect.innerHTML = '<option>Error loading devices</option>';
        }
    }

    async function generateConfig() {
        const device = deviceSelect.value;
        const prompt = promptInput.value;

        if (!device || !prompt) {
            alert('Please select a device and describe the configuration change.');
            return;
        }

        generateBtn.disabled = true;
        generateBtn.textContent = 'Generating...';
        configOutput.textContent = '...';

        try {
            const response = await fetch('/api/ai/generate-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ device, prompt }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate configuration');
            }

            const data = await response.json();
            configOutput.textContent = data.config;
            pushBtn.classList.remove('d-none');
        } catch (error) {
            console.error('Error generating config:', error);
            configOutput.textContent = `Error: ${error.message}`;
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Config';
        }
    }

    async function pushConfig() {
        const device = deviceSelect.value;
        const config = configOutput.textContent;

        if (!confirm(`Are you sure you want to push the following configuration to ${device}?\n\n${config}`)) {
            return;
        }

        pushBtn.disabled = true;
        pushBtn.textContent = 'Pushing...';

        try {
            const response = await fetch('/api/network/push-config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ device, config }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to push configuration');
            }

            const data = await response.json();
            alert(data.message);
            pushBtn.classList.add('d-none');
        } catch (error) {
            console.error('Error pushing config:', error);
            alert(`Error: ${error.message}`);
        } finally {
            pushBtn.disabled = false;
            pushBtn.textContent = 'Push to Device';
        }
    }

    // Listen for view changes to load devices when the view becomes active
    const viewRouter = document.querySelector('body');
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'data-active-view' && viewRouter.dataset.activeView === 'config-push') {
                fetchDevices();
            }
        });
    });

    observer.observe(viewRouter, { attributes: true });

    generateBtn.addEventListener('click', generateConfig);
    pushBtn.addEventListener('click', pushConfig);
});
