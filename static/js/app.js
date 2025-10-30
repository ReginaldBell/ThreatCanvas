class ThreatCanvasApp {
    constructor() {
        this.api = new ThreatCanvasAPI();
        this.map = new ThreatMap('map');
        this.ui = new UIController();
        
        this.filters = {
            since: '24h',
            types: ['failed_login', 'accepted_login', 'invalid_user', 'break_in_attempt'],
            search: ''
        };

        this.autoRefreshInterval = null;
        this.autoRefreshEnabled = false;
        this.currentIncidents = [];
        
        // Socket.IO connection
        this.socket = null;
        this.realtimeEnabled = false;

        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupRealtimeConnection();
        await this.loadData();
    }

    setupRealtimeConnection() {
        try {
            // Connect to Socket.IO
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔴 Real-time connection established');
                this.realtimeEnabled = true;
                this.ui.showSuccess('Real-time streaming active');
            });

            this.socket.on('disconnect', () => {
                console.log('🔴 Real-time connection lost');
                this.realtimeEnabled = false;
            });

            // Listen for new SSH events
            this.socket.on('new_ssh_event', (event) => {
                console.log('🔵 New SSH event:', event);
                this.handleNewSSHEvent(event);
            });

        } catch (error) {
            console.error('Failed to setup real-time connection:', error);
        }
    }

    async handleNewSSHEvent(event) {
        // Show notification
        this.ui.showSuccess(`New ${event.type} from ${event.ip}`);
        
        // Optionally reload data to update map
        // await this.loadData();
    }

    setupEventListeners() {
        document.querySelectorAll('[data-time]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('[data-time]').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.filters.since = e.target.dataset.time;
                this.loadData();
            });
        });

        document.querySelectorAll('.checkbox-label input').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.filters.types = Array.from(
                    document.querySelectorAll('.checkbox-label input:checked')
                ).map(cb => cb.value);
                this.loadData();
            });
        });

        const searchInput = document.getElementById('searchInput');
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.filters.search = e.target.value.trim();
                this.loadData();
            }, 500);
        });

        document.getElementById('toggleAutoRefresh').addEventListener('click', () => {
            this.toggleAutoRefresh();
        });

        document.getElementById('refreshNow').addEventListener('click', () => {
            this.loadData();
        });

        document.getElementById('toggleClusters').addEventListener('click', (e) => {
            const enabled = this.map.toggleClustering();
            e.target.classList.toggle('active', enabled);
        });

        document.getElementById('toggleHeatmap').addEventListener('click', (e) => {
            const enabled = this.map.toggleHeatmap();
            e.target.classList.toggle('active', enabled);
        });

        document.getElementById('toggleSidebar').addEventListener('click', () => {
            this.ui.toggleSidebar();
        });

        document.getElementById('closeDrawer').addEventListener('click', () => {
            this.ui.hideIncidentDetails();
        });

        document.getElementById('exportCSV').addEventListener('click', () => {
            window.open(this.api.getExportURL('csv', 100), '_blank');
            this.ui.showSuccess('CSV export started');
        });

        document.getElementById('exportJSON').addEventListener('click', () => {
            this.ui.downloadJSON(this.currentIncidents, 'threatcanvas_incidents.json');
            this.ui.showSuccess('JSON downloaded');
        });

        document.getElementById('toggleClusters').classList.add('active');

        window.showIncidentDetails = (ip) => {
            const incident = this.currentIncidents.find(i => i.ip === ip);
            if (incident) {
                this.ui.showIncidentDetails(incident);
            }
        };

        window.focusOnAttacker = (ip) => {
            this.map.focusOnIP(ip);
            const incident = this.currentIncidents.find(i => i.ip === ip);
            if (incident) {
                this.ui.showIncidentDetails(incident);
            }
        };
    }

    async loadData() {
        this.ui.showLoading();

        try {
            const incidents = await this.api.fetchIncidents(this.filters);
            this.currentIncidents = incidents;

            this.map.updateIncidents(incidents, (incident) => {
                this.ui.showIncidentDetails(incident);
            });

            this.ui.updateStats(incidents);

            const topAttackers = await this.api.fetchTopAttackers(10);
            this.ui.updateTopAttackers(topAttackers);

            if (incidents.length > 0) {
                this.map.fitBounds();
            }

            this.ui.hideLoading();
        } catch (error) {
            this.ui.hideLoading();
            this.ui.showError(`Failed to load data: ${error.message}`);
            console.error('Load error:', error);
        }
    }

    toggleAutoRefresh() {
        this.autoRefreshEnabled = !this.autoRefreshEnabled;
        const btn = document.getElementById('toggleAutoRefresh');

        if (this.autoRefreshEnabled) {
            btn.textContent = 'ON';
            btn.classList.add('active');
            this.autoRefreshInterval = setInterval(() => {
                this.loadData();
            }, 30000);
            this.ui.showSuccess('Auto-refresh enabled (30s)');
        } else {
            btn.textContent = 'OFF';
            btn.classList.remove('active');
            if (this.autoRefreshInterval) {
                clearInterval(this.autoRefreshInterval);
                this.autoRefreshInterval = null;
            }
            this.ui.showSuccess('Auto-refresh disabled');
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new ThreatCanvasApp();
    });
} else {
    window.app = new ThreatCanvasApp();
}

/* == Realtime SSH hook (injected) == */
(function () {
  try {
    // reuse existing socket if the app already created it; otherwise create one
    var _socket = (window.socket && typeof window.socket.on === 'function')
      ? window.socket
      : io({ transports: ["websocket","polling"], reconnection: true });

    function isPrivate(ip){
      return ip === "127.0.0.1" ||
             ip.startsWith("10.") ||
             ip.startsWith("192.168.") ||
             /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(ip);
    }
    function parse(data){
      if (typeof data === "string") { try { return JSON.parse(data); } catch(e){ return null; } }
      return data;
    }

    _socket.on("ssh_event", function (payload) {
      var ev = parse(payload);
      if (!ev) return;

      // 1) update the counters (existing app function)
      if (typeof window.updateCounters === "function") {
        window.updateCounters(ev.status);
      }

      // 2) add a marker if public IP (existing app function)
      if (!isPrivate(ev.ip) && typeof window.addMarkerToMap === "function") {
        window.addMarkerToMap(ev.ip, ev.status, ev.geo || null);
      }

      // 3) optional: prepend to any live activity list if provided by the app
      if (typeof window.prependIncidentRow === "function") {
        window.prependIncidentRow(ev);
      }
    });

    console.info("Realtime hook ready: listening for ssh_event");
  } catch (e) {
    console.error("Realtime hook failed:", e);
  }
})();
