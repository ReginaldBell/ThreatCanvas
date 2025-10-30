// static/js/realtime.js
const socket = io({
  transports: ["websocket", "polling"],
  reconnection: true,
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  timeout: 20000,
});

function parseEvent(data){ try{ return (typeof data==="string")?JSON.parse(data):data; }catch{ return null; } }
function isPrivateIp(ip){
  return ip==="127.0.0.1" || ip.startsWith("10.") || ip.startsWith("192.168.") || /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(ip);
}

socket.on("connect", ()=>console.info("Real-time connection established"));
socket.on("disconnect", r=>console.warn("Real-time disconnected:", r));
socket.on("connect_error", e=>console.error("Real-time connect_error:", e?.message||e));

socket.on("ssh_event",(payload)=>{
  const ev = parseEvent(payload);
  if(!ev) return;

  if (typeof updateCounters === "function") updateCounters(ev.status);
  if (!isPrivateIp(ev.ip) && typeof addMarkerToMap === "function") addMarkerToMap(ev.ip, ev.status, ev.geo || null);
  if (typeof prependIncidentRow === "function") prependIncidentRow(ev);
});
