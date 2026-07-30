const fs = require('fs');
const { JSDOM } = require('E:/workbuddy-data/binaries/node/workspace/node_modules/jsdom');

const html = fs.readFileSync('E:/workspace/stock-scanner/repo-temp/v8/dist/index.html', 'utf8');
const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://ah-quant999.github.io/quant-scanner-v8/',
  beforeParse(window) {
    window.console.error = (...a) => errors.push('console.error: ' + a.join(' '));
    window.onerror = (msg, src, line, col, err) => { errors.push('onerror: ' + msg + ' @' + line + ':' + col); };
    // stub fetch to avoid noise
    window.fetch = () => Promise.resolve({ json: () => Promise.resolve({}) });
  }
});
const { window } = dom;
const doc = window.document;

function secState() {
  const op = doc.getElementById('sec-op');
  const lg = doc.getElementById('sec-lg');
  const opTab1 = doc.getElementById('opTab1');
  const lgTd = doc.getElementById('lg-td');
  return {
    opActive: op && op.classList.contains('active'),
    lgActive: lg && lg.classList.contains('active'),
    opTab1TextLen: opTab1 ? opTab1.innerText.trim().length : -1,
    lgTdTextLen: lgTd ? lgTd.innerText.trim().length : -1,
  };
}

setTimeout(() => {
  console.log('JS ERRORS (post-load):', errors.length);
  errors.forEach(e => console.log('  ' + e));
  console.log('');

  // simulate admin login
  try {
    window.localStorage.setItem('v8_admin','1');
    window.refreshAdminUI();
    console.log('isAdmin:', window.isAdmin());
  } catch(e){ console.log('login sim err:', e.message); }

  // click 运维
  const opTab = [...doc.querySelectorAll('.tab')].find(t => t.dataset.sec === 'op');
  try { opTab.click(); } catch(e){ console.log('click op err:', e.message); }
  console.log('after click 运维:', JSON.stringify(secState()));

  // click 逻辑详解
  const lgTab = [...doc.querySelectorAll('.tab')].find(t => t.dataset.sec === 'lg');
  try { lgTab.click(); } catch(e){ console.log('click lg err:', e.message); }
  console.log('after click 逻辑详解:', JSON.stringify(secState()));

  // check lg sub-panes content
  const lgPanes = [...doc.querySelectorAll('#sec-lg .lg-pane')];
  console.log('lg-panes:', lgPanes.map(p => p.id + '(' + p.innerText.trim().length + ')').join(', '));

  console.log('\nERRORS after clicks:', errors.length);
  errors.forEach(e => console.log('  ' + e));
}, 800);
