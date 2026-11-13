import { build } from '../../../visualization/node_modules/esbuild/lib/main.js';
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const folder = dirname(fileURLToPath(import.meta.url));
const result = await build({
  entryPoints: [resolve(folder, 'src/app.js')],
  nodePaths: [resolve(folder, '../../../visualization/node_modules')],
  bundle: true, minify: true, format: 'iife', write: false,
  legalComments: 'inline', target: 'es2022',
});
const template = await readFile(resolve(folder, 'src/index.html'), 'utf8');
const css = await readFile(resolve(folder, 'src/style.css'), 'utf8');
const html = template.replace('/* STYLES */', () => css).replace(
  '/* SCRIPT */', () => result.outputFiles[0].text.replaceAll('</script', '<\\/script'),
);
await writeFile(resolve(folder, 'index.html'), html);
console.log(`Rev C offline viewer: ${(Buffer.byteLength(html) / 1024 / 1024).toFixed(2)} MiB`);
