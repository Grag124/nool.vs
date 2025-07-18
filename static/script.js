let updateInterval;

function updateStatus() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('bot-status').textContent = data.active ? 'Active' : 'Inactive';
            document.getElementById('bot-status').className = data.active ? 'status-active' : 'status-inactive';
            document.getElementById('checks-performed').textContent = data.checks_performed;
            document.getElementById('duration').textContent = data.duration || 'Not started';
            document.getElementById('current-time').textContent = data.current_time;
        })
        .catch(error => {
            console.error('Error updating status:', error);
        });
}

function updateLogs() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(data => {
            const logsContainer = document.getElementById('logs-container');
            logsContainer.innerHTML = '';
            data.logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                logEntry.textContent = log;
                logsContainer.appendChild(logEntry);
            });
            logsContainer.scrollTop = logsContainer.scrollHeight;
        })
        .catch(error => {
            console.error('Error updating logs:', error);
        });
}

function startAutoUpdate() {
    updateStatus();
    updateLogs();
    updateInterval = setInterval(() => {
        updateStatus();
        if (Math.random() < 0.3) { // Update logs less frequently
            updateLogs();
        }
    }, 5000);
}

function stopAutoUpdate() {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
}

function refreshAll() {
    updateStatus();
    updateLogs();
}

// Start auto-update when page loads
document.addEventListener('DOMContentLoaded', startAutoUpdate);

// Stop auto-update when page unloads
window.addEventListener('beforeunload', stopAutoUpdate);
