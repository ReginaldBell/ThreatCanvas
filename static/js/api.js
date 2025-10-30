class ThreatCanvasAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    async fetchIncidents(filters = {}) {
        try {
            const params = new URLSearchParams();
            if (filters.since) params.append('since', filters.since);
            if (filters.types && filters.types.length > 0) {
                params.append('types', filters.types.join(','));
            }
            if (filters.search) params.append('q', filters.search);
            if (filters.limit) params.append('limit', filters.limit);

            const response = await fetch(`${this.baseURL}/api/incidents?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Unknown API error');
            }
            return data.data;
        } catch (error) {
            console.error('Failed to fetch incidents:', error);
            throw error;
        }
    }

    async fetchTopAttackers(limit = 10) {
        try {
            const response = await fetch(`${this.baseURL}/api/top?limit=${limit}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Failed to fetch top attackers:', error);
            throw error;
        }
    }

    async fetchStats() {
        try {
            const response = await fetch(`${this.baseURL}/api/stats`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            throw error;
        }
    }

    async fetchTimeline(since = '24h', interval = 'hour') {
        try {
            const response = await fetch(`${this.baseURL}/api/timeline?since=${since}&interval=${interval}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            return data.data;
        } catch (error) {
            console.error('Failed to fetch timeline:', error);
            throw error;
        }
    }

    getExportURL(format = 'csv', limit = 100) {
        return `${this.baseURL}/api/top?format=${format}&limit=${limit}`;
    }
}

window.ThreatCanvasAPI = ThreatCanvasAPI;
