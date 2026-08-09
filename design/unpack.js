#!/usr/bin/env node
// Распаковывает bundled-макет new_broadcaster_design.html в читаемый HTML.
//
// Исходник — bundled-страница: реальная разметка лежит JSON-строкой в
// <script type="__bundler/template">, ассеты (шрифты, JS) — в
// <script type="__bundler/manifest">. Грепать исходник бесполезно.
//
// Usage: node design/unpack.js

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SRC = path.join(ROOT, 'new_broadcaster_design.html');
const OUT_HTML = path.join(__dirname, 'new_broadcaster_design.unpacked.html');
const OUT_INDEX = path.join(__dirname, 'new_broadcaster_design.manifest-index.json');

const src = fs.readFileSync(SRC, 'utf8');

function block(type) {
  const re = new RegExp(`<script type="${type.replace('/', '\\/')}"[^>]*>([\\s\\S]*?)<\\/script>`);
  const m = src.match(re);
  if (!m) throw new Error(`script block not found: ${type}`);
  return JSON.parse(m[1].trim());
}

const template = block('__bundler/template');
fs.writeFileSync(OUT_HTML, template);

const manifest = block('__bundler/manifest');
const index = Object.entries(manifest).map(([id, a]) => ({
  id,
  mime: a.mime,
  compressed: a.compressed,
  bytes: (a.data || a.content || '').length,
}));
fs.writeFileSync(OUT_INDEX, JSON.stringify(index, null, 2));

console.log(`${path.relative(ROOT, OUT_HTML)}: ${template.length} bytes`);
console.log(`${path.relative(ROOT, OUT_INDEX)}: ${index.length} assets`);
