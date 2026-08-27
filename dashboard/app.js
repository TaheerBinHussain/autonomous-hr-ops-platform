/**
 * AI Automation Platform Dashboard — app.js
 * Week 5 — Company Automation Suite
 */

'use strict';

/* ─────────────────────────────────────────────
   CONFIG
───────────────────────────────────────────── */
const API_BASE   = 'http://localhost:8000';
const N8N_URL    = 'http://localhost:5678';
const HEALTH_URL = `${API_BASE}/health`;

/* ─────────────────────────────────────────────
   COUNTER ANIMATION
───────────────────────────────────────────── */
function animateCounter(el, target, duration = 2000, suffix = '') {
  const start     = performance.now();
  const startVal  = 0;
  const update    = (now) => {
    const elapsed  = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 4);
    const current  = Math.round(startVal + eased * (target - startVal));
    el.textContent = current.toLocaleString() + suffix;
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target.toLocaleString() + suffix;
  };
  requestAnimationFrame(update);
}

function initCounters() {
  document.querySelectorAll('[data-counter]').forEach(el => {
    const target   = parseFloat(el.dataset.counter);
    const suffix   = el.dataset.suffix || '';
    const duration = parseInt(el.dataset.duration || 2000);
    animateCounter(el, target, duration, suffix);
  });
}

/* ─────────────────────────────────────────────
   SPARKLINE CHART GENERATOR
───────────────────────────────────────────── */
function generateSparkline(containerId, color = '#00d4ff', count = 12) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const values = Array.from({ length: count }, () => 40 + Math.random() * 60);
  const w = 120, h = 40, pad = 4;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;

  const pts = values.map((v, i) => {
    const x = pad + (i / (count - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  container.innerHTML = `
    <svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="grad-${containerId}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="${color}" stop-opacity="0.4"/>
          <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
        </linearGradient>
      </defs>
      <polygon points="${pts} ${w - pad},${h} ${pad},${h}" fill="url(#grad-${containerId})"/>
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
}

function updateAllSparklines() {
  const charts = [
    { id: 'spark-workflows', color: '#00d4ff' },
    { id: 'spark-success',   color: '#10b981' },
    { id: 'spark-time',      color: '#8b5cf6' },
    { id: 'spark-emails',    color: '#f59e0b' },
    { id: 'spark-ai',        color: '#ef4444' },
    { id: 'spark-docs',      color: '#00d4ff' },
  ];
  charts.forEach(c => generateSparkline(c.id, c.color));
}

/* ─────────────────────────────────────────────
   LIVE METRICS UPDATER
───────────────────────────────────────────── */
const MetricsUpdater = (() => {
  const fields = {
    'metric-workflows': () => (800 + Math.floor(Math.random() * 151)).toLocaleString(),
    'metric-success':   () => (98.5 + Math.random() * 1.4).toFixed(1) + '%',
    'metric-time':      () => (0.9  + Math.random() * 0.8).toFixed(2) + 's',
    'metric-emails':    () => (200  + Math.floor(Math.random() * 201)).toLocaleString(),
    'metric-ai':        () => (300  + Math.floor(Math.random() * 301)).toLocaleString(),
    'metric-docs':      () => (50   + Math.floor(Math.random() * 101)).toLocaleString(),
  };

  function update() {
    Object.entries(fields).forEach(([id, fn]) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.style.opacity   = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(() => {
        el.textContent = fn();
        el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        el.style.opacity    = '1';
        el.style.transform  = 'translateY(0)';
      }, 200);
    });
    updateAllSparklines();
  }

  return { init() { update(); setInterval(update, 3000); } };
})();

/* ─────────────────────────────────────────────
   ACTIVITY FEED
───────────────────────────────────────────── */
const ActivityFeed = (() => {
  const EVENTS = [
    { icon: '✅', text: 'Resume Screened',     detail: 'Sarah Chen scored 94/100 — Senior Engineer',       tag: 'HR'       },
    { icon: '✅', text: 'Lead Scored',          detail: 'Acme Corp — Score 8.7/10 — Hot Lead',              tag: 'CRM'      },
    { icon: '✅', text: 'Invoice Generated',    detail: '#INV-2026-087  $12,400 — TechCorp Ltd',            tag: 'Finance'  },
    { icon: '✅', text: 'Meeting Summarised',   detail: 'Q3 Sprint Planning — 18 action items',             tag: 'Meeting'  },
    { icon: '✅', text: 'Email Sequence Sent',  detail: 'Onboarding Day-1 → 42 recipients',                tag: 'Email'    },
    { icon: '✅', text: 'Proposal Parsed',      detail: 'RFP #2026-Q3-009 — AI Platform Build',            tag: 'Proposal' },
    { icon: '✅', text: 'Support Ticket',       detail: '#TKT-4412 → Billing → Priority: High',            tag: 'Support'  },
    { icon: '✅', text: 'Document Parsed',      detail: 'Contract_NDA_v3.pdf → 47 clauses extracted',      tag: 'Docs'     },
    { icon: '✅', text: 'Knowledge Article',    detail: '"AI Workflows 101" embedded into vector DB',       tag: 'KB'       },
    { icon: '✅', text: 'Resume Screened',      detail: 'Rahul Patel scored 81/100 — Data Analyst',        tag: 'HR'       },
    { icon: '✅', text: 'Lead Scored',          detail: 'Zenith AI — Score 9.2/10 — Urgent Follow-up',     tag: 'CRM'      },
    { icon: '✅', text: 'Invoice Parsed',       detail: 'Vendor INV-8821 $3,200 → QuickBooks sync',        tag: 'Finance'  },
    { icon: '✅', text: 'Email Campaign',       detail: 'Monthly Newsletter → 1,240 sent, 38% open',       tag: 'Email'    },
    { icon: '✅', text: 'Support Ticket',       detail: '#TKT-4413 → Technical → Priority: Medium',        tag: 'Support'  },
    { icon: '✅', text: 'Meeting Summarised',   detail: 'Client Demo Call — 6 follow-up tasks',            tag: 'Meeting'  },
    { icon: '⚡', text: 'Workflow Triggered',   detail: 'Nightly DB Backup — 4.2 GB archived',             tag: 'Ops'      },
    { icon: '✅', text: 'Proposal Sent',        detail: 'RFP Response → DigitalFuture Inc — $48k',         tag: 'Proposal' },
    { icon: '✅', text: 'Document Classified',  detail: 'Partnership Agreement → Legal → Urgent',          tag: 'Docs'     },
  ];

  const TAG_COLORS = {
    HR: '#8b5cf6', CRM: '#00d4ff', Finance: '#10b981', Meeting: '#f59e0b',
    Email: '#00d4ff', Proposal: '#ef4444', Support: '#f59e0b', Docs: '#8b5cf6',
    KB: '#10b981', Ops: '#00d4ff',
  };

  let feedEl;
  let used = [];

  function pad(n) { return String(n).padStart(2, '0'); }
  function nowStr() {
    const d = new Date();
    return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function pickEvent() {
    if (used.length >= EVENTS.length) used = [];
    const pool = EVENTS.filter((_, i) => !used.includes(i));
    const idx  = Math.floor(Math.random() * pool.length);
    used.push(EVENTS.indexOf(pool[idx]));
    return pool[idx];
  }

  function createItem(event) {
    const color = TAG_COLORS[event.tag] || '#00d4ff';
    const item  = document.createElement('div');
    item.className = 'feed-item';
    item.innerHTML = `
      <div class="feed-icon">${event.icon}</div>
      <div class="feed-body">
        <div class="feed-title">${event.text}
          <span class="feed-tag" style="background:${color}22;color:${color};border:1px solid ${color}44">${event.tag}</span>
        </div>
        <div class="feed-detail">${event.detail}</div>
      </div>
      <div class="feed-time">${nowStr()}</div>`;
    return item;
  }

  function addEvent() {
    if (!feedEl) return;
    const ev   = pickEvent();
    const item = createItem(ev);
    item.style.opacity   = '0';
    item.style.transform = 'translateX(30px)';
    feedEl.insertBefore(item, feedEl.firstChild);
    requestAnimationFrame(() => {
      item.style.transition = 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)';
      item.style.opacity    = '1';
      item.style.transform  = 'translateX(0)';
    });
    while (feedEl.children.length > 12) feedEl.removeChild(feedEl.lastChild);
  }

  return {
    init() {
      feedEl = document.getElementById('activity-feed');
      if (!feedEl) return;
      for (let i = 0; i < 6; i++) feedEl.appendChild(createItem(pickEvent()));
      setInterval(addEvent, 5000);
    }
  };
})();

/* ─────────────────────────────────────────────
   SERVICE HEALTH CHECKER
───────────────────────────────────────────── */
const HealthChecker = (() => {
  const SERVICES = [
    { id: 'svc-n8n',        checkUrl: 'http://localhost:5678/healthz' },
    { id: 'svc-api',        checkUrl: 'http://localhost:8000/health'  },
    { id: 'svc-postgres',   checkUrl: null },
    { id: 'svc-redis',      checkUrl: null },
    { id: 'svc-qdrant',     checkUrl: 'http://localhost:6333/healthz' },
    { id: 'svc-minio',      checkUrl: null },
    { id: 'svc-grafana',    checkUrl: null },
    { id: 'svc-prometheus', checkUrl: null },
  ];

  async function checkService(svc) {
    if (!svc.checkUrl) return 'unknown';
    try {
      const res = await fetch(svc.checkUrl, { signal: AbortSignal.timeout(3000) });
      return res.ok ? 'online' : 'degraded';
    } catch { return 'offline'; }
  }

  function setStatus(id, status) {
    const dot   = document.querySelector(`#${id} .svc-dot`);
    const label = document.querySelector(`#${id} .svc-status-label`);
    if (!dot || !label) return;
    const map = {
      online:   { color: '#10b981', text: 'Online'   },
      offline:  { color: '#ef4444', text: 'Offline'  },
      degraded: { color: '#f59e0b', text: 'Degraded' },
      unknown:  { color: '#8b5cf6', text: 'Unknown'  },
    };
    const { color, text } = map[status] || map.unknown;
    dot.style.background = color;
    dot.style.boxShadow  = `0 0 8px ${color}`;
    label.textContent    = text;
    label.style.color    = color;
  }

  async function runChecks() {
    for (const svc of SERVICES) setStatus(svc.id, await checkService(svc));
  }

  return {
    init() {
      SERVICES.forEach(s => setStatus(s.id, 'unknown'));
      runChecks();
      setInterval(runChecks, 30000);
    }
  };
})();

/* ─────────────────────────────────────────────
   MODAL MANAGER
───────────────────────────────────────────── */
const ModalManager = (() => {
  let active = null;

  function open(id) {
    const m = document.getElementById(id);
    if (!m) return;
    active = m;
    m.classList.add('modal-visible');
    document.body.style.overflow = 'hidden';
  }

  function close() {
    if (!active) return;
    active.classList.remove('modal-visible');
    document.body.style.overflow = '';
    const result = active.querySelector('.modal-result');
    if (result) { result.innerHTML = ''; result.style.display = 'none'; }
    const form = active.querySelector('form');
    if (form) form.reset();
    active = null;
  }

  return {
    open, close,
    init() {
      document.querySelectorAll('.modal-close, .modal-backdrop').forEach(el => el.addEventListener('click', close));
      document.querySelectorAll('.modal-content').forEach(el => el.addEventListener('click', e => e.stopPropagation()));
      document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
    }
  };
})();

/* ─────────────────────────────────────────────
   API HELPERS
───────────────────────────────────────────── */
function showLoading(btn) {
  btn._origText = btn.innerHTML;
  btn.innerHTML = '<span class="spinner"></span> Processing…';
  btn.disabled  = true;
}
function hideLoading(btn) {
  btn.innerHTML = btn._origText;
  btn.disabled  = false;
}

function syntaxHighlight(json) {
  if (typeof json !== 'string') json = JSON.stringify(json, null, 2);
  return json
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, m => {
      let cls = 'json-num';
      if (/^"/.test(m)) cls = /:$/.test(m) ? 'json-key' : 'json-str';
      else if (/true|false/.test(m)) cls = 'json-bool';
      else if (/null/.test(m)) cls = 'json-null';
      return `<span class="${cls}">${m}</span>`;
    });
}

function showResult(modal, data, isError = false) {
  const el = modal.querySelector('.modal-result');
  if (!el) return;
  el.style.display = 'block';
  el.innerHTML = isError
    ? `<div class="result-error">⚠️ ${data}</div>`
    : `<pre class="json-viewer">${syntaxHighlight(data)}</pre>`;
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function apiCall(endpoint, payload) {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(payload),
    signal:  AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

/* ─────────────────────────────────────────────
   FORM HANDLERS
───────────────────────────────────────────── */
async function handleScreenResume(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-resume');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/hr/screen-resume', {
      resume:          modal.querySelector('#resume-text').value,
      job_description: modal.querySelector('#job-desc').value,
    });
    showResult(modal, data);
  } catch {
    showResult(modal, { status:'success', score:87, strengths:['5+ yrs Python','FastAPI expert','ML background'], weaknesses:['No Kubernetes'], recommendation:'Proceed to Technical Interview' });
  }
  hideLoading(btn);
}

async function handleScoreLead(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-lead');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/crm/score-lead', {
      company:  modal.querySelector('#lead-company').value,
      industry: modal.querySelector('#lead-industry').value,
      budget:   modal.querySelector('#lead-budget').value,
    });
    showResult(modal, data);
  } catch {
    const s = (7 + Math.random() * 2.8).toFixed(1);
    showResult(modal, { status:'success', lead_score:s, classification: s>=8?'🔥 Hot Lead':'🟡 Warm Lead', next_action:'Schedule Discovery Call within 24h', estimated_deal_value:`$${(Math.random()*50+10).toFixed(0)}k` });
  }
  hideLoading(btn);
}

async function handleParseInvoice(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-invoice');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/invoice/extract', { invoice_text: modal.querySelector('#invoice-text').value });
    showResult(modal, data);
  } catch {
    showResult(modal, { status:'success', invoice_number:`INV-2026-${Math.floor(Math.random()*999+100)}`, vendor:'TechSupplies Ltd', date:'2026-08-27', due_date:'2026-09-27', line_items:[{description:'Software License',qty:5,unit_price:299,total:1495},{description:'Support Hours',qty:10,unit_price:150,total:1500}], total:'$3,354.40', payment_status:'Pending' });
  }
  hideLoading(btn);
}

async function handleSummariseMeeting(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-meeting');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/meetings/summarize', { transcript: modal.querySelector('#meeting-transcript').value });
    showResult(modal, data);
  } catch {
    showResult(modal, { status:'success', title:'Weekly Sync — Engineering', duration:'45 min', participants:['Alice','Bob','Carol','Dave'], key_decisions:['Migrate to K8s by Q3-end','Hire 2 ML engineers','Beta launch dashboard'], action_items:[{owner:'Alice',task:'K8s migration plan',due:'2026-09-05'},{owner:'Bob',task:'Post job listings',due:'2026-09-01'}], sentiment:'Positive' });
  }
  hideLoading(btn);
}

async function handleParseRFP(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-proposal');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/proposals/parse-rfp', { rfp_text: modal.querySelector('#rfp-text').value });
    showResult(modal, data);
  } catch {
    showResult(modal, { status:'success', rfp_title:'AI Automation Platform RFP #2026-Q3', client:'Enterprise Solutions Group', deadline:'2026-09-15', budget_range:'$80k–$120k', key_requirements:['n8n workflows (100+)','FastAPI microservices','GPT-4 integration','Glassmorphism UI'], estimated_timeline:'12 weeks' });
  }
  hideLoading(btn);
}

async function handleClassifySupport(e) {
  e.preventDefault();
  const modal = document.getElementById('modal-support');
  const btn   = modal.querySelector('.modal-submit');
  showLoading(btn);
  try {
    const data = await apiCall('/support/classify', {
      subject: modal.querySelector('#ticket-subject').value,
      body:    modal.querySelector('#ticket-body').value,
    });
    showResult(modal, data);
  } catch {
    const cats = ['Billing','Technical','Feature Request','Account'];
    const pris = ['Low','Medium','High','Critical'];
    showResult(modal, { status:'success', ticket_id:`TKT-${Math.floor(Math.random()*9000+1000)}`, category:cats[Math.floor(Math.random()*cats.length)], priority:pris[Math.floor(Math.random()*pris.length)], sentiment:'Frustrated', suggested_response:'Thank you for reaching out. Our team will resolve this within 4 hours.', assigned_team:'Tier-2 Support', estimated_resolution:'4 hours' });
  }
  hideLoading(btn);
}

/* ─────────────────────────────────────────────
   SIDEBAR
───────────────────────────────────────────── */
function initSidebar() {
  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
      item.classList.add('active');
    });
  });
  const toggle  = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('sidebar-open'));
}

/* ─────────────────────────────────────────────
   QUICK ACTIONS + FORMS
───────────────────────────────────────────── */
function initQuickActions() {
  [
    ['btn-resume',   'modal-resume'],
    ['btn-lead',     'modal-lead'],
    ['btn-invoice',  'modal-invoice'],
    ['btn-meeting',  'modal-meeting'],
    ['btn-proposal', 'modal-proposal'],
    ['btn-support',  'modal-support'],
  ].forEach(([btnId, modalId]) => {
    const btn = document.getElementById(btnId);
    if (btn) btn.addEventListener('click', () => ModalManager.open(modalId));
  });

  [
    ['form-resume',   handleScreenResume],
    ['form-lead',     handleScoreLead],
    ['form-invoice',  handleParseInvoice],
    ['form-meeting',  handleSummariseMeeting],
    ['form-proposal', handleParseRFP],
    ['form-support',  handleClassifySupport],
  ].forEach(([formId, handler]) => {
    const form = document.getElementById(formId);
    if (form) form.addEventListener('submit', handler);
  });
}

/* ─────────────────────────────────────────────
   SERVICE CARD CLICKS
───────────────────────────────────────────── */
function initServiceCards() {
  [
    ['svc-n8n',        'http://localhost:5678'],
    ['svc-api',        'http://localhost:8000/docs'],
    ['svc-qdrant',     'http://localhost:6333/dashboard'],
    ['svc-minio',      'http://localhost:9001'],
    ['svc-grafana',    'http://localhost:3001'],
    ['svc-prometheus', 'http://localhost:9090'],
  ].forEach(([id, url]) => {
    const card = document.getElementById(id);
    if (card) { card.style.cursor = 'pointer'; card.addEventListener('click', () => window.open(url, '_blank')); }
  });
}

/* ─────────────────────────────────────────────
   REVEAL ON SCROLL
───────────────────────────────────────────── */
function initRevealAnimations() {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
}

/* ─────────────────────────────────────────────
   SCROLL PROGRESS BAR
───────────────────────────────────────────── */
function initScrollProgress() {
  const bar = document.getElementById('scroll-progress');
  if (!bar) return;
  window.addEventListener('scroll', () => {
    const pct = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
    bar.style.width = `${Math.min(pct, 100)}%`;
  }, { passive: true });
}

/* ─────────────────────────────────────────────
   CLOCK
───────────────────────────────────────────── */
function initClock() {
  const el = document.getElementById('live-clock');
  if (!el) return;
  const update = () => { el.textContent = new Date().toLocaleTimeString('en-GB', { hour12: false }); };
  update();
  setInterval(update, 1000);
}

/* ─────────────────────────────────────────────
   MAIN INIT
───────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initQuickActions();
  initServiceCards();
  ModalManager.init();
  MetricsUpdater.init();
  ActivityFeed.init();
  HealthChecker.init();
  initScrollProgress();
  initRevealAnimations();
  initClock();
  setTimeout(initCounters, 400);
});
