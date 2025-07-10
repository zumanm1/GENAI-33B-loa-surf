document.addEventListener('DOMContentLoaded', () => {
  const tableContainer = document.querySelector('.device-list-panel');

  async function fetchStatus() {
    try {
      const resp = await fetch('/api/network/status');
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      const data = await resp.json();
      render(data.devices || []);
    } catch (e) {
      console.error('Failed to fetch network status', e);
    }
  }

  function render(devices) {
    tableContainer.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'device-table';
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>Hostname</th><th>Status</th><th>CPU %</th><th>Mem %</th></tr>';
    table.appendChild(thead);
    const tbody = document.createElement('tbody');
    devices.forEach(dev => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${dev.hostname}</td><td>${dev.status}</td><td>${dev.cpu}</td><td>${dev.mem}</td>`;
      if (dev.status === 'online') tr.classList.add('online');
      if (dev.status === 'offline') tr.classList.add('offline');
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    tableContainer.appendChild(table);
  }

  // poll when view visible
  function maybePoll() {
    if (window.location.hash === '#network-ops') fetchStatus();
  }
  window.addEventListener('hashchange', maybePoll);
  if (window.location.hash === '#network-ops') fetchStatus();
  setInterval(maybePoll, 10000);
});
