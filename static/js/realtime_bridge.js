(function () {
  if (typeof io === 'undefined') { console.error('[realtime] socket.io client missing'); return; }
  const socket = io({ transports: ['websocket','polling'] });

  // Receive events emitted by Flask-SocketIO: socketio.emit('ssh_event', {...})
  socket.on('ssh_event', (payload) => {
    const ev = (typeof payload === 'string') ? JSON.parse(payload) : payload;

    // 1) counters (only if your app exposed it)
    if (typeof window.updateCounters === 'function') {
      try { window.updateCounters(ev.status); } catch(e){ console.warn('updateCounters failed', e); }
    }

    // 2) add a marker using your map instance
    //    Your ThreatMap expects: addIncidents([{ ip, status, geo, samples, count }])
    if (window.app && window.app.map && typeof window.app.map.addIncidents === 'function') {
      const incident = {
        ip: ev.ip,
        status: ev.status || 'unknown',
        geo: ev.geo || { lat: null, lon: null },   // your backend can attach geo later
        samples: [ev.timestamp || new Date().toISOString()],
        count: 1
      };
      try {
        window.app.map.addIncidents([incident]);
        if (typeof window.app.map.fitBounds === 'function') window.app.map.fitBounds();
      } catch(e){ console.warn('map addIncidents failed', e); }
    }
  });
})();
