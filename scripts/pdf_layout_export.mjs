#!/usr/bin/env node
/**
 * PDF -> reading-order blocks (JSONL) with the layout reconstruction of the pdf-editor project.
 *
 * [EN]
 * - Role: offline step of the PDF corpus. Per page: paragraphs with their role (body, heading, list-item, caption,
 *   header, footer, footnote, other), tables as row/column grids, figures; in the reconstructed reading order.
 *   Header/footer detection compares neighbouring pages (±1, ±2), as the pdf-editor viewer does.
 * - The pdf-editor code is not copied into this repository: its built packages (core, layout-recon) are imported at
 *   run time from the checkout given as the first argument (https://github.com/Juunary/pdf-editor, AGPL-3.0).
 * - Output rows: {page, kind: "paragraph", role, bbox, text} | {page, kind: "table", bbox, rows, cols, strategy, cells: [[text]]}
 *   | {page, kind: "figure", figureKind, bbox, labels}. The first row is {meta: {...}} (pages, pdf-editor commit, timing).
 * - Usage: node scripts/pdf_layout_export.mjs <pdf-editor checkout> <in.pdf> <out.jsonl>
 *
 * [KO]
 * - 역할: PDF 코퍼스의 오프라인 단계. 쪽마다 역할이 붙은 문단(본문·제목·목록·캡션·머리말·꼬리말·각주·기타), 행·열
 *   격자로 복원한 표, 그림을 복원된 읽기 순서대로 내보낸다. 머리·꼬리말은 pdf-editor 뷰어처럼 이웃 쪽(±1, ±2)과 비교해 찾는다.
 * - pdf-editor 코드는 이 저장소에 복사하지 않는다. 첫 번째 인자로 준 체크아웃의 빌드 결과(core, layout-recon)를 실행 시점에
 *   import 한다(https://github.com/Juunary/pdf-editor, AGPL-3.0).
 * - 사용: node scripts/pdf_layout_export.mjs <pdf-editor 체크아웃> <in.pdf> <out.jsonl>
 */
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [root, inPdf, outPath] = process.argv.slice(2);
if (!outPath) {
  console.error('usage: node scripts/pdf_layout_export.mjs <pdf-editor checkout> <in.pdf> <out.jsonl>');
  process.exit(2);
}
const { extractPageModel, openPdf } = await import(path.join(path.resolve(root), 'packages/core/dist/index.js'));
const { reconstructPage } = await import(path.join(path.resolve(root), 'packages/layout-recon/dist/index.js'));
const commit = execFileSync('git', ['-C', root, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();

const doc = openPdf(new Uint8Array(fs.readFileSync(inPdf)));
const n = doc.countPages();
// 쪽 추출 모델은 이웃 쪽 비교에 다시 쓰이므로 잠깐 보관한다 (현재 쪽에서 3쪽 이상 지난 것은 버림)
const models = new Map();
const model = (i) => {
  if (!models.has(i)) {
    const page = doc.loadPage(i);
    models.set(i, extractPageModel(page, { pageIndex: i, includePathSegments: true }));
    page.destroy();
  }
  return models.get(i);
};

const rows = [];
const warnings = [];
const t0 = performance.now();
for (let i = 0; i < n; i++) {
  const neighbors = [-2, -1, 1, 2].map((k) => i + k).filter((k) => k >= 0 && k < n).map(model);
  const layout = reconstructPage(model(i), { neighbors });
  if (layout.warnings.length) warnings.push({ page: i, warnings: layout.warnings });
  const para = new Map(layout.paragraphs.map((p) => [p.id, p]));
  const text = (id) => para.get(id)?.text ?? '';
  for (const ref of layout.readingOrder) {
    if (ref.kind === 'paragraph') {
      const p = para.get(ref.id);
      rows.push({ page: i, kind: 'paragraph', role: p.role, bbox: p.bbox, text: p.text });
    } else if (ref.kind === 'table') {
      const t = layout.tables.find((x) => x.id === ref.id);
      // 병합 셀은 왼쪽 위 칸에만 글자를 넣는다 (나머지 칸은 빈 문자열)
      const cells = Array.from({ length: t.rows }, () => Array(t.cols).fill(''));
      for (const c of t.cells) cells[c.row][c.col] = c.paragraphs.map(text).join(' ');
      rows.push({ page: i, kind: 'table', bbox: t.bbox, rows: t.rows, cols: t.cols, strategy: t.strategy, cells });
    } else {
      const f = layout.figures.find((x) => x.id === ref.id);
      rows.push({ page: i, kind: 'figure', figureKind: f.kind, bbox: f.bbox, labels: f.labels.map(text) });
    }
  }
  models.delete(i - 3);
}
doc.destroy();
const meta = { pages: n, pdfEditorCommit: commit, ms: Math.round(performance.now() - t0), warnings };
fs.writeFileSync(outPath, [JSON.stringify({ meta }), ...rows.map((r) => JSON.stringify(r))].join('\n') + '\n');
const count = (k) => rows.filter((r) => r.kind === k).length;
console.log(`${path.basename(inPdf)} pages=${n} paragraphs=${count('paragraph')} tables=${count('table')} figures=${count('figure')} ms=${meta.ms}`);
