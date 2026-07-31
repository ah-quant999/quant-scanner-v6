const fs = require('fs');
const { JSDOM } = require('E:/workbuddy-data/binaries/node/workspace/node_modules/jsdom');

const html = fs.readFileSync('E:/workspace/stock-scanner/repo-temp/index_master.html', 'utf8');
const errors = [];
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://ah-quant999.github.io/quant-scanner-v6/',
  beforeParse(window) {
    window.console.error = (...a) => errors.push('console.error: ' + a.join(' '));
    window.console.log = (...a) => {
      const s = a.join(' ');
      if (/renderStockCockpit error|error/i.test(s)) errors.push('console.log: ' + s);
    };
    window.onerror = (msg, src, line, col, err) => { errors.push('onerror: ' + msg + ' @' + line + ':' + col); };
    window.fetch = () => Promise.resolve({ json: () => Promise.resolve({}) });
  }
});
const { window } = dom;
const doc = window.document;

setTimeout(() => {
  console.log('ERRORS after load:', errors.length);
  errors.forEach(e => console.log('  ' + e));
  console.log('');

  const slot = doc.getElementById('cockpitVolSlot');
  console.log('cockpitVolSlot exists:', !!slot);
  if (slot) console.log('cockpitVolSlot text:', (slot.textContent || '').trim().substring(0, 100));

  const stockCockpit = doc.getElementById('stockCockpit');
  console.log('stockCockpit exists:', !!stockCockpit);
  console.log('stockCockpit display:', stockCockpit ? stockCockpit.style.display : 'N/A');

  // Try calling renderStockCockpit explicitly
  try {
    if (typeof window.renderStockCockpit === 'function') {
      window.renderStockCockpit();
      console.log('renderStockCockpit called OK');
    } else {
      console.log('renderStockCockpit NOT FOUND');
    }
  } catch(e) {
    console.log('renderStockCockpit threw:', e.message);
  }

  const slot2 = doc.getElementById('cockpitVolSlot');
  console.log('after call cockpitVolSlot exists:', !!slot2);
  if (slot2) console.log('after call text length:', slot2.innerText.trim().length, '| text:', slot2.innerText.trim().substring(0, 80));

  console.log('\nFINAL ERRORS:', errors.length);
  errors.forEach(e => console.log('  ' + e));
}, 1200);
