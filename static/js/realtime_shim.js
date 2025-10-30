(function(){
  // very small counters shim (adjust selectors if needed)
  const getInt = (sel) => parseInt((document.querySelector(sel)?.textContent||'0').trim())||0;
  const setInt = (sel, v) => { const n=document.querySelector(sel); if(n) n.textContent=String(v); };

  window.updateCounters = window.updateCounters || function(status){
    setInt('#total-incidents', getInt('#total-incidents') + 1);
    if (status === 'failed_login') setInt('#failed-logins', getInt('#failed-logins') + 1);
    // Add more statuses if you want (accepted_login, invalid_user, etc.)
  };
})();
