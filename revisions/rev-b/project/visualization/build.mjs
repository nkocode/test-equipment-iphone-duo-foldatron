import { build } from 'esbuild';
import { readFile, writeFile } from 'node:fs/promises';
const result = await build({ entryPoints: ['src/app.js'], bundle: true, minify: true, format: 'iife', write: false, legalComments: 'inline', target: 'es2022' });
const template = await readFile('src/index.html', 'utf8');
const css = await readFile('src/style.css', 'utf8');
const html = template.replace('/* STYLES */', () => css).replace('/* SCRIPT */', () => result.outputFiles[0].text.replaceAll('</script', '<\\/script'));
await writeFile('index.html', html);
console.log(`Built offline viewer: ${(Buffer.byteLength(html) / 1024).toFixed(0)} KB`);
