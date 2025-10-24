const fs = require('fs');
const vm = require('vm');

// load userscript and extract parseOrderText + helper functions by naive text extraction
const us = fs.readFileSync('d:/Daten/3-PROJECTS/4-EXTRACT_PAPA/scripts/taobao_export_json.user.js','utf8');

// find parseOrderText by locating its start and matching braces
const idx = us.indexOf('function parseOrderText(');
if (idx < 0) { console.error('parseOrderText not found'); process.exit(1); }
let i = us.indexOf('{', idx);
if (i < 0) { console.error('opening brace not found'); process.exit(1); }
let depth = 0; let end = -1;
for (let j = i; j < us.length; ++j) {
  const ch = us[j];
  if (ch === '{') depth++;
  else if (ch === '}') { depth--; if (depth === 0) { end = j; break; } }
}
if (end < 0) { console.error('matching brace not found'); process.exit(1); }
const fnText = us.slice(idx, end+1);

// evaluate in a sandbox and expose parseOrderText
const sandbox = { console: console, Date: Date };
vm.createContext(sandbox);
vm.runInContext(fnText + '\n;parseOrderText;', sandbox);
const parseOrderText = sandbox.parseOrderText || sandbox['parseOrderText'];
if (typeof parseOrderText !== 'function') { console.error('parseOrderText not loaded after eval'); process.exit(1); }

const snips = JSON.parse(fs.readFileSync('d:/Daten/3-PROJECTS/4-EXTRACT_PAPA/scripts/test_snippets.json','utf8'));
let rows = [];
for(const s of snips) {
  const out = parseOrderText(s.snippet, true, '');
  console.log('--- SNIPPET ---');
  console.log(s.snippet.slice(0,200).replace(/\n/g,'\\n'));
  console.log('parsed rows:', out);
  rows = rows.concat(out);
}
console.log('ALL ROWS:\n', rows);
