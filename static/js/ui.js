class UIController {
    constructor() {
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.sidebar = document.getElementById('sidebar');
        this.incidentDrawer = document.getElementById('incidentDrawer');
        this.currentIncidents = [];
    }

    showLoading() { this.loadingOverlay.classList.add('visible'); }
    hideLoading() { this.loadingOverlay.classList.remove('visible'); }

    updateStats(incidents) {
        const total = incidents.reduce((sum, i) => sum + i.count, 0);
        const uniqueIPs = incidents.length;
        const countries = new Set(incidents.map(i => i.geo.country)).size;
        const failed = incidents.filter(i => i.types.includes('failed_login')).reduce((sum, i) => sum + i.count, 0);

        this._animateValue('statTotal', total);
        this._animateValue('statIPs', uniqueIPs);
        this._animateValue('statCountries', countries);
        this._animateValue('statFailed', failed);
    }

    _animateValue(elementId, targetValue) {
        const element = document.getElementById(elementId);
        const currentValue = parseInt(element.textContent) || 0;
        const duration = 500;
        const steps = 30;
        const increment = (targetValue - currentValue) / steps;
        let current = currentValue;
        let step = 0;

        const timer = setInterval(() => {
            step++;
            current += increment;
            element.textContent = Math.round(current).toLocaleString();
            if (step >= steps) {
                element.textContent = targetValue.toLocaleString();
                clearInterval(timer);
            }
        }, duration / steps);
    }

    updateTopAttackers(attackers) {
        const container = document.getElementById('topAttackers');
        if (attackers.length === 0) {
            container.innerHTML = '<p style="color: #8b92a9; text-align: center; padding: 20px;">No data available</p>';
            return;
        }
        container.innerHTML = attackers.slice(0, 10).map((attacker, index) => `
            <div class="attacker-item" onclick="window.focusOnAttacker('${attacker.ip}')">
                <div class="attacker-ip">#${index + 1} ${attacker.ip}</div>
                <div class="attacker-meta"><span class="attacker-count">${attacker.count} events</span> • ${attacker.country}</div>
            </div>
        `).join('');
    }

    showIncidentDetails(incident) {
        const drawer = this.incidentDrawer;
        const content = document.getElementById('drawerContent');
        content.innerHTML = `
            <div class="drawer-field"><div class="drawer-field-label">IP Address</div><div class="drawer-field-value">${incident.ip}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Total Events</div><div class="drawer-field-value" style="color: #ff4757;">${incident.count}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Location</div><div class="drawer-field-value">${incident.geo.city}, ${incident.geo.country}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Country Code</div><div class="drawer-field-value">${incident.geo.countryCode}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Organization</div><div class="drawer-field-value">${incident.geo.org || 'Unknown'}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">ISP</div><div class="drawer-field-value">${incident.geo.isp || 'Unknown'}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Event Types</div><div class="drawer-field-value">${incident.types.join(', ')}</div></div>
            <div class="drawer-field"><div class="drawer-field-label">Last Seen</div><div class="drawer-field-value">${this._formatTimestamp(incident.last_seen)}</div></div>
            <div class="drawer-field" style="grid-column: 1 / -1;"><div class="drawer-field-label">Recent Timestamps (Latest 5)</div><div class="timestamp-list">${incident.samples.map(ts => `<div>• ${this._formatTimestamp(ts)}</div>`).join('')}</div></div>
        `;
        drawer.classList.add('visible');
    }

    hideIncidentDetails() { this.incidentDrawer.classList.remove('visible'); }
    toggleSidebar() { this.sidebar.classList.toggle('collapsed'); }

    _formatTimestamp(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #ff4757; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); z-index: 3000; animation: slideIn 0.3s ease;';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        setTimeout(() => {
            errorDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => errorDiv.remove(), 300);
        }, 4000);
    }

    showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #2ed573; color: white; padding: 16px 24px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); z-index: 3000; animation: slideIn 0.3s ease;';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        setTimeout(() => {
            successDiv.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => successDiv.remove(), 300);
        }, 3000);
    }

    downloadJSON(data, filename = 'threatcanvas_data.json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        this._downloadBlob(blob, filename);
    }

    _downloadBlob(blob, filename) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn { from { transform: translateX(400px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
    @keyframes slideOut { from { transform: translateX(0); opacity: 1; } to { transform: translateX(400px); opacity: 0; } }
`;
document.head.appendChild(style);

window.UIController = UIController;
