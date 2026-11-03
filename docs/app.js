"use strict";
// 데이터: scripts/export_site_data.py가 만든 docs/data/*.json (실제 실행 기록)
const SETS = ["v2", "pdf", "user"];
const STATE = { lang: "ko", set: "v2", rows: {}, meta: null, chunks: null, idx: 0, list: [], playing: false, revealed: 0, speed: 1, cardHTML: {} };
let RUN = 0;                                  // 재생 세대 번호: 바뀌면 진행 중인 애니메이션을 멈춘다

const T = {
  ko: {
    title: "RAG 파이프라인 추적", subtitle: "질문 하나가 검색·생성·검증을 지나는 과정을 실제 실행 기록으로 보여줍니다.",
    pair: "언어쌍", show: "보기", question: "질문", play: "재생", pause: "일시정지", replay: "다시 재생", next_stage: "다음 단계 ›", show_all: "전체 보기", speed: "속도", stage_of: "단계", all: "전체",
    set_v2: "위키백과 질문", set_v2_s: "90개 · 청크 346개", set_pdf: "PDF 질문", set_pdf_s: "48개 · 청크 903개",
    set_user: "사람이 쓴 질문", set_user_s: "10개 · 청크 903개",
    k_all: "전체", k_missing: "정답 청크가 컨텍스트에 없음", k_blocked: "차단·거절된 답변",
    note_v2: "코퍼스: 위키백과 한·영·독 45건. 검색은 채팅 서버와 같은 구성(영어 BM25 + dense, RRF, 리랭커 영어 입력), 답변 프롬프트 cite_v1.",
    note_pdf: "코퍼스: 위키백과 + PDF 6건(NASA 보고서, 학위논문), 표 머리글 반복 청크. 검색은 영어 BM25 + 영어 dense, RRF, 리랭커 영어 입력, 답변 프롬프트 cite_v1.",
    note_user: "채점자가 문서를 보지 않고 쓴 실무 질문. PDF 질문과 같은 검색, 서비스 프롬프트 cite_refuse_v1(근거가 없으면 거절).",
    s_input: "입력 검증", s_translate: "질의 번역", s_retrieve: "후보 검색", s_rrf: "RRF 융합", s_rerank: "리랭커", s_generate: "생성", s_output: "출력 검증", s_answer: "답변",
    w_input: "빈 질문과 1000자를 넘는 질문을 걸러냅니다. 통과한 질문만 검색과 LLM을 부릅니다.",
    w_translate: "Qwen3-4B가 질문을 영어로 옮깁니다. 문서 조각도 미리 영어로 번역해 두었으므로, 한국어 질문으로 독일어 문서를 찾을 때도 영어끼리 비교합니다.",
    w_retrieve: "두 검색기가 각자 상위 50개 후보를 냅니다. BM25는 영어 번역문에서 단어 일치로, dense는 bge-m3 임베딩의 뜻 유사도(HNSW 근사 검색)로 찾습니다.",
    w_rrf: "점수가 아니라 순위만으로 두 목록을 합칩니다. 두 검색기에 모두 높게 나온 조각이 위로 올라오고, 상위 30개가 리랭커로 갑니다.",
    w_rerank: "bge-reranker-v2-m3가 (영어 질문, 영어 조각) 쌍을 한 쌍씩 읽고 다시 점수를 매깁니다. 상위 5개만 생성 모델에 들어갑니다.",
    w_generate: "Qwen3-4B-Instruct가 아래 5개 조각과 질문만 보고 답을 씁니다(greedy). 문장마다 근거 조각 ID를 [ ]로 붙이게 합니다.",
    w_output: "답변이 사용자에게 가기 전 마지막 관문입니다. 규칙에 걸리면 답변 대신 고정 문구를 보여줍니다.",
    w_answer: "출력 검증을 통과한 답변이 사용자에게 전달됩니다. 차단되면 답변 대신 고정 문구가 나갑니다.",
    delivered: "전달", fixed_msg: "고정 문구", raw_answer: "모델이 쓴 원래 답변 보기",
    pass: "통과", blocked: "차단", original: "원문", english: "영어", cached: "캐시에 저장된 원래 생성 시간",
    candidates: "후보", gold: "정답", gold_rank: "정답 청크 순위", out_of: "개 중", not_in: "위 밖", rank: "위",
    english_text: "영어 번역문", original_text: "원문", rrf_formula: "점수 = Σ 1 / (k + 검색기별 순위), k = ",
    to_gen: "여기까지 생성 모델에 전달", from_rrf: "RRF 순위 대비", context: "컨텍스트(상위 5)", prompt_tok: "프롬프트 토큰",
    out_tok: "생성 토큰", gen_time: "생성 시간", system_prompt: "시스템 프롬프트 보기",
    c_empty: "빈 답변이 아님", c_sentinel: "거절 신호 NO_ANSWER가 아님", c_refusal: "첫 문장이 거절 문장이 아님",
    c_valid: "인용한 ID가 모두 컨텍스트에 있음", c_has: "인용이 하나 이상 있음", not_checked: "앞 단계에서 차단되어 검사 안 함",
    cited_ids: "인용한 조각",
    r_refusal_sentinel: "거절 신호(NO_ANSWER)", r_refusal_text: "첫 문장이 거절", r_invalid_citation: "컨텍스트에 없는 ID 인용", r_no_citation: "인용 없음", r_empty_answer: "빈 답변",
    foot1: "단계 시간은 이 데이터를 만들 때 RTX 3080 Ti에서 검색을 다시 실행해 잰 값입니다. 번역·생성 시간은 처음 생성했을 때 저장한 값입니다.",
    foot2: "다시 실행한 검색의 상위 결과는 저장된 실험 결과와 148개 질문 모두 같습니다. 답변은 저장된 결과를 그대로 보여주며 이 페이지에서 새로 만들지 않습니다.",
    foot3: "모든 모델은 로컬에서 실행한 오픈소스 모델입니다.",
    foot4: "문서 출처: 위키백과(CC BY-SA 4.0), NASA 기술보고서(퍼블릭 도메인), 하노버대 학위논문(CC BY 3.0 DE), innoTRAC 논문(CC BY 4.0). 영어 번역문은 Qwen3-4B로 기계 번역했으며 원문과 같은 라이선스를 따릅니다. 문서별 출처는 저장소 README의 라이선스와 출처 절에 있습니다.",
    theme_auto: "자동", theme_light: "밝게", theme_dark: "어둡게", ms: "ms", s: "s",
  },
  en: {
    title: "RAG Pipeline Trace", subtitle: "One question at a time through retrieval, generation and validation, from real run records.",
    pair: "Language pair", show: "Show", question: "Question", play: "Play", pause: "Pause", replay: "Replay", next_stage: "Next stage ›", show_all: "Show all", speed: "Speed", stage_of: "stage", all: "All",
    set_v2: "Wikipedia questions", set_v2_s: "90 · 346 chunks", set_pdf: "PDF questions", set_pdf_s: "48 · 903 chunks",
    set_user: "Human-written questions", set_user_s: "10 · 903 chunks",
    k_all: "All", k_missing: "Gold chunk not in the context", k_blocked: "Blocked or refused",
    note_v2: "Corpus: 45 Wikipedia articles in Korean, English and German. Retrieval as in the chat server (English BM25 + dense, RRF, reranker on English text); answer prompt cite_v1.",
    note_pdf: "Corpus: Wikipedia + 6 PDFs (NASA reports, theses), table headers repeated in chunks. Retrieval: English BM25 + English dense, RRF, reranker on English text; answer prompt cite_v1.",
    note_user: "Practical questions written by the grader without looking at the documents. Same retrieval as the PDF set, serving prompt cite_refuse_v1 (refuses without evidence).",
    s_input: "Input check", s_translate: "Translation", s_retrieve: "Candidates", s_rrf: "RRF fusion", s_rerank: "Reranker", s_generate: "Generation", s_output: "Output check", s_answer: "Answer",
    w_input: "Rejects empty questions and questions over 1000 characters. Only questions that pass call retrieval and the LLM.",
    w_translate: "Qwen3-4B translates the question into English. The chunks were translated in advance, so a Korean question is matched against German documents in English.",
    w_retrieve: "Two retrievers return 50 candidates each: BM25 by word overlap on the English translations, dense by bge-m3 embedding similarity (HNSW approximate search).",
    w_rrf: "Merges the two lists by rank only, not score. Chunks ranked high by both rise; the top 30 go to the reranker.",
    w_rerank: "bge-reranker-v2-m3 reads each (English question, English chunk) pair and scores it again. Only the top 5 reach the generator.",
    w_generate: "Qwen3-4B-Instruct writes the answer from the 5 chunks below and the question only (greedy), citing a chunk id in [ ] after every sentence.",
    w_output: "The last gate before the user. An answer that breaks a rule is replaced by a fixed message.",
    w_answer: "An answer that passes the output check is delivered to the user. A blocked answer is replaced by a fixed message.",
    delivered: "delivered", fixed_msg: "fixed message", raw_answer: "Show the model's original answer",
    pass: "pass", blocked: "blocked", original: "Original", english: "English", cached: "original generation time stored in the cache",
    candidates: "candidates", gold: "gold", gold_rank: "Gold chunk rank", out_of: "", not_in: "not in top ", rank: "",
    english_text: "English translation", original_text: "original text", rrf_formula: "score = Σ 1 / (k + rank in each retriever), k = ",
    to_gen: "passed to the generator", from_rrf: "vs. RRF rank", context: "Context (top 5)", prompt_tok: "Prompt tokens",
    out_tok: "Generated tokens", gen_time: "Generation time", system_prompt: "Show system prompt",
    c_empty: "answer is not empty", c_sentinel: "not the refusal sentinel NO_ANSWER", c_refusal: "first sentence is not a refusal",
    c_valid: "every cited id was in the context", c_has: "at least one citation", not_checked: "not checked (blocked earlier)",
    cited_ids: "Cited chunks",
    r_refusal_sentinel: "refusal sentinel (NO_ANSWER)", r_refusal_text: "first sentence is a refusal", r_invalid_citation: "cites an id not in the context", r_no_citation: "no citation", r_empty_answer: "empty answer",
    foot1: "Stage times were measured when this data was exported, by running retrieval again on an RTX 3080 Ti. Translation and generation times are the values stored when they were first generated.",
    foot2: "The re-run retrieval matches the stored experiment results for all 148 questions. Answers are shown as stored; nothing is generated on this page.",
    foot3: "All models are open-source models run locally.",
    foot4: "Sources: Wikipedia (CC BY-SA 4.0), NASA technical reports (public domain), Leibniz University Hannover theses (CC BY 3.0 DE), an innoTRAC article (CC BY 4.0). English translations are machine translations by Qwen3-4B under the license of the original. Per-document sources are in the license and sources section of the repository README.",
    theme_auto: "Auto", theme_light: "Light", theme_dark: "Dark", ms: "ms", s: "s",
  },
};
const STAGES = ["input", "translate", "retrieve", "rrf", "rerank", "generate", "output", "answer"];
const CITE = /\[([A-Za-z0-9_.\-]+#\d+)\]/g;

const $ = (s) => document.querySelector(s);
const t = (k) => T[STATE.lang][k] ?? k;
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (x, d = 2) => (x == null ? "-" : Number(x).toFixed(d));
const ms = (x) => (x < 1 ? `${fmt(x, 2)} ${t("ms")}` : x < 100 ? `${fmt(x, 1)} ${t("ms")}` : `${fmt(x, 0)} ${t("ms")}`);
function rankLabel(r, n) {
  if (STATE.lang === "ko") return r == null ? `${n}위 밖` : `${r}위`;
  return r == null ? `not in top ${n}` : `#${r}`;
}

async function getJSON(p) { const r = await fetch(p); if (!r.ok) throw new Error(p); return r.json(); }

async function init() {
  let saved = null;
  try { saved = localStorage.getItem("lang"); } catch {}
  STATE.lang = saved === "ko" || saved === "en" ? saved : ((navigator.language || "ko").startsWith("ko") ? "ko" : "en");
  applyTheme(readTheme());
  [STATE.meta, STATE.chunks] = await Promise.all([getJSON("data/meta.json"), getJSON("data/chunks.json")]);
  await Promise.all(SETS.map(async (s) => { STATE.rows[s] = await getJSON(`data/${s}.json`); }));
  const h = new URLSearchParams(location.hash.slice(1));
  if (SETS.includes(h.get("set"))) STATE.set = h.get("set");
  bind();
  renderStatic();
  buildList(h.get("q"));
}

function readTheme() { try { return localStorage.getItem("theme") || "auto"; } catch { return "auto"; } }
function applyTheme(m) {
  if (m === "auto") document.documentElement.removeAttribute("data-theme"); else document.documentElement.setAttribute("data-theme", m);
  STATE.theme = m;
  $("#theme-btn").textContent = "◐ " + t(`theme_${m}`);
}

function bind() {
  $("#lang-btn").onclick = () => { STATE.lang = STATE.lang === "ko" ? "en" : "ko"; try { localStorage.setItem("lang", STATE.lang); } catch {} renderStatic(); buildList(cur()?.qid); };
  $("#theme-btn").onclick = () => { const order = ["auto", "light", "dark"]; const m = order[(order.indexOf(STATE.theme) + 1) % 3]; try { localStorage.setItem("theme", m); } catch {} applyTheme(m); };
  $("#f-pair").onchange = () => buildList(cur()?.qid);
  $("#f-kind").onchange = () => buildList(cur()?.qid);
  $("#f-q").onchange = (e) => { STATE.idx = Number(e.target.value); show(); };
  $("#prev").onclick = () => step(-1);
  $("#next").onclick = () => step(1);
  $("#p-play").onclick = () => {
    if (STATE.playing) return cancel();
    if (STATE.revealed >= STAGES.length) return restart();
    run(STATE.revealed, false);
  };
  $("#p-next").onclick = () => { cancel(); if (STATE.revealed < STAGES.length) run(STATE.revealed, true); };
  $("#p-all").onclick = () => { cancel(); for (let i = STATE.revealed; i < STAGES.length; i++) revealNow(i); syncPlayer(); };
  $("#p-restart").onclick = () => restart();
  $("#p-speed").onchange = (e) => { STATE.speed = Number(e.target.value); };
  document.addEventListener("click", (e) => { const b = e.target.closest("[data-cid]"); if (b) openChunk(b.dataset.cid); });
  // 공유 링크(#set=..&q=..)로 들어오거나 주소창의 해시만 바뀐 경우
  window.addEventListener("hashchange", () => {
    const h = new URLSearchParams(location.hash.slice(1));
    const s = SETS.includes(h.get("set")) ? h.get("set") : STATE.set;
    if (s === STATE.set && h.get("q") === cur()?.qid) return;
    STATE.set = s; $("#f-pair").value = ""; $("#f-kind").value = "all";
    renderStatic(); buildList(h.get("q"));
  });
  document.addEventListener("keydown", (e) => {
    if (e.target.matches("select, input, textarea") || $("#chunk-dialog").open) return;
    if (e.key === "ArrowRight") step(1); if (e.key === "ArrowLeft") step(-1);
  });
}

function renderStatic() {
  document.documentElement.lang = STATE.lang;
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.title = t("title");
  $("#lang-btn").textContent = STATE.lang === "ko" ? "EN" : "KO";
  applyTheme(STATE.theme);
  if (STATE.list.length) syncPlayer();
  $("#set-tabs").innerHTML = SETS.map((s) => `<button class="tab" role="tab" aria-selected="${s === STATE.set}" data-set="${s}">${esc(t("set_" + s))}<small>${esc(t("set_" + s + "_s"))}</small></button>`).join("");
  document.querySelectorAll(".tab").forEach((b) => (b.onclick = () => { STATE.set = b.dataset.set; $("#f-pair").value = ""; $("#f-kind").value = "all"; renderStatic(); buildList(); }));
  $("#set-note").textContent = t("note_" + STATE.set);
  const rows = STATE.rows[STATE.set];
  const pairs = [...new Set(rows.map((r) => r.group))].sort();
  const pv = $("#f-pair").value;
  $("#f-pair").innerHTML = `<option value="">${esc(t("all"))}</option>` + pairs.map((p) => `<option ${p === pv ? "selected" : ""}>${esc(p)}</option>`).join("");
  $("#f-pair").disabled = pairs.length < 2;
  const kinds = ["all", "missing", "blocked"].filter((k) => STATE.set !== "user" || k !== "missing");
  const kv = $("#f-kind").value || "all";
  $("#f-kind").innerHTML = kinds.map((k) => `<option value="${k}" ${k === kv ? "selected" : ""}>${esc(t("k_" + k))}</option>`).join("");
  $("#foot").innerHTML = `<p>${esc(t("foot1"))}</p><p>${esc(t("foot2"))}</p><p>${esc(t("foot3"))}</p><p>${esc(t("foot4"))}</p>
    <p><code>${esc(STATE.meta.sets[STATE.set].config)}</code> · <code>${esc(STATE.meta.sets[STATE.set].answers)}</code> · <code>scripts/export_site_data.py</code></p>`;
}

function matches(r, kind) {
  const inCtx = Object.keys(r.gold).some((g) => r.context_ids.includes(g));
  if (kind === "missing") return Object.keys(r.gold).length > 0 && !inCtx;
  if (kind === "blocked") return !r.output.ok;
  return true;
}

function buildList(keepQid) {
  const rows = STATE.rows[STATE.set];
  const pair = $("#f-pair").value, kind = $("#f-kind").value || "all";
  STATE.list = rows.filter((r) => (!pair || r.group === pair) && matches(r, kind));
  const sel = $("#f-q");
  sel.innerHTML = STATE.list.length
    ? STATE.list.map((r, i) => `<option value="${i}">${esc(r.qid)} · ${esc(r.question.length > 70 ? r.question.slice(0, 70) + "…" : r.question)}</option>`).join("")
    : `<option>-</option>`;
  const k = STATE.list.findIndex((r) => r.qid === keepQid);
  STATE.idx = k >= 0 ? k : 0;
  sel.value = String(STATE.idx);
  show();
}

const cur = () => STATE.list[STATE.idx];
function step(d) { if (!STATE.list.length) return; STATE.idx = (STATE.idx + d + STATE.list.length) % STATE.list.length; $("#f-q").value = String(STATE.idx); show(); }

function show() {
  cancel();
  const r = cur();
  if (!r) { $("#question-card").innerHTML = `<p class="empty">-</p>`; $("#flow").innerHTML = ""; $("#stages").innerHTML = ""; return; }
  history.replaceState(null, "", `#set=${STATE.set}&q=${encodeURIComponent(r.qid)}`);
  renderQuestion(r);
  renderFlow(r);
  renderStages(r);
  STATE.revealed = 0;
  syncPlayer();
  // 움직임 줄이기 설정이면 바로 전부 보여 주고, 아니면 처음 단계부터 자동 재생한다
  if (reduced()) { for (let i = 0; i < STAGES.length; i++) revealNow(i); syncPlayer(); } else run(0, false);
}

const isGold = (r, cid) => Object.prototype.hasOwnProperty.call(r.gold, cid);
const cidBtn = (r, cid) => `<button class="cid" data-cid="${esc(cid)}" title="${esc(STATE.chunks[cid]?.title || "")}">${isGold(r, cid) ? `<span class="star" aria-label="${esc(t("gold"))}">★</span>` : ""}${esc(cid)}</button>`;

function renderQuestion(r) {
  const pills = [`<span class="pill">${esc(r.qid)}</span>`, `<span class="pill">${esc(r.group)}</span>`];
  if (r.evidence_kind) pills.push(`<span class="pill">${esc(r.evidence_kind)}</span>`);
  if (Object.keys(r.gold).length) pills.push(`<span class="pill gold">★ ${esc(t("gold"))} ${Object.keys(r.gold).length}</span>`);
  $("#question-card").innerHTML = `<div class="q-meta">${pills.join("")}</div><p class="q-text">${esc(r.question)}</p>`;
}

function nodeVal(r, s) {
  const st = r.stages, m = STATE.meta.sets[STATE.set];
  switch (s) {
    case "input": return st.input.ok ? t("pass") : t("blocked");
    case "translate": return `${fmt(st.translation.seconds, 2)} ${t("s")}`;
    case "retrieve": return `${m.n_chunks} → ${st.parts.map((p) => p.n).join(" + ")}`;
    case "rrf": return `→ ${st.rrf.n}`;
    case "rerank": return `${st.rerank.n} → ${m.retrieval.context_k}`;
    case "generate": return r.gen ? `${fmt(r.gen.seconds, 1)} ${t("s")}` : m.prompt;
    case "output": return r.output.ok ? t("pass") : t("blocked");
    case "answer": return r.output.ok ? t("delivered") : t("fixed_msg");
  }
}

function renderFlow(r) {
  $("#flow").innerHTML = STAGES.map((s, i) => {
    const blocked = (s === "output" && !r.output.ok) || (s === "input" && !r.stages.input.ok);
    return `<button class="node${blocked ? " blocked" : ""}" data-stage="${s}" type="button"><span class="n-step">${i + 1}</span><span class="n-name">${esc(t("s_" + s))}</span><span class="n-val">${esc(nodeVal(r, s))}</span></button>`;
  }).join("");
  // 노드를 누르면 그 단계까지 바로 펼치고 그 단계로 이동한다
  document.querySelectorAll(".node").forEach((n, i) => (n.onclick = () => {
    cancel();
    for (let k = STATE.revealed; k <= i; k++) revealNow(k);
    mark(STATE.revealed - 1, false); syncPlayer(); scrollToStage(i, true);
  }));
}

function card(s, i, timing, body) {
  return `<article class="stage" data-stage="${s}" id="stage-${s}" hidden><div class="stage-head"><h2><span class="num">${i + 1}</span>${esc(t("s_" + s))}</h2>${timing ? `<span class="timing">${timing}</span>` : ""}</div><p class="what">${esc(t("w_" + s))}</p>${body}</article>`;
}

function scoreRows(r, hits, color, opts = {}) {
  const sc = hits.map((h) => h[1]);
  const lo = Math.min(...sc), hi = Math.max(...sc);
  return hits.map((h, i) => {
    const w = hi > lo ? 12 + 88 * (h[1] - lo) / (hi - lo) : 100;
    const mv = opts.prev ? movement(opts.prev[h[0]], i + 1) : "";
    const row = `<li class="rank-row${opts.prev ? " wide" : ""}${isGold(r, h[0]) ? " is-gold" : ""}"><span class="r">${i + 1}</span>${cidBtn(r, h[0])}<span class="bar" title="${fmt(h[1], 4)}"><span style="width:${w}%;background:${color}"></span></span><span class="s">${fmt(h[1], opts.digits ?? 3)}</span>${opts.prev ? `<span class="mv prov">${mv}</span>` : ""}</li>`;
    return (opts.cutAt && i === opts.cutAt) ? `<li class="cut">${esc(t("to_gen"))} ↑</li>${row}` : row;
  }).join("");
}
function movement(prev, now) {
  if (prev == null) return "";
  const d = prev - now;
  return d > 0 ? `▲${d}` : d < 0 ? `▼${-d}` : "=";
}

function goldLine(r, gr, n) {
  const ids = Object.keys(r.gold);
  if (!ids.length) return "";
  return `<div class="gold-line">★ ${esc(t("gold_rank"))}: ${ids.map((g) => `<span class="pill gold">${esc(g)} → ${esc(rankLabel(gr[g], n))}</span>`).join(" ")}</div>`;
}

function renderStages(r) {
  const st = r.stages, m = STATE.meta.sets[STATE.set];
  const out = [];
  // 1. 입력 검증
  out.push(card("input", 0, ms(st.input.ms), `<ul class="checks"><li><span class="ic ${st.input.ok ? "ok" : "no"}">${st.input.ok ? "✓" : "✕"}</span>${esc(st.input.ok ? `${t("pass")} · ${r.question.length} / 1000` : st.input.reason)}</li></ul>`));
  // 2. 번역
  out.push(card("translate", 1, `${fmt(st.translation.seconds, 2)} ${t("s")} · ${esc(t("cached"))}`,
    `<div class="translate-row"><div class="tbox"><small>${esc(t("original"))} · ${esc(r.q_lang)}</small>${esc(r.question)}</div><span class="arrow" aria-hidden="true">→</span><div class="tbox"><small>${esc(t("english"))}</small>${esc(st.translation.text)}</div></div>`));
  // 3. 후보 검색
  const colors = { bm25: "var(--s-bm25)", dense: "var(--s-dense)" };
  out.push(card("retrieve", 2, st.parts.map((p) => `${esc(p.label)} ${ms(p.ms)}`).join(" · "),
    `<div class="cols">${st.parts.map((p) => `<div><div class="col-title"><span class="swatch" style="background:${colors[p.kind]}"></span>${esc(p.label)} · ${esc(p.english ? t("english_text") : t("original_text"))} · ${p.n} ${esc(t("candidates"))}</div><ol class="rank-list">${scoreRows(r, p.hits, colors[p.kind], { digits: p.kind === "bm25" ? 2 : 3 })}</ol>${goldLine(r, p.gold_rank, p.n)}</div>`).join("")}</div>`));
  // 4. RRF
  const k = st.rrf.k, maxTot = st.parts.length / (k + 1);
  const rrfRows = st.rrf.hits.slice(0, 10).map((h, i) => {
    const segs = st.parts.map((p) => {
      const rk = h[2][p.name];
      return rk ? `<span style="width:${(100 * (1 / (k + rk)) / maxTot).toFixed(1)}%;background:${colors[p.kind]}" title="${esc(p.label)} ${rk}"></span>` : "";
    }).join("");
    const prov = st.parts.map((p) => `${p.kind === "bm25" ? "B" : "D"}${h[2][p.name] ?? "–"}`).join(" ");
    return `<li class="rank-row wide${isGold(r, h[0]) ? " is-gold" : ""}"><span class="r">${i + 1}</span>${cidBtn(r, h[0])}<span class="bar">${segs}</span><span class="s">${fmt(h[1], 4)}</span><span class="mv prov">${prov}</span></li>`;
  }).join("");
  out.push(card("rrf", 3, ms(st.rrf.ms),
    `<div class="formula">${esc(t("rrf_formula"))}${k}</div><div class="legend">${st.parts.map((p) => `<span><span class="swatch" style="background:${colors[p.kind]}"></span>${esc(p.label)} (${p.kind === "bm25" ? "B" : "D"} = ${esc(STATE.lang === "ko" ? "순위" : "rank")})</span>`).join("")}</div><ol class="rank-list">${rrfRows}</ol>${goldLine(r, st.rrf.gold_rank, st.rrf.n)}`));
  // 5. 리랭커
  const prev = Object.fromEntries(st.rrf.hits.map((h, i) => [h[0], i + 1]));
  out.push(card("rerank", 4, ms(st.rerank.ms),
    `<div class="legend"><span><span class="swatch" style="background:var(--s-rerank)"></span>${esc(m.retrieval.rerank_model)}</span><span>▲▼ ${esc(t("from_rrf"))}</span></div><ol class="rank-list">${scoreRows(r, st.rerank.hits, "var(--s-rerank)", { prev, cutAt: m.retrieval.context_k })}</ol>${goldLine(r, st.rerank.gold_rank, st.rerank.n)}`));
  // 6. 생성
  const gen = r.gen ? `<dl class="kv"><dt>${esc(t("prompt_tok"))}</dt><dd>${r.gen.prompt_tokens}</dd><dt>${esc(t("out_tok"))}</dt><dd>${r.gen.completion_tokens}</dd><dt>${esc(t("gen_time"))}</dt><dd>${fmt(r.gen.seconds, 2)} ${t("s")}</dd></dl>` : "";
  const ctx = `<div class="col-title">${esc(t("context"))}</div><div class="ctx-list">${r.context_ids.map((c) => `<button class="ctx${isGold(r, c) ? " gold" : ""}" data-cid="${esc(c)}">${isGold(r, c) ? "★ " : ""}${esc(c)}</button>`).join("")}</div>`;
  out.push(card("generate", 5, r.gen ? `${fmt(r.gen.seconds, 2)} ${t("s")} · ${esc(m.prompt)}` : esc(m.prompt),
    `${ctx}${gen}<details><summary>${esc(t("system_prompt"))} (${esc(m.prompt)})</summary><pre class="sys">${esc(STATE.meta.prompts[m.prompt])}\n\nContext:\n\n[${esc(r.context_ids[0])}] …\n…\n\nQuestion: ${esc(r.question)}</pre></details>`));
  // 7. 출력 검증
  out.push(card("output", 6, "", renderChecks(r)));
  // 8. 답변: 사용자에게 실제로 전달되는 글 (차단되면 고정 문구, 모델 원문은 접어 둔다)
  out.push(card("answer", 7, "", renderDelivered(r)));
  $("#stages").innerHTML = out.join("");
  // 애니메이션은 DOM을 바꾸므로, 멈추거나 건너뛸 때 되돌릴 최종 모습을 단계별로 저장해 둔다
  STATE.cardHTML = {};
  document.querySelectorAll(".stage").forEach((c) => { STATE.cardHTML[c.dataset.stage] = c.innerHTML; });
}

const SAFE = {
  ko: "제공된 문서에서 이 질문에 답할 근거를 찾지 못했습니다.",
  en: "I could not find supporting evidence for this question in the provided documents.",
  de: "Für diese Frage habe ich in den vorliegenden Dokumenten keine Belege gefunden.",
};

function renderDelivered(r) {
  if (r.output.ok) return `<div class="answer final">${renderAnswer(r)}</div>`;
  // 서비스 경로(사람이 쓴 질문)는 저장된 답변이 이미 고정 문구이고 모델 원문은 NO_ANSWER다
  const shown = STATE.set === "user" ? r.answer : SAFE[r.q_lang] || SAFE.en;
  const raw = STATE.set === "user" ? (r.output.reason === "refusal_sentinel" ? "NO_ANSWER" : "") : r.answer;
  return `<div class="answer final blocked">${esc(shown)}</div>` +
    (raw ? `<details><summary>${esc(t("raw_answer"))} · ${esc(t("r_" + r.output.reason))}</summary><pre class="sys">${raw === r.answer ? renderAnswer(r) : esc(raw)}</pre></details>` : "");
}

function renderAnswer(r) {
  return esc(r.answer).replace(CITE, (_, id) => `<button class="cite${isGold(r, id) ? " gold" : ""}" data-cid="${id}">${isGold(r, id) ? "★ " : ""}${id}</button>`);
}

function renderChecks(r) {
  const rules = [["empty_answer", "c_empty"], ["refusal_sentinel", "c_sentinel"], ["refusal_text", "c_refusal"], ["invalid_citation", "c_valid"], ["no_citation", "c_has"]];
  const failAt = r.output.ok ? -1 : rules.findIndex(([reason]) => reason === r.output.reason);
  const items = rules.map(([, key], i) => {
    const state = failAt === -1 || i < failAt ? "ok" : i === failAt ? "no" : "na";
    const icon = { ok: "✓", no: "✕", na: "–" }[state];
    return `<li><span class="ic ${state}">${icon}</span><span>${esc(t(key))}${state === "na" ? ` <span class="empty">(${esc(t("not_checked"))})</span>` : ""}</span></li>`;
  }).join("");
  const verdict = r.output.ok ? `<span class="pill good">✓ ${esc(t("pass"))}</span>` : `<span class="pill bad">✕ ${esc(t("blocked"))} · ${esc(t("r_" + r.output.reason))}</span>`;
  const cited = r.output.cited.length ? `<div class="gold-line">${esc(t("cited_ids"))}: ${r.output.cited.map((c) => cidBtn(r, c)).join(", ")}</div>` : "";
  return `<ul class="checks">${items}</ul><div class="reveal" style="margin-top:10px">${verdict}</div>${cited}`;
}

function openChunk(cid) {
  const c = STATE.chunks[cid];
  if (!c) return;
  $("#dlg-id").textContent = cid;
  $("#dlg-title").textContent = `${c.title} · ${c.lang}`;
  const tabs = [["text", t("original_text")]];
  if (c.en) tabs.push(["en", t("english_text")]);
  const set = (k) => { $("#dlg-text").textContent = c[k]; document.querySelectorAll("#dlg-tabs .chip-btn").forEach((b) => b.setAttribute("aria-pressed", b.dataset.k === k)); };
  $("#dlg-tabs").innerHTML = tabs.length > 1 ? tabs.map(([k, l]) => `<button class="chip-btn" type="button" data-k="${k}">${esc(l)}</button>`).join("") : "";
  document.querySelectorAll("#dlg-tabs .chip-btn").forEach((b) => (b.onclick = () => set(b.dataset.k)));
  set("text");
  $("#chunk-dialog").showModal();
}

// ---------- 재생: 단계를 하나씩 펼치고 단계 안의 움직임을 순서대로 보여 준다 ----------
const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const sleep = (ms) => new Promise((res) => setTimeout(res, ms / STATE.speed));
const stageEl = (i) => document.querySelector(`.stage[data-stage="${STAGES[i]}"]`);

function syncPlayer() {
  const n = STATE.revealed, done = n >= STAGES.length;
  $("#p-play").innerHTML = STATE.playing ? `❚❚ ${esc(t("pause"))}` : done ? `↺ ${esc(t("replay"))}` : `▶ ${esc(t("play"))}`;
  $("#p-play").setAttribute("aria-pressed", String(STATE.playing));
  $("#p-next").textContent = t("next_stage");
  $("#p-all").textContent = t("show_all");
  $("#p-speed-l").textContent = t("speed");
  $("#p-next").disabled = done; $("#p-all").disabled = done;
  const curStage = Math.max(0, Math.min(n, STAGES.length) - 1);
  $("#p-progress").textContent = n ? (STATE.lang === "ko" ? `${n} / ${STAGES.length} ${t("stage_of")} · ${t("s_" + STAGES[curStage])}` : `${t("stage_of")} ${n} / ${STAGES.length} · ${t("s_" + STAGES[curStage])}`) : "";
}

function mark(i, running) {
  document.querySelectorAll(".node").forEach((nd, k) => {
    nd.classList.toggle("done", k < i || (k === i && !running));
    nd.classList.toggle("active", k === i && running);
    nd.classList.toggle("todo", k > i);
  });
  document.querySelectorAll(".stage").forEach((c, k) => c.classList.toggle("active", k === i));
}

function scrollToStage(i, always) {
  const el = stageEl(i);
  if (!el) return;
  const r = el.getBoundingClientRect();
  if (always || r.top > innerHeight * 0.55 || r.top < 0) el.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" });
}

function restore(el) {
  el.innerHTML = STATE.cardHTML[el.dataset.stage];
  el.classList.remove("anim", "enter", "no-tr");
}

function revealNow(i) {
  const el = stageEl(i);
  if (!el) return;
  restore(el);
  el.hidden = false;
  STATE.revealed = Math.max(STATE.revealed, i + 1);
  mark(Math.min(STATE.revealed, STAGES.length) - 1, false);
}

function cancel() {
  RUN += 1;
  STATE.playing = false;
  // 애니메이션 도중이던 카드는 최종 모습으로 되돌린다
  document.querySelectorAll(".stage.anim").forEach(restore);
  if (document.querySelector(".node")) mark(Math.max(0, STATE.revealed - 1), false);
  syncPlayer();
}

function restart() {
  cancel();
  document.querySelectorAll(".stage").forEach((c) => { restore(c); c.hidden = true; });
  STATE.revealed = 0;
  scrollTo({ top: $("#question-card").offsetTop - 8, behavior: reduced() ? "auto" : "smooth" });
  run(0, false);
}

async function run(from, single) {
  const id = ++RUN;
  STATE.playing = !single;
  syncPlayer();
  for (let i = from; i < STAGES.length; i++) {
    const el = stageEl(i);
    restore(el);
    el.hidden = false;
    STATE.revealed = i + 1;
    mark(i, true);
    syncPlayer();
    el.classList.add("anim", "enter");
    scrollToStage(i, false);
    await (ANIM[STAGES[i]] || (() => sleep(400)))(el, id);
    if (id !== RUN) return;
    el.classList.remove("anim", "enter");
    mark(i, false);
    if (single) break;
    await sleep(700);
    if (id !== RUN) return;
  }
  STATE.playing = false;
  syncPlayer();
}

// 요소를 처음 상태(숨김, 막대 0)로 바꿔 두는 준비 단계: 전환 없이 즉시 적용한다
function prep(el, hideSel) {
  el.classList.add("no-tr");
  el.querySelectorAll(hideSel).forEach((x) => x.classList.add("pre"));
  el.querySelectorAll(".bar > span").forEach((b) => { b.dataset.w = b.style.width; b.style.width = "0"; });
  void el.offsetHeight;
  el.classList.remove("no-tr");
}
const showEl = (x, pop) => { if (!x) return; x.classList.remove("pre"); if (pop) x.querySelector(".ic, .star")?.classList.add("popin"); };
const grow = (scope) => scope.querySelectorAll(".bar > span").forEach((b) => { b.style.width = b.dataset.w; });

async function typeText(node, text, id, maxMs) {
  const tick = 22, per = Math.max(1, Math.ceil(text.length / (maxMs / tick)));
  for (let k = 0; k < text.length; k += per) {
    if (id !== RUN) return;
    node.textContent = text.slice(0, k + per);
    await sleep(tick);
  }
}

const ANIM = {
  async input(el, id) {
    prep(el, ".checks li");
    await sleep(300); if (id !== RUN) return;
    showEl(el.querySelector(".checks li"), true);
    await sleep(500);
  },
  async translate(el, id) {
    const box = el.querySelectorAll(".tbox")[1];
    const node = box.lastChild, full = node.textContent;
    node.textContent = "";
    await sleep(350); if (id !== RUN) return;
    el.querySelector(".arrow")?.classList.add("flow-on");
    box.classList.add("typing");
    await sleep(500); if (id !== RUN) return;
    await typeText(node, full, id, 1400);
    box.classList.remove("typing");
    await sleep(300);
  },
  async retrieve(el, id) {
    prep(el, ".rank-row, .gold-line");
    const cols = [...el.querySelectorAll(".cols > div")];
    await sleep(300);
    for (let k = 0; k < 10; k++) {
      if (id !== RUN) return;
      cols.forEach((c) => { const row = c.querySelectorAll(".rank-row")[k]; if (row) { showEl(row, true); grow(row); } });
      await sleep(110);
    }
    await sleep(350); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async rrf(el, id) {
    prep(el, ".rank-row, .gold-line");
    el.querySelectorAll(".bar").forEach((b) => b.classList.add("seq"));
    await sleep(400);
    for (const row of el.querySelectorAll(".rank-row")) {
      if (id !== RUN) return;
      showEl(row, true); grow(row);
      await sleep(150);
    }
    await sleep(500); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async rerank(el, id) {
    // RRF 순서로 먼저 세운 뒤 리랭커 점수 순서로 움직여 재정렬한다 (FLIP)
    prep(el, ".mv, .cut, .gold-line");
    const rr = STATE.list[STATE.idx].stages.rrf.hits;
    const rrfRank = Object.fromEntries(rr.map((h, k) => [h[0], k + 1]));
    const rows = [...el.querySelectorAll(".rank-row")];
    const tops = rows.map((row) => row.offsetTop);
    const h = rows[0].offsetHeight;
    el.classList.add("no-tr");
    rows.forEach((row, k) => {
      const cid = row.querySelector("[data-cid]").dataset.cid, r0 = rrfRank[cid];
      const target = r0 <= rows.length ? tops[r0 - 1] : tops[rows.length - 1] + 1.5 * h;
      row.style.transform = `translateY(${target - tops[k]}px)`;
      if (r0 > rows.length) row.style.opacity = "0";
      const rc = row.querySelector(".r"); rc.dataset.final = rc.textContent; rc.textContent = r0; rc.classList.add("old");
    });
    void el.offsetHeight;
    el.classList.remove("no-tr");
    await sleep(1100); if (id !== RUN) return;
    rows.forEach((row) => { row.classList.add("flip"); row.style.transform = ""; row.style.opacity = ""; const rc = row.querySelector(".r"); rc.textContent = rc.dataset.final; rc.classList.remove("old"); });
    await sleep(1000); if (id !== RUN) return;
    for (const row of rows) { grow(row); await sleep(60); if (id !== RUN) return; }
    await sleep(350);
    el.querySelectorAll(".mv").forEach((m) => showEl(m));
    await sleep(350); if (id !== RUN) return;
    showEl(el.querySelector(".cut"));
    await sleep(400); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async generate(el, id) {
    prep(el, ".ctx, .kv, details");
    await sleep(300);
    for (const c of el.querySelectorAll(".ctx")) { if (id !== RUN) return; showEl(c); c.classList.add("popin"); await sleep(180); }
    await sleep(300); if (id !== RUN) return;
    el.querySelectorAll(".kv").forEach((k) => showEl(k));
    await sleep(400); if (id !== RUN) return;
    showEl(el.querySelector("details"));
    await sleep(500);
  },
  async output(el, id) {
    prep(el, ".checks li, .reveal, .gold-line");
    await sleep(300);
    for (const li of el.querySelectorAll(".checks li")) { if (id !== RUN) return; showEl(li, true); await sleep(330); }
    await sleep(200); if (id !== RUN) return;
    el.querySelectorAll(".reveal").forEach((x) => { showEl(x); x.querySelector(".pill")?.classList.add("popin"); });
    await sleep(300); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async answer(el, id) {
    // 답변을 타자 치듯 출력하고, 인용 칩은 통째로 튀어나오게 한다
    prep(el, "details");
    const ans = el.querySelector(".answer");
    const parts = [...ans.childNodes];
    ans.innerHTML = "";
    ans.classList.add("typing");
    await sleep(400);
    const total = parts.reduce((a, n) => a + (n.nodeType === 3 ? n.textContent.length : 0), 0);
    const budget = Math.min(3200, 600 + total * 12);
    for (const n of parts) {
      if (id !== RUN) return;
      if (n.nodeType === 3) {
        const tn = document.createTextNode("");
        ans.appendChild(tn);
        await typeText(tn, n.textContent, id, budget * n.textContent.length / Math.max(1, total));
      } else { n.classList.add("popin"); ans.appendChild(n); await sleep(120); }
    }
    ans.classList.remove("typing");
    await sleep(300); if (id !== RUN) return;
    showEl(el.querySelector("details"));
    await sleep(300);
  },
};

init().catch((e) => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p class="empty">Failed to load data: ${esc(e.message)}</p>`); });
