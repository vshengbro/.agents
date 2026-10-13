#!/usr/bin/env node
/**
 * deploy-site.js — 依赖感知的静态站点多文件部署
 *
 * 为「纯单文件上传器」补上缺失的那一半：
 * 扫依赖图 → 拓扑排序（叶子优先）→ 逐个把本地引用改写成最终 URL → 上传。
 * 单文件上传器自己不做这些，所以多文件站点必须由本脚本驱动。
 *
 * 用法:
 *   node deploy-site.js <site-dir> [upload.js 路径]
 *   node deploy-site.js ./site
 *   node deploy-site.js ./site index.html      # 只部署入口及其传递依赖
 *
 * 输出: JSON { entry_url, files: { <相对路径>: <url> } }  → stdout
 * 进度日志走 stderr，方便 `node deploy-site.js . > result.json`。
 *
 * 成对的两个要点（详见 SKILL.md pitfalls 8 / 9）：
 *   - importmap 的裸说明符必须当依赖边，否则 vendor bundle 会排在用到它的模块之后。
 *   - 上传器的 stdout 混着进度行，不能整段 JSON.parse。
 */
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

const SITE = path.resolve(process.argv[2] || '.');
const SKIP_FILES = new Set(['build-deps.js', 'deploy-ltpp.js', 'deploy-site.js', 'serve.py', 'README.md', '.DS_Store']);
const SKIP_DIR = new Set(['node_modules', '.git', '.cache']);
const TEXT_EXT = new Set(['.html', '.htm', '.js', '.mjs', '.css', '.svg', '.json', '.txt']);
// 二进制扩展名只当叶子，绝不按文本打开（PNG 0x89 / WASM 0x00 会 UnicodeDecodeError）
const EXTERNAL = /^(https?:|data:|blob:|mailto:|tel:|\/\/|#)/i;

function findUploader() {
  const arg = process.argv.find(a => a.endsWith('upload.js'));
  if (arg) return path.resolve(arg);
  for (const d of [path.join(__dirname), path.join(path.dirname(__dirname)), process.cwd()]) {
    const p = path.join(d, 'upload.js');
    if (fs.existsSync(p)) return p;
  }
  console.error('找不到 upload.js —— 显式传入路径: node deploy-site.js <site-dir> <upload.js>');
  process.exit(1);
}
const UPLOAD = findUploader();

const SCOPE = process.argv.slice(3).filter(a => !a.endsWith('.js') && path.resolve(SITE, a) !== path.resolve(UPLOAD));

function walk(dir, out = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.') && e.name !== '.') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { if (!SKIP_DIR.has(e.name)) walk(p, out); }
    else if (!SKIP_FILES.has(e.name)) out.push(p);
  }
  return out;
}

const SCANNERS = {
  '.html': [
    /<script[^>]*\ssrc\s*=\s*["']([^"']+)["']/gi,
    /<link[^>]*\shref\s*=\s*["']([^"']+)["']/gi,
    /<img[^>]*\ssrc\s*=\s*["']([^"']+)["']/gi,
    /<source[^>]*\ssrc\s*=\s*["']([^"']+)["']/gi,
  ],
  '.js': [
    /\bimport\s+[^;'"]*?from\s*["']([^"']+)["']/gi,
    /\bimport\s*["']([^"']+)["']/gi,
    /\bimport\s*\(\s*["']([^"']+)["']\s*\)/gi,
    /\bfetch\s*\(\s*["']([^"']+)["']\s*\)/gi,
    /\bnew\s+URL\s*\(\s*["']([^"']+)["']/gi,
  ],
  '.css': [/url\s*\(\s*["']?([^"')]+)["']?\s*\)/gi, /@import\s+(?:url\()?\s*["']([^"']+)["']/gi],
};

const allFiles = walk(SITE);
const known = new Set(allFiles);
const rel = f => path.relative(SITE, f);

/** 收集一个文件里的本地引用；importmap 的裸说明符映射也算边 */
function refsOf(file) {
  const ext = path.extname(file).toLowerCase();
  if (!TEXT_EXT.has(ext)) return [];
  const src = fs.readFileSync(file, 'utf8');
  const out = [];
  for (const re of SCANNERS[ext] || []) {
    re.lastIndex = 0;
    let m;
    while ((m = re.exec(src)) !== null) {
      const ref = m[1].trim();
      if (!ref || EXTERNAL.test(ref)) continue;
      const abs = path.resolve(path.dirname(file), ref);
      if (known.has(abs)) out.push({ abs, literal: ref });
    }
  }
  if (ext === '.html') {
    const im = src.match(/<script[^>]*type\s*=\s*["']importmap["'][^>]*>([\s\S]*?)<\/script>/i);
    if (im) {
      const re2 = /(["'])([^"']+)\1\s*:\s*(["'])([^"']+)\3/g;
      let m2;
      while ((m2 = re2.exec(im[1])) !== null) {
        const val = m2[4].trim();
        if (EXTERNAL.test(val)) continue;
        const abs = path.resolve(path.dirname(file), val);
        if (known.has(abs)) out.push({ abs, literal: val, viaImportmap: true, spec: m2[2] });
      }
    }
  }
  const seen = new Set();
  return out.filter(f => { const k = f.abs + '|' + f.literal; if (seen.has(k)) return false; seen.add(k); return true; });
}

let selected = new Set(allFiles);
if (SCOPE.length) {
  selected = new Set();
  const add = f => { if (selected.has(f) || !known.has(f)) return; selected.add(f); for (const r of refsOf(f)) add(r.abs); };
  for (const s of SCOPE) {
    const abs = path.resolve(SITE, s);
    if (!known.has(abs)) { console.error(`scope 路径不存在: ${s}`); process.exit(1); }
    add(abs);
  }
}

// 拓扑排序：叶子优先，同层按路径排序 → 可复现
const deps = new Map([...selected].map(f => [f, refsOf(f).map(r => r.abs).filter(d => selected.has(d))]));
const order = [], done = new Set();
const visit = (f, stack = new Set()) => {
  if (done.has(f) || stack.has(f)) return;   // 环：先传一边，日志里会体现
  stack.add(f);
  for (const d of [...deps.get(f)].sort()) visit(d, stack);
  stack.delete(f);
  done.add(f);
  order.push(f);
};
for (const f of [...selected].sort()) visit(f);

console.error(`上传顺序（叶子优先，共 ${order.length} 个文件）:`);
order.forEach((f, i) => console.error(`  ${i + 1}. ${rel(f)}  ← ${deps.get(f).length} 个依赖`));

const escapeRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

function rewrite(file, urlMap) {
  const ext = path.extname(file).toLowerCase();
  const original = fs.readFileSync(file);
  if (!TEXT_EXT.has(ext)) return { buf: original, changed: false };
  let src = original.toString('utf8');
  for (const { abs, literal } of refsOf(file)) {
    const url = urlMap.get(abs);
    if (!url) continue;
    const before = src;
    const relForm = path.relative(path.dirname(file), abs);
    for (const re of [
      new RegExp(escapeRe(literal), 'g'),
      new RegExp(escapeRe('./' + relForm), 'g'),
      new RegExp(escapeRe(relForm), 'g'),
    ]) src = src.replace(re, url);
    if (src !== before) console.error(`    改写 ${literal} → ${url.slice(0, 46)}…`);
  }
  return { buf: Buffer.from(src), changed: src !== original.toString('utf8') };
}

const urlMap = new Map();
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'deploy-site-'));
let entry = null;

for (const f of order) {
  const { buf, changed } = rewrite(f, urlMap);
  let target = f;
  if (changed) {
    target = path.join(tmp, rel(f).replace(/[\\/]/g, '__'));  // 保留扩展名：服务端靠它推断 MIME
    fs.writeFileSync(target, buf);
  }
  console.error(`\n上传 ${rel(f)}${changed ? '（引用已改写）' : ''} …`);
  let out;
  try {
    out = execFileSync('node', [UPLOAD, target], { encoding: 'utf8', maxBuffer: 32 * 1024 * 1024 });
  } catch (e) {
    console.error('上传失败:', e.message);
    process.exit(1);
  }
  // stdout 混着进度行，取最后一段 JSON 数组
  let arr;
  try {
    const raw = out.trim();
    const s = raw.lastIndexOf('[\n  {');
    arr = JSON.parse(s >= 0 ? raw.slice(s) : raw.slice(raw.lastIndexOf('[')));
  } catch { console.error('无法解析上传输出:\n' + out); process.exit(1); }
  const r = Array.isArray(arr) ? arr[0] : arr;
  if (!r || r.error || !r.url) { console.error('上传返回错误:', JSON.stringify(r)); process.exit(1); }
  urlMap.set(f, r.url);
  if (!entry && f.toLowerCase().endsWith('.html')) entry = r.url;
  console.error(`  ✓ ${r.url}\n    ${r.size}B verified=${r.verified}${r.verifiedMd5 ? ' md5=' + r.verifiedMd5.slice(0, 12) + '…' : ''}`);
}
fs.rmSync(tmp, { recursive: true, force: true });

console.log(JSON.stringify({
  entry_url: entry,
  files: Object.fromEntries([...urlMap].map(([k, v]) => [rel(k), v])),
}, null, 2));
