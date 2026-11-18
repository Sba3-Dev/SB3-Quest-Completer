(() => {
  'use strict';
  const state = { games: [], queue: [], query: '', page: 0, pageSize: 12 };
  const $ = (id) => document.getElementById(id);
  const api = () => window.pywebview && window.pywebview.api ? window.pywebview.api : null;
  const text = (value, fallback = '') => String(value ?? fallback);
  function initials(name) { return text(name, 'SB').trim().split(/\s+/).map(x => x[0]).join('').slice(0,2).toUpperCase() || 'SB'; }
  function toast(message) { const el = $('toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 2400); }
  function renderGames() {
    const grid = $('game-grid');
    const query = state.query.trim().toLowerCase();
    const filtered = state.games.filter(g => `${g.name} ${g.id} ${g.platform || ''}`.toLowerCase().includes(query));
    const end = Math.min(filtered.length, (state.page + 1) * state.pageSize);
    grid.replaceChildren();
    if (!state.games.length) { for (let i=0;i<6;i++) { const s=document.createElement('div'); s.className='skeleton'; grid.append(s); } return; }
    if (!filtered.length) { const empty=document.createElement('div'); empty.className='empty-queue'; empty.textContent='No games match your search.'; grid.append(empty); return; }
    filtered.slice(0,end).forEach(game => {
      const card=document.createElement('article'); card.className='game-card';
      const icon=document.createElement('div'); icon.className='game-icon'; icon.textContent=initials(game.name);
      if (game.icon) { const img=document.createElement('img'); img.src=game.icon; img.alt=''; img.onerror=()=>img.remove(); icon.replaceChildren(img); }
      const title=document.createElement('h3'); title.textContent=text(game.name,'Game');
      const meta=document.createElement('p'); meta.textContent=text(game.platform,'Verified PC launcher');
      const button=document.createElement('button'); button.className='primary-button'; button.type='button'; button.textContent='Add';
      button.addEventListener('click', () => { const bridge=api(); if (bridge?.add_to_queue) bridge.add_to_queue(String(game.id)); addQueue(game); });
      card.append(icon,title,meta,button); grid.append(card);
    });
    $('library-count').textContent = `Showing ${end.toLocaleString()} of ${filtered.length.toLocaleString()}`;
    $('load-more').hidden = end >= filtered.length;
  }
  function addQueue(game) { if (state.queue.some(x => String(x.id) === String(game.id))) return toast('Already in queue'); state.queue.push(game); renderQueue(); toast(`Added: ${text(game.name,'Game')}`); }
  function renderQueue() {
    const list=$('queue-list'); list.replaceChildren(); $('queue-count').textContent=`${state.queue.length} selected`; $('stop-all').hidden=!state.queue.length;
    if (!state.queue.length) { const empty=document.createElement('div'); empty.className='empty-queue'; empty.textContent='Your queue is empty.'; list.append(empty); return; }
    state.queue.forEach(game => { const row=document.createElement('div'); row.className='queue-item'; const info=document.createElement('div'); info.className='queue-info'; const name=document.createElement('strong'); name.textContent=text(game.name,'Game'); const meta=document.createElement('span'); meta.textContent=game.running?'Running':'Ready'; info.append(name,meta); const run=document.createElement('button'); run.className=`queue-action${game.running?' stop':''}`; run.textContent=game.running?'Stop':'Run'; run.onclick=()=>{const bridge=api(); if(game.running){bridge?.stop_quest?.(String(game.id));game.running=false}else{bridge?.run_quest?.(String(game.id));game.running=true}renderQueue()}; const remove=document.createElement('button'); remove.className='remove-action'; remove.textContent='×'; remove.setAttribute('aria-label','Remove'); remove.onclick=()=>{const bridge=api();bridge?.remove_from_queue?.(String(game.id));state.queue=state.queue.filter(x=>String(x.id)!==String(game.id));renderQueue()}; row.append(info,run,remove); list.append(row); });
  }
  function setGames(games) { state.games=(Array.isArray(games)?games:[]).map(g=>({id:g.id,name:g.name||g._public_name,platform:g.platform||g._platforms?.[0],icon:g.icon||g.icon_url})); state.page=0; renderGames(); }
  function bootstrap(data) { if (!data) return; if (data.games) setGames(data.games); if (data.queue) {state.queue=data.queue;renderQueue();} if (data.version) $('version-text').textContent=`v${data.version}`; }
  $('search').addEventListener('input', e => { state.query=e.target.value; state.page=0; renderGames(); });
  $('search').addEventListener('keydown', e => { if ((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k') { e.preventDefault(); e.currentTarget.focus(); } });
  $('load-more').addEventListener('click', () => { state.page++; renderGames(); });
  $('stop-all').addEventListener('click', () => { api()?.stop_all?.(); state.queue.forEach(x=>x.running=false); renderQueue(); });
  window.sb3Web = { bootstrap, setGames, setQueue: q => {state.queue=q||[];renderQueue();}, notify: toast };
  renderGames(); renderQueue();
  window.addEventListener('pywebviewready', async () => { try { const bridge=api(); if (bridge?.bootstrap) bootstrap(await bridge.bootstrap()); } catch (e) { toast('Web interface is running in safe preview mode'); } });
})();
