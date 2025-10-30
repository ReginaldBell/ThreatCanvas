class ThreatMap {
    constructor(containerId) {
        this.map = L.map(containerId, {
            center: [20, 0],
            zoom: 2,
            minZoom: 2,
            maxZoom: 18
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
            subdomains: 'abcd',
            maxZoom: 19
        }).addTo(this.map);

        this.markers = L.markerClusterGroup({
            maxClusterRadius: 80,
            spiderfyOnMaxZoom: true,
            showCoverageOnHover: false,
            zoomToBoundsOnClick: true,
            iconCreateFunction: (cluster) => {
                const count = cluster.getChildCount();
                let size = 'small';
                if (count > 100) size = 'large';
                else if (count > 20) size = 'medium';
                return L.divIcon({
                    html: `<div><span>${count}</span></div>`,
                    className: `marker-cluster marker-cluster-${size}`,
                    iconSize: L.point(40, 40)
                });
            }
        });

        this.heatLayer = null;
        this.incidents = [];
        this.clusteringEnabled = true;
        this.heatmapEnabled = false;
        this._setupClusterStyles();
    }

    _setupClusterStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .marker-cluster { background-color: rgba(0, 212, 255, 0.6); border: 3px solid #00d4ff; border-radius: 50%; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; }
            .marker-cluster-small { width: 30px !important; height: 30px !important; }
            .marker-cluster-medium { width: 40px !important; height: 40px !important; font-size: 16px; }
            .marker-cluster-large { width: 50px !important; height: 50px !important; font-size: 18px; background-color: rgba(255, 71, 87, 0.6); border-color: #ff4757; }
        `;
        document.head.appendChild(style);
    }

    updateIncidents(incidents, onMarkerClick) {
        this.incidents = incidents;
        this.markers.clearLayers();

        incidents.forEach(incident => {
            const { lat, lon } = incident.geo;
            if (!lat || !lon || (lat === 0 && lon === 0)) return;
            const marker = this._createMarker(incident, onMarkerClick);
            this.markers.addLayer(marker);
        });

        if (this.clusteringEnabled) {
            this.map.addLayer(this.markers);
        } else {
            this.markers.eachLayer(marker => marker.addTo(this.map));
        }

        if (this.heatmapEnabled) {
            this._updateHeatmap();
        }
    }

    _createMarker(incident, onClick) {
        const { lat, lon, country, city } = incident.geo;
        const severity = this._getSeverityColor(incident);

        const icon = L.divIcon({
            className: 'custom-marker',
            html: `<div style="background-color: ${severity}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${severity};"></div>`,
            iconSize: [12, 12]
        });

        const marker = L.marker([lat, lon], { icon });

        const popupContent = `
            <div style="color: #0a0e27; min-width: 200px;">
                <h3 style="margin: 0 0 8px 0; font-size: 16px;">${incident.ip}</h3>
                <p style="margin: 4px 0;"><strong>Location:</strong> ${city}, ${country}</p>
                <p style="margin: 4px 0;"><strong>Events:</strong> ${incident.count}</p>
                <p style="margin: 4px 0;"><strong>Types:</strong> ${incident.types.join(', ')}</p>
                <button onclick="window.showIncidentDetails('${incident.ip}')" style="margin-top: 8px; padding: 6px 12px; background: #00d4ff; border: none; border-radius: 4px; cursor: pointer; color: white;">View Details</button>
            </div>
        `;

        marker.bindPopup(popupContent);
        marker.on('click', () => {
            if (onClick) onClick(incident);
        });

        return marker;
    }

    _getSeverityColor(incident) {
        const count = incident.count;
        const hasFailed = incident.types.includes('failed_login');
        const hasBreakIn = incident.types.includes('break_in_attempt');

        if (hasBreakIn || count > 50) return '#ff4757';
        if (hasFailed && count > 20) return '#ffa502';
        if (hasFailed) return '#ffd32a';
        return '#2ed573';
    }

    _updateHeatmap() {
        if (this.heatLayer) {
            this.map.removeLayer(this.heatLayer);
        }

        const heatData = this.incidents
            .filter(i => i.geo.lat && i.geo.lon)
            .map(i => [i.geo.lat, i.geo.lon, Math.min(i.count / 10, 1)]);

        this.heatLayer = L.heatLayer(heatData, {
            radius: 25,
            blur: 35,
            maxZoom: 10,
            max: 1.0,
            gradient: { 0.0: '#2ed573', 0.3: '#ffd32a', 0.6: '#ffa502', 1.0: '#ff4757' }
        });

        if (this.heatmapEnabled) {
            this.heatLayer.addTo(this.map);
        }
    }

    toggleClustering() {
        this.clusteringEnabled = !this.clusteringEnabled;
        if (this.clusteringEnabled) {
            this.markers.eachLayer(marker => {
                if (this.map.hasLayer(marker)) {
                    this.map.removeLayer(marker);
                }
            });
            this.map.addLayer(this.markers);
        } else {
            this.map.removeLayer(this.markers);
            this.markers.eachLayer(marker => marker.addTo(this.map));
        }
        return this.clusteringEnabled;
    }

    toggleHeatmap() {
        this.heatmapEnabled = !this.heatmapEnabled;
        if (this.heatmapEnabled) {
            this._updateHeatmap();
        } else if (this.heatLayer) {
            this.map.removeLayer(this.heatLayer);
        }
        return this.heatmapEnabled;
    }

    fitBounds() {
        if (this.incidents.length === 0) return;
        const bounds = L.latLngBounds(this.incidents.filter(i => i.geo.lat && i.geo.lon).map(i => [i.geo.lat, i.geo.lon]));
        if (bounds.isValid()) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    focusOnIP(ip) {
        const incident = this.incidents.find(i => i.ip === ip);
        if (!incident || !incident.geo.lat || !incident.geo.lon) return;
        this.map.setView([incident.geo.lat, incident.geo.lon], 8);
        this.markers.eachLayer(marker => {
            const latlng = marker.getLatLng();
            if (Math.abs(latlng.lat - incident.geo.lat) < 0.01 && Math.abs(latlng.lng - incident.geo.lon) < 0.01) {
                marker.openPopup();
            }
        });
    }
}

window.ThreatMap = ThreatMap;
