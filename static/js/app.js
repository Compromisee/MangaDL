(function(){
'use strict';

/* ======== STATE ======== */
let manga=null, chapters=[], volumes={}, results=[], socket=null;
let listView=false, activeTab='chapters', currentLang='en';
let history=JSON.parse(localStorage.getItem('mdl_history')||'[]');
let cart=JSON.parse(localStorage.getItem('mdl_cart')||'[]');
let completedTasks=new Set();

const $=s=>document.querySelector(s);
const $$=s=>[...document.querySelectorAll(s)];
const esc=t=>{const d=document.createElement('div');d.textContent=t||'';return d.innerHTML};
const escA=t=>(t||'').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const fmtB=b=>{if(!b)return'0 B';const k=1024,u=['B','KB','MB','GB'];const i=Math.floor(Math.log(b)/Math.log(k));return(b/Math.pow(k,i)).toFixed(1)+' '+u[i]};

/* ======== THEME ======== */
const THEMES = ['dark','light','midnight','forest','rose','amber','ocean','hc-dark','hc-light'];
let currentTheme = localStorage.getItem('mdl_theme') || 'dark';

function applyTheme(name){
  if(!THEMES.includes(name)) name = 'dark';
  currentTheme = name;
  document.documentElement.setAttribute('data-theme', name);
  localStorage.setItem('mdl_theme', name);
  $$('.theme-option').forEach(b => b.classList.toggle('active', b.dataset.theme === name));
}

function initTheme(){
  applyTheme(currentTheme);

  const btn = $('#themeBtn');
  const dd = $('#themeDropdown');

  if(btn && dd){
    btn.addEventListener('click', e => {
      e.stopPropagation();
      dd.classList.toggle('open');
    });
    document.addEventListener('click', e => {
      if(!e.target.closest('#themePicker')) dd.classList.remove('open');
    });
    $$('.theme-option').forEach(b => {
      b.addEventListener('click', () => {
        applyTheme(b.dataset.theme);
        const name = b.querySelector('.theme-name')?.textContent || b.dataset.theme;
        toast(`Theme: ${name}`, 'success');
        setTimeout(() => dd.classList.remove('open'), 200);
      });
    });
  }

  // Accessibility prefs
  const reducedMotion = localStorage.getItem('mdl_reduced_motion') === '1';
  const largerText = localStorage.getItem('mdl_larger_text') === '1';
  if(reducedMotion) document.body.classList.add('no-motion');
  if(largerText) document.body.classList.add('larger-text');
}

function applyAccessibility(reduceMotion, largerText){
  document.body.classList.toggle('no-motion', !!reduceMotion);
  document.body.classList.toggle('larger-text', !!largerText);
  localStorage.setItem('mdl_reduced_motion', reduceMotion ? '1' : '0');
  localStorage.setItem('mdl_larger_text', largerText ? '1' : '0');
}

/* ======== CONFETTI ======== */
const confettiCanvas = $('#confettiCanvas');
const confCtx = confettiCanvas ? confettiCanvas.getContext('2d') : null;
let confettiPieces = [];
let confettiRunning = false;

function resizeConfetti(){
  if(!confettiCanvas) return;
  confettiCanvas.width = window.innerWidth;
  confettiCanvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeConfetti);
resizeConfetti();

function fireConfetti(){
  if(!confCtx) return;
  // Respect reduced motion
  if(document.body.classList.contains('no-motion')) return;

  const colors = ['#3b82f6','#22c55e','#eab308','#ef4444','#a855f7','#06b6d4','#f97316','#ec4899'];
  for(let i=0; i<120; i++){
    confettiPieces.push({
      x: window.innerWidth/2 + (Math.random()-.5)*200,
      y: window.innerHeight/2,
      vx: (Math.random()-.5)*18,
      vy: -(Math.random()*16+6),
      w: Math.random()*8+4,
      h: Math.random()*6+3,
      color: colors[Math.floor(Math.random()*colors.length)],
      rot: Math.random()*360,
      rotV: (Math.random()-.5)*12,
      gravity: .35,
      opacity: 1,
      decay: Math.random()*.015+.003,
    });
  }
  if(!confettiRunning){
    confettiRunning = true;
    animateConfetti();
  }
}

function animateConfetti(){
  confCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
  confettiPieces = confettiPieces.filter(p => {
    p.x += p.vx;
    p.y += p.vy;
    p.vy += p.gravity;
    p.rot += p.rotV;
    p.opacity -= p.decay;
    p.vx *= .99;
    if(p.opacity <= 0) return false;
    confCtx.save();
    confCtx.translate(p.x, p.y);
    confCtx.rotate(p.rot * Math.PI / 180);
    confCtx.globalAlpha = p.opacity;
    confCtx.fillStyle = p.color;
    confCtx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
    confCtx.restore();
    return true;
  });
  if(confettiPieces.length){
    requestAnimationFrame(animateConfetti);
  } else {
    confCtx.clearRect(0, 0, confettiCanvas.width, confettiCanvas.height);
    confettiRunning = false;
  }
}

/* ======== SPLASH ======== */
function initSplash(){
  setTimeout(() => {
    const s = $('#splash');
    if(!s) return;
    s.classList.add('out');
    setTimeout(() => {
      s.style.display = 'none';
      $('#app')?.classList.remove('hidden');
    }, 600);
  }, 2200);
}

/* ======== SOCKET ======== */
function initSocket(){
  if(typeof io === 'undefined'){
    console.warn('Socket.IO not loaded');
    return;
  }
  socket = io();
  socket.on('connect', () => console.log('Socket connected'));
  socket.on('disconnect', () => console.log('Socket disconnected'));
  socket.on('download_progress', d => {
    updateDl(d);
    if(d.status === 'completed' && !completedTasks.has(d.task_id)){
      completedTasks.add(d.task_id);
      fireConfetti();
      toast('Download completed: ' + (d.title || 'manga'), 'success');
    }
  });
}

/* ======== NAV ======== */
function initNav(){
  $$('.nav-link').forEach(l => l.addEventListener('click', e => {
    e.preventDefault();
    go(l.dataset.view);
  }));
  $$('[data-goto]').forEach(el => el.addEventListener('click', () => go(el.dataset.goto)));

  const tog = $('#sidebarToggle');
  if(tog) tog.addEventListener('click', () => $('#sidebar')?.classList.toggle('open'));

  document.addEventListener('click', e => {
    if(!e.target.closest('.sidebar') && !e.target.closest('#sidebarToggle')){
      $('#sidebar')?.classList.remove('open');
    }
  });
}

function go(v){
  $$('.nav-link').forEach(n => n.classList.toggle('active', n.dataset.view === v));
  $$('.view').forEach(el => el.classList.remove('active'));
  const target = $(`#view-${v}`);
  if(target){
    target.classList.add('active');
    target.scrollTop = 0;
  }
  const icons = {
    home:'home', search:'search', url:'link', cart:'shopping_cart',
    queue:'queue', downloads:'downloading', library:'folder_open',
    history:'history', settings:'tune', about:'info'
  };
  const names = {
    home:'Home', search:'Search', url:'URL Import', cart:'Cart',
    queue:'Queue', downloads:'Downloads', library:'Library',
    history:'History', settings:'Settings', about:'About'
  };
  const bc = $('#breadcrumb');
  if(bc){
    bc.innerHTML = `<span class="material-icons-outlined">${icons[v]||'home'}</span><span>${names[v]||v}</span>`;
  }

  if(v === 'downloads') refreshDl();
  if(v === 'library') refreshLib();
  if(v === 'history') renderHistory();
  if(v === 'cart') renderCart();
  if(v === 'queue') renderQueue();
  if(v === 'settings') loadSettings();
  $('#sidebar')?.classList.remove('open');
}

/* ======== SEARCH ======== */
function initSearch(){
  $('#searchBtn')?.addEventListener('click', doSearch);
  $('#searchInput')?.addEventListener('keydown', e => {
    if(e.key === 'Enter') doSearch();
  });
  $('#gridBtn')?.addEventListener('click', () => {
    listView = false;
    $('#gridBtn').classList.add('active');
    $('#listBtn').classList.remove('active');
    $('#searchResults').classList.remove('list-view');
  });
  $('#listBtn')?.addEventListener('click', () => {
    listView = true;
    $('#listBtn').classList.add('active');
    $('#gridBtn').classList.remove('active');
    $('#searchResults').classList.add('list-view');
  });
}

function doSearch(){
  const q = $('#searchInput').value.trim();
  if(!q) return;
  show('searchSpinner');
  $('#searchResults').innerHTML = '';
  $('#searchMeta').style.display = 'none';
  fetch('/api/search', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({query: q, source: $('#searchSource').value})
  })
  .then(r => r.json())
  .then(d => {
    hide('searchSpinner');
    if(d.error){ toast(d.error, 'error'); return; }
    results = d.results || [];
    renderResults(results);
  })
  .catch(() => { hide('searchSpinner'); toast('Search failed', 'error'); });
}

function renderResults(res){
  const c = $('#searchResults');
  c.innerHTML = '';
  if(!res.length){
    c.innerHTML = '<div class="empty" style="grid-column:1/-1"><span class="material-icons-outlined">search_off</span><p>No results</p></div>';
    return;
  }
  $('#searchMeta').style.display = 'flex';
  $('#resultCountLabel').textContent = `${res.length} result${res.length !== 1 ? 's' : ''}`;
  res.forEach((m, idx) => {
    const d = document.createElement('div');
    d.className = 'manga-card';
    d.style.animationDelay = `${idx * 30}ms`;
    d.innerHTML = `<div class="mc-img"><div class="mc-placeholder"><span class="material-icons-outlined">image</span></div><img src="" alt="" loading="lazy"></div><div class="mc-info"><div class="mc-title">${esc(m.title)}</div><div class="mc-author">${esc(m.author||'Unknown')}</div></div>`;

    // Add source badge
    const badge = document.createElement('span');
    badge.className = 'mc-badge';
    badge.textContent = m.source || '';
    d.querySelector('.mc-img').appendChild(badge);

    // Lazy-load cover
    const img = d.querySelector('.mc-img img');
    if(m.cover_url){
      const loader = new Image();
      loader.onload = () => { img.src = m.cover_url; img.classList.add('loaded'); };
      loader.onerror = () => { img.style.display = 'none'; };
      loader.src = m.cover_url;
    } else {
      img.style.display = 'none';
    }
    d.addEventListener('click', () => openModal(m));
    c.appendChild(d);
  });
  if(listView) c.classList.add('list-view');
}

/* ======== URL ======== */
function initUrl(){
  $('#urlBtn')?.addEventListener('click', doUrl);
  $('#urlInput')?.addEventListener('keydown', e => {
    if(e.key === 'Enter') doUrl();
  });
}

function doUrl(){
  const u = $('#urlInput').value.trim();
  if(!u) return;
  show('urlSpinner');
  fetch('/api/manga_info', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url: u})
  })
  .then(r => r.json())
  .then(d => {
    hide('urlSpinner');
    if(d.error){ toast(d.error, 'error'); return; }
    openModal(d, true);
  })
  .catch(() => { hide('urlSpinner'); toast('Fetch failed', 'error'); });
}

/* ======== MODAL ======== */
function openModal(m, hasCh = false){
  manga = m;
  currentLang = m.current_language || 'en';
  const o = $('#mangaModal');
  o.classList.add('open');
  $('#mTitle').textContent = m.title;

  // Cover
  const coverImg = $('#mCover');
  if(coverImg){
    coverImg.classList.remove('loaded');
    coverImg.src = '';
    if(m.cover_url){
      const loader = new Image();
      loader.onload = () => { coverImg.src = m.cover_url; coverImg.classList.add('loaded'); };
      loader.onerror = () => {};
      loader.src = m.cover_url;
    }
  }

  $('#mAuthor').textContent = m.author || 'Unknown';
  $('#mStatus').textContent = m.status || 'Unknown';
  $('#mSource').textContent = m.source || 'Unknown';
  $('#mDesc').textContent = m.description || '';

  const g = $('#mGenres');
  g.innerHTML = '';
  (m.genres || []).forEach(x => {
    const t = document.createElement('span');
    t.className = 'tag';
    t.textContent = x;
    g.appendChild(t);
  });

  $('#mFormat').value = $('#sFormat').value || 'cbz';
  $('#mMode').value = $('#sMode').value || 'chapter';
  handleMode();

  activeTab = 'chapters';
  $$('.m-tab').forEach(t => t.classList.toggle('active', t.dataset.tab === 'chapters'));
  $('#mChaptersWrap').style.display = '';
  $('#mVolumesWrap').style.display = 'none';

  buildLangs(m.available_languages || [{code:'en', name:'English'}]);

  if(hasCh && m.chapters && m.chapters.length){
    chapters = m.chapters;
    volumes = buildVols(chapters);
    updateCounts();
    renderCh();
    renderVol();
  } else {
    show('mLoader');
    fetchInfo(m, currentLang);
  }
  addHistory(m);
}

function fetchInfo(m, lang){
  fetch('/api/manga_info', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url: m.url, source_key: m.source_key, language: lang})
  })
  .then(r => r.json())
  .then(d => {
    hide('mLoader');
    if(d.error){ toast(d.error, 'error'); return; }
    manga = d;
    chapters = d.chapters || [];
    volumes = buildVols(chapters);
    currentLang = d.current_language || lang;

    $('#mTitle').textContent = d.title;
    $('#mAuthor').textContent = d.author || 'Unknown';
    $('#mStatus').textContent = d.status || 'Unknown';
    $('#mDesc').textContent = d.description || '';

    if(d.cover_url){
      const ci = $('#mCover');
      const l = new Image();
      l.onload = () => { ci.src = d.cover_url; ci.classList.add('loaded'); };
      l.src = d.cover_url;
    }

    const g = $('#mGenres');
    g.innerHTML = '';
    (d.genres || []).forEach(x => {
      const t = document.createElement('span');
      t.className = 'tag';
      t.textContent = x;
      g.appendChild(t);
    });

    buildLangs(d.available_languages || []);
    updateCounts();
    renderCh();
    renderVol();
  })
  .catch(() => { hide('mLoader'); toast('Failed to load', 'error'); });
}

function buildLangs(langs){
  const s = $('#mLang');
  if(!s) return;
  s.innerHTML = '';
  const list = langs.map(l => typeof l === 'string' ? {code: l, name: l.toUpperCase()} : l);
  if(!list.length) list.push({code:'en', name:'English'});
  list.forEach(l => {
    const o = document.createElement('option');
    o.value = l.code;
    o.textContent = `${l.name} (${l.code})`;
    if(l.code === currentLang) o.selected = true;
    s.appendChild(o);
  });
  $('#mLangRow').style.display = list.length > 1 ? '' : 'none';
}

function buildVols(chs){
  const v = {};
  chs.forEach((c, i) => {
    const k = c.volume || 'No Volume';
    if(!v[k]) v[k] = [];
    v[k].push(i);
  });
  return v;
}

function updateCounts(){
  $('#mChCount').textContent = `${chapters.length} chapters`;
  const vc = Object.keys(volumes).filter(k => k !== 'No Volume').length;
  const un = (volumes['No Volume'] || []).length;
  let vt = `${vc} volume${vc !== 1 ? 's' : ''}`;
  if(un) vt += ` (+${un})`;
  $('#mVolCount').textContent = vt;
  $('#mChListCount').textContent = `${chapters.length} chapters`;
  $('#mVolListCount').textContent = `${Object.keys(volumes).length} groups`;
}

function renderCh(){
  const c = $('#mChList');
  c.innerHTML = '';
  if(!chapters.length){
    c.innerHTML = '<div class="empty"><p>No chapters</p></div>';
    return;
  }
  chapters.forEach((ch, i) => {
    const d = document.createElement('div');
    d.className = 'm-ch';
    d.dataset.index = i;
    d.innerHTML = `<input type="checkbox" checked data-index="${i}" data-type="ch"><span class="m-ch-num">Ch. ${esc(ch.number)}</span><span class="m-ch-title">${esc(ch.title)}</span>${ch.volume ? `<span class="m-ch-vol">V.${esc(ch.volume)}</span>` : ''}`;
    d.addEventListener('click', e => {
      if(e.target.tagName !== 'INPUT'){
        d.querySelector('input').checked = !d.querySelector('input').checked;
      }
      syncVolFromCh();
    });
    d.querySelector('input').addEventListener('change', () => syncVolFromCh());
    c.appendChild(d);
  });
  if(chapters.length){
    $('#mChFrom').placeholder = chapters[0].number;
    $('#mChTo').placeholder = chapters[chapters.length - 1].number;
  }
}

function renderVol(){
  const c = $('#mVolList');
  c.innerHTML = '';
  const keys = Object.keys(volumes).sort((a, b) => {
    if(a === 'No Volume') return 1;
    if(b === 'No Volume') return -1;
    return (parseFloat(a) || 0) - (parseFloat(b) || 0);
  });
  if(!keys.length){
    c.innerHTML = '<div class="empty"><p>No volumes</p></div>';
    return;
  }
  const nk = keys.filter(k => k !== 'No Volume');
  if(nk.length){
    $('#mVolFrom').placeholder = nk[0];
    $('#mVolTo').placeholder = nk[nk.length - 1];
  }
  keys.forEach(vn => {
    const idxs = volumes[vn];
    const dn = vn === 'No Volume' ? 'Unassigned' : `Volume ${vn}`;
    const g = document.createElement('div');
    g.className = 'vol-group';
    g.dataset.volume = vn;
    g.innerHTML = `<div class="vol-head"><input type="checkbox" checked data-volume="${escA(vn)}" data-type="vol"><span class="vol-label">${esc(dn)}</span><span class="vol-count">${idxs.length} ch.</span><span class="material-icons-outlined vol-arrow">expand_more</span></div><div class="vol-children"></div>`;
    const cc = g.querySelector('.vol-children');
    idxs.forEach(idx => {
      const ch = chapters[idx];
      const d = document.createElement('div');
      d.className = 'm-ch';
      d.innerHTML = `<input type="checkbox" checked data-index="${idx}" data-vc="${escA(vn)}" data-type="vch"><span class="m-ch-num">Ch. ${esc(ch.number)}</span><span class="m-ch-title">${esc(ch.title)}</span>`;
      d.addEventListener('click', e => {
        if(e.target.tagName !== 'INPUT'){
          d.querySelector('input').checked = !d.querySelector('input').checked;
        }
        updVolCb(vn);
        syncChFromVol();
      });
      d.querySelector('input').addEventListener('change', () => {
        updVolCb(vn);
        syncChFromVol();
      });
      cc.appendChild(d);
    });
    const hd = g.querySelector('.vol-head');
    hd.addEventListener('click', e => {
      if(e.target.tagName === 'INPUT') return;
      g.querySelector('.vol-arrow').classList.toggle('open');
      cc.classList.toggle('open');
    });
    const vcb = hd.querySelector('input');
    vcb.addEventListener('change', () => {
      cc.querySelectorAll('input').forEach(x => x.checked = vcb.checked);
      syncChFromVol();
    });
    c.appendChild(g);
  });
}

function syncVolFromCh(){
  const s = new Set();
  $$('#mChList input[data-type="ch"]').forEach(cb => {
    if(cb.checked) s.add(+cb.dataset.index);
  });
  $$('#mVolList input[data-type="vch"]').forEach(cb => {
    cb.checked = s.has(+cb.dataset.index);
  });
  Object.keys(volumes).forEach(v => updVolCb(v));
}

function syncChFromVol(){
  const s = new Set();
  $$('#mVolList input[data-type="vch"]').forEach(cb => {
    if(cb.checked) s.add(+cb.dataset.index);
  });
  $$('#mChList input[data-type="ch"]').forEach(cb => {
    cb.checked = s.has(+cb.dataset.index);
  });
}

function updVolCb(v){
  const g = $(`.vol-group[data-volume="${v}"]`);
  if(!g) return;
  const cbs = [...g.querySelectorAll('.vol-children input')];
  const vcb = g.querySelector('.vol-head input');
  if(!vcb || !cbs.length) return;
  const all = cbs.every(c => c.checked);
  const some = cbs.some(c => c.checked);
  vcb.checked = all;
  vcb.indeterminate = some && !all;
}

function getSelected(){
  return $$('#mChList input[data-type="ch"]')
    .filter(c => c.checked)
    .map(c => +c.dataset.index);
}

function initModal(){
  $('#mClose')?.addEventListener('click', closeModal);
  $('#mangaModal')?.addEventListener('click', e => {
    if(e.target === e.currentTarget) closeModal();
  });

  $$('.m-tab').forEach(t => t.addEventListener('click', () => {
    activeTab = t.dataset.tab;
    $$('.m-tab').forEach(x => x.classList.toggle('active', x.dataset.tab === activeTab));
    $('#mChaptersWrap').style.display = activeTab === 'chapters' ? '' : 'none';
    $('#mVolumesWrap').style.display = activeTab === 'volumes' ? '' : 'none';
  }));

  $('#mMode')?.addEventListener('change', handleMode);

  $('#mLang')?.addEventListener('change', () => {
    const nl = $('#mLang').value;
    if(nl === currentLang) return;
    currentLang = nl;
    show('mLoader');
    fetchInfo(manga, currentLang);
  });

  $('#mSelAll')?.addEventListener('click', () => setAll(true));
  $('#mSelNone')?.addEventListener('click', () => setAll(false));
  $('#mSelInv')?.addEventListener('click', () => {
    $$('#mChList input[data-type="ch"]').forEach(c => c.checked = !c.checked);
    syncVolFromCh();
  });

  $('#mChFilter')?.addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    $$('#mChList .m-ch').forEach(x => {
      x.style.display = x.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  $('#mVolFilter')?.addEventListener('input', e => {
    const q = e.target.value.toLowerCase();
    $$('#mVolList .vol-group').forEach(x => {
      x.style.display = x.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });

  const applyChR = () => {
    const f = parseFloat($('#mChFrom').value) || -Infinity;
    const t = parseFloat($('#mChTo').value) || Infinity;
    $$('#mChList input[data-type="ch"]').forEach(cb => {
      const n = parseFloat(chapters[+cb.dataset.index].number) || 0;
      cb.checked = n >= f && n <= t;
    });
    syncVolFromCh();
  };
  $('#mChFrom')?.addEventListener('change', applyChR);
  $('#mChTo')?.addEventListener('change', applyChR);

  const applyVR = () => {
    const f = parseFloat($('#mVolFrom').value) || -Infinity;
    const t = parseFloat($('#mVolTo').value) || Infinity;
    $$('#mVolList .vol-group').forEach(g => {
      const v = g.dataset.volume;
      const ir = v !== 'No Volume' && (parseFloat(v) || 0) >= f && (parseFloat(v) || 0) <= t;
      g.querySelector('.vol-head input').checked = ir;
      g.querySelectorAll('.vol-children input').forEach(c => c.checked = ir);
    });
    syncChFromVol();
  };
  $('#mVolFrom')?.addEventListener('change', applyVR);
  $('#mVolTo')?.addEventListener('change', applyVR);

  $('#mDownloadBtn')?.addEventListener('click', startDl);
  $('#mAddCart')?.addEventListener('click', addToCart);
}

function handleMode(){
  const m = $('#mMode').value;
  $('#mChRangeRow').style.display = m === 'volume' ? 'none' : '';
  $('#mVolRangeRow').style.display = m === 'volume' ? '' : 'none';
  if(m === 'volume'){
    $$('.m-tab').forEach(t => {
      if(t.dataset.tab === 'volumes') t.click();
    });
  }
}

function setAll(v){
  $$('#mChList input').forEach(c => c.checked = v);
  $$('#mVolList input').forEach(c => {
    c.checked = v;
    c.indeterminate = false;
  });
}

function closeModal(){
  $('#mangaModal').classList.remove('open');
  manga = null;
  chapters = [];
  volumes = {};
  $('#mChList').innerHTML = '';
  $('#mVolList').innerHTML = '';
  $('#mChFilter').value = '';
  $('#mVolFilter').value = '';
  $('#mChFrom').value = '';
  $('#mChTo').value = '';
  $('#mVolFrom').value = '';
  $('#mVolTo').value = '';
}

/* ======== CART ======== */
function addToCart(){
  if(!manga || !chapters.length) return;
  const sel = getSelected();
  if(!sel.length){ toast('No chapters selected', 'error'); return; }

  const existing = cart.findIndex(c => c.manga.url === manga.url);
  const item = {
    manga: {...manga},
    chapter_indices: sel,
    format: $('#mFormat').value,
    mode: $('#mMode').value,
    addedAt: Date.now(),
  };
  if(existing >= 0) cart[existing] = item;
  else cart.push(item);

  saveCart();
  toast(`Added to cart: ${manga.title} (${sel.length} ch.)`, 'success');
  updCartBadge();
}

function saveCart(){
  localStorage.setItem('mdl_cart', JSON.stringify(cart));
}

function renderCart(){
  const c = $('#cartList');
  if(!cart.length){
    c.innerHTML = '<div class="empty"><span class="material-icons-outlined">shopping_cart</span><p>Cart is empty. Search for manga and add them here.</p></div>';
    return;
  }
  c.innerHTML = '';
  cart.forEach((item, idx) => {
    const d = document.createElement('div');
    d.className = 'cart-item';
    d.innerHTML = `<img src="${esc(item.manga.cover_url || '')}" alt="" onerror="this.style.visibility='hidden'"><div class="cart-item-info"><div class="cart-item-title">${esc(item.manga.title)}</div><div class="cart-item-sub">${esc(item.manga.source || '')} &middot; ${item.format} / ${item.mode}</div></div><span class="cart-item-chapters">${item.chapter_indices.length} ch.</span><button class="cart-item-remove" data-idx="${idx}"><span class="material-icons-outlined">close</span></button>`;
    d.querySelector('.cart-item-remove').addEventListener('click', e => {
      e.stopPropagation();
      cart.splice(idx, 1);
      saveCart();
      renderCart();
      updCartBadge();
    });
    c.appendChild(d);
  });
}

function downloadCart(){
  if(!cart.length){ toast('Cart is empty', 'error'); return; }
  const fmt = $('#cartFormat').value;
  const mode = $('#cartMode').value;

  cart.forEach(item => {
    const payload = {
      manga: item.manga,
      chapter_indices: item.chapter_indices,
      format: item.format || fmt,
      mode: item.mode || mode,
    };
    fetch('/api/download', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    })
    .then(r => r.json())
    .catch(() => {});
  });

  setTimeout(() => {
    toast(`Started ${cart.length} download(s)`, 'success');
    cart = [];
    saveCart();
    renderCart();
    updCartBadge();
    go('downloads');
  }, 500);
}

function updCartBadge(){
  const n = cart.length;
  const b = $('#cartBadge');
  const p = $('#cartPill');
  if(n > 0){
    if(b){ b.style.display = ''; b.textContent = n; }
    if(p){ p.style.display = 'flex'; $('#cartPillCount').textContent = n; }
  } else {
    if(b) b.style.display = 'none';
    if(p) p.style.display = 'none';
  }
}

function initCart(){
  $('#clearCartBtn')?.addEventListener('click', () => {
    cart = [];
    saveCart();
    renderCart();
    updCartBadge();
  });
  $('#downloadCartBtn')?.addEventListener('click', downloadCart);
  $('#cartPill')?.addEventListener('click', () => go('cart'));
  updCartBadge();
}

/* ======== DOWNLOAD ======== */
function startDl(){
  if(!manga || !chapters.length) return;
  const sel = getSelected();
  if(!sel.length){ toast('No chapters selected', 'error'); return; }
  fetch('/api/download', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      manga,
      chapter_indices: sel,
      format: $('#mFormat').value,
      mode: $('#mMode').value,
    })
  })
  .then(r => r.json())
  .then(d => {
    if(d.error){ toast(d.error, 'error'); return; }
    toast(`Download started: ${sel.length} ch.`, 'success');
    closeModal();
    go('downloads');
    updBadge();
  })
  .catch(() => toast('Failed', 'error'));
}

/* ======== DOWNLOADS ======== */
function refreshDl(){
  fetch('/api/tasks').then(r => r.json()).then(d => renderDl(d.tasks || []));
}

function renderDl(tasks){
  const c = $('#dlList');
  if(!tasks.length){
    c.innerHTML = '<div class="empty"><span class="material-icons-outlined">cloud_download</span><p>No downloads yet</p></div>';
    return;
  }
  c.innerHTML = '';
  tasks.reverse().forEach(t => c.appendChild(mkDl(t)));
}

function mkDl(t){
  const d = document.createElement('div');
  d.className = 'dl-item';
  d.id = `dl-${t.task_id}`;
  d.innerHTML = dlHTML(t);
  return d;
}

function dlHTML(t){
  const pc = t.status === 'completed' ? 'done' : t.status === 'error' ? 'err' : '';
  const sp = t.speed ? fmtB(t.speed) + '/s' : '';
  const si = {
    queued: 'hourglass_empty', running: 'downloading',
    completed: 'check_circle', error: 'error', cancelled: 'cancel'
  }[t.status] || 'help';
  return `<div class="dl-top"><span class="dl-title">${esc(t.title || '')}</span>${t.status === 'running' ? `<button class="btn btn-ghost btn-sm" onclick="cancelDl('${t.task_id}')"><span class="material-icons-outlined">stop</span></button>` : ''}</div><div class="dl-info"><span class="dl-status s-${t.status}"><span class="material-icons-outlined">${si}</span>${t.status}</span><span>${t.current_chapter || ''}</span><span>${t.completed_chapters || 0}/${t.total_chapters || 0} ch.</span>${sp ? `<span>${sp}</span>` : ''}<span>${t.format || ''} / ${t.mode || ''}</span></div><div class="dl-bar"><div class="dl-fill ${pc}" style="width:${t.progress || 0}%"></div></div><div class="dl-bottom"><span>${(t.progress || 0).toFixed(1)}%</span><span>${fmtB(t.downloaded_bytes || 0)}</span></div>`;
}

function updateDl(t){
  let el = $(`#dl-${t.task_id}`);
  if(el){
    el.innerHTML = dlHTML(t);
    if(t.status === 'completed') el.classList.add('completed-anim');
  } else {
    const c = $('#dlList');
    const e = c.querySelector('.empty');
    if(e) c.innerHTML = '';
    c.prepend(mkDl(t));
  }
  updBadge();
}

window.cancelDl = id => fetch(`/api/cancel/${id}`, {method:'POST'}).then(() => refreshDl());

function initDl(){
  $('#clearDoneBtn')?.addEventListener('click', () => {
    fetch('/api/clear_completed', {method:'POST'}).then(() => {
      refreshDl();
      completedTasks.clear();
    });
  });
  setInterval(() => {
    if($('#view-downloads')?.classList.contains('active')) refreshDl();
    updBadge();
  }, 2000);
}

function updBadge(){
  fetch('/api/tasks').then(r => r.json()).then(d => {
    const a = (d.tasks || []).filter(t => t.status === 'running' || t.status === 'queued');
    const b = $('#activePill');
    const nb = $('#navBadge');
    if(a.length){
      if(b){ b.style.display = 'flex'; $('#activePillCount').textContent = a.length; }
      if(nb){ nb.style.display = ''; nb.textContent = a.length; }
    } else {
      if(b) b.style.display = 'none';
      if(nb) nb.style.display = 'none';
    }
  });
}

/* ======== QUEUE ======== */
function renderQueue(){
  fetch('/api/tasks').then(r => r.json()).then(d => {
    const q = (d.tasks || []).filter(t => t.status === 'queued');
    const c = $('#queueList');
    if(!q.length){
      c.innerHTML = '<div class="empty"><span class="material-icons-outlined">queue</span><p>Queue is empty</p></div>';
      return;
    }
    c.innerHTML = '';
    q.forEach((t, i) => {
      const d = document.createElement('div');
      d.className = 'queue-item';
      d.innerHTML = `<span class="q-pos">${i + 1}</span><div class="q-info"><div class="q-title">${esc(t.title)}</div><div class="q-sub">${t.total_chapters} chapters &middot; ${t.format}/${t.mode}</div></div>`;
      c.appendChild(d);
    });
  });
}

/* ======== LIBRARY ======== */
function refreshLib(){
  fetch('/api/library').then(r => r.json()).then(d => renderLib(d.files || []));
}

function renderLib(files){
  const c = $('#libList');
  if(!files.length){
    c.innerHTML = '<div class="empty"><span class="material-icons-outlined">inventory_2</span><p>Library is empty</p></div>';
    return;
  }
  c.innerHTML = '';
  files.forEach(f => {
    const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
    const ic = {'.cbz':'archive', '.pdf':'picture_as_pdf', '.epub':'auto_stories'}[ext] || 'folder';
    const d = document.createElement('div');
    d.className = 'lib-item';
    d.innerHTML = `<span class="material-icons-outlined">${ic}</span><span class="lib-name">${esc(f.name)}</span><span class="lib-size">${fmtB(f.size)}</span>`;
    c.appendChild(d);
  });
}

function initLib(){
  $('#openDirBtn')?.addEventListener('click', () => fetch('/api/open_folder', {method:'POST'}));
}

/* ======== HISTORY ======== */
function addHistory(m){
  history = history.filter(h => h.url !== m.url);
  history.unshift({
    title: m.title,
    url: m.url,
    source: m.source,
    source_key: m.source_key,
    cover_url: m.cover_url || '',
    author: m.author || 'Unknown',
    ts: Date.now(),
  });
  if(history.length > 50) history = history.slice(0, 50);
  localStorage.setItem('mdl_history', JSON.stringify(history));
}

function renderHistory(){
  const c = $('#historyList');
  if(!history.length){
    c.innerHTML = '<div class="empty"><span class="material-icons-outlined">history</span><p>No history yet</p></div>';
    return;
  }
  c.innerHTML = '';
  history.forEach(h => {
    const d = document.createElement('div');
    d.className = 'hist-item';
    d.innerHTML = `<img src="${esc(h.cover_url)}" alt="" onerror="this.style.visibility='hidden'"><div class="hist-info"><div class="hist-title">${esc(h.title)}</div><div class="hist-sub">${esc(h.source || '')} &middot; ${new Date(h.ts).toLocaleDateString()}</div></div>`;
    d.addEventListener('click', () => openModal(h));
    c.appendChild(d);
  });
}

function initHistory(){
  $('#clearHistBtn')?.addEventListener('click', () => {
    history = [];
    localStorage.removeItem('mdl_history');
    renderHistory();
  });
}

/* ======== SETTINGS ======== */
function loadSettings(){
  fetch('/api/settings').then(r => r.json()).then(d => {
    if(d.threads) $('#sThreads').value = d.threads;
    if(d.timeout) $('#sTimeout').value = d.timeout;
    if(d.retries) $('#sRetries').value = d.retries;
    if(d.download_dir){
      $('#sDirInput').value = d.download_dir;
      $('#sDirLabel').textContent = d.download_dir;
    }
    if(d.max_tasks) $('#sMaxTasks').value = d.max_tasks;
  }).catch(() => {});
}

function saveSettings(){
  const payload = {
    threads: parseInt($('#sThreads').value),
    format: $('#sFormat').value,
    mode: $('#sMode').value,
    timeout: parseInt($('#sTimeout').value),
    retries: parseInt($('#sRetries').value),
    download_dir: $('#sDirInput').value.trim(),
    max_tasks: parseInt($('#sMaxTasks').value),
  };
  fetch('/api/settings', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  })
  .then(r => r.json())
  .then(d => {
    if(d.error) toast(d.error, 'error');
    else {
      toast('Settings saved', 'success');
      if(d.download_dir) $('#sDirLabel').textContent = d.download_dir;
    }
  })
  .catch(() => toast('Failed to save settings', 'error'));
}

function initSettings(){
  ['sThreads', 'sFormat', 'sMode', 'sTimeout', 'sRetries', 'sMaxTasks'].forEach(id => {
    const el = $('#' + id);
    if(el) el.addEventListener('change', saveSettings);
  });
  $('#sDirApply')?.addEventListener('click', saveSettings);
  $('#sDirInput')?.addEventListener('keydown', e => {
    if(e.key === 'Enter') saveSettings();
  });

  // Accessibility toggles
  const rm = $('#sReduceMotion');
  const lt = $('#sLargerText');
  if(rm){
    rm.checked = localStorage.getItem('mdl_reduced_motion') === '1';
    rm.addEventListener('change', () => {
      applyAccessibility(rm.checked, lt?.checked || false);
      toast(rm.checked ? 'Motion reduced' : 'Motion enabled', 'success');
    });
  }
  if(lt){
    lt.checked = localStorage.getItem('mdl_larger_text') === '1';
    lt.addEventListener('change', () => {
      applyAccessibility(rm?.checked || false, lt.checked);
      toast(lt.checked ? 'Larger text on' : 'Default text size', 'success');
    });
  }
}

/* ======== HELPERS ======== */
function show(id){
  const el = $('#' + id);
  if(el) el.style.display = 'flex';
}

function hide(id){
  const el = $('#' + id);
  if(el) el.style.display = 'none';
}

function toast(msg, type){
  const t = $('#toast');
  if(!t) return;
  t.textContent = msg;
  t.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove('show'), 3500);
}

/* ======== INIT ======== */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initSplash();
  initSocket();
  initNav();
  initSearch();
  initUrl();
  initModal();
  initCart();
  initDl();
  initLib();
  initHistory();
  initSettings();
  loadSettings();
});

})();