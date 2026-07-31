const fs=require('fs');
const html=fs.readFileSync('E:/workspace/quant-scanner-v8/index.html','utf8');
const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
let m,i=0,errs=0;
while((m=re.exec(html))){
  i++;
  try{ new Function(m[1]); }
  catch(e){ errs++; console.log('SCRIPT #'+i+' SYNTAX ERROR:', e.message); }
}
console.log('Checked '+i+' inline scripts, syntax errors: '+errs);
