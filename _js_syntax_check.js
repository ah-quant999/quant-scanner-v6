// 抽取 HTML 内联 <script> 并用 new Function 做纯语法解析校验（不执行）
const fs = require('fs');
const files = process.argv.slice(2);
let bad = 0;
for (const f of files) {
  const html = fs.readFileSync(f, 'utf-8');
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
  let m, idx = 0, fileBad = 0;
  while ((m = re.exec(html)) !== null) {
    idx++;
    const code = m[1];
    if (!code.trim()) continue;
    try { new Function(code); } catch (e) {
      fileBad++; bad++;
      // 定位大致行号
      const upto = html.slice(0, m.index).split('\n').length;
      console.log(`[FAIL] ${f} script#${idx} (起始行~${upto}): ${e.message}`);
    }
  }
  if (!fileBad) console.log(`[OK] ${f} (${idx} script blocks)`);
}
process.exit(bad ? 1 : 0);
