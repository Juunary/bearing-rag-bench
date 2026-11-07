"use strict";
// 데이터: scripts/export_site_data.py가 만든 docs/data/*.json (실제 실행 기록)
const SETS = ["v2", "pdf", "okf", "service"];
// trace = 파이프라인 추적(재생), chunking = PDF 문서가 청크가 되는 과정(정적), okf = 지식 번들 페이지(정적)와 번들 전용 질문(재생)
const KIND = { v2: "trace", pdf: "chunking", okf: "okf", service: "trace" };
const STATE = { lang: "ko", set: "v2", view: "q", rows: {}, meta: null, chunks: null, pdfdocs: [], pdfmeta: null, okf: null, pdfChunks: null, idx: 0, list: [], playing: false, revealed: 0, speed: 1, cardHTML: {}, waiting: true };   // waiting: 첫 재생 전 대기 (3초 무조작 또는 아래로 스크롤하면 시작); view: okf 세트에서 q(질문) | pages(페이지)
let RUN = 0;                                  // 재생 세대 번호: 바뀌면 진행 중인 애니메이션을 멈춘다

const T = {
  ko: {
    title: "RAG 파이프라인 추적", subtitle: "실제 실행 기록으로 보여줍니다: 질문 하나가 검색·생성·검증을 지나는 과정, PDF 문서가 청크가 되는 과정, OKF 지식 번들 페이지와 번들 전용 답변의 사람 채점.",
    pair: "언어쌍", show: "보기", question: "질문", wheel_hint: "휠 ↓ 짧게: 다음 단계 · 길게 또는 ↑: 전체 보기", wait_hint: "3초 뒤 또는 아래로 스크롤하면 재생을 시작합니다", play: "재생", pause: "일시정지", replay: "다시 재생", next_stage: "다음 단계 ›", show_all: "전체 보기", speed: "속도", stage_of: "단계", all: "전체",
    set_v2: "위키백과 질문", set_v2_s: "90개 · 청크 346개", set_pdf: "PDF 문서 → 청크", set_pdf_s: "문서 6건 · 청크 557개",
    set_okf: "OKF 지식 번들", set_okf_s: "페이지 24쪽 · 질문 40개", set_service: "서비스 (지식 번들)", set_service_s: "50개 · 번들 24쪽 + 청크 903개",
    k_all: "전체", k_missing: "정답 청크가 컨텍스트에 없음", k_blocked: "차단·거절된 답변",
    k_r1: "1차 (12쪽 전부)", k_r2: "2차 (24쪽, 매칭 쪽만)", k_correct: "맞음", k_partial: "부분", k_wrong: "틀림", k_refuse_ok: "거절 (적절)", k_refuse_bad: "거절 (부적절)", k_nomatch: "매칭 없음",
    doc: "문서", page: "페이지", target: "대상", okf_questions: "질문 40개", okf_pages: "페이지 24쪽",
    note_pdf: "PDF 6건이 청크 557개가 되는 과정입니다(질문·검색 없음). pdf-editor의 레이아웃 복원으로 읽기 순서의 블록을 얻고, 머리말·꼬리말·그림 글자·목차 줄·참고문헌 절을 버린 뒤, 제목으로 절을 나누고, bge-m3 토크나이저 기준 384토큰 예산으로 문장 경계에서 잘라 끝 문장을 다음 청크에 겹칩니다(오버랩 48토큰). 표 중간에서 시작하는 청크에는 캡션과 머리글 행을 다시 붙입니다.",
    note_okf: "OKF(Open Knowledge Format) 발상을 따른 지식 번들: 사람이 검수한 안내 페이지 24쪽(별칭 ko/en/de, 관련 페이지 링크, 본문)과, 그 페이지에 매칭된 질문을 문서 검색 없이 번들로만 답한 결과입니다. 질문 40개는 사람이 페이지를 보지 않고 썼고, 답변은 모드를 숨기고 섞어 사람이 채점했습니다. 1차(12쪽): 매칭되면 페이지 전부를 컨텍스트로. 2차(24쪽): 매칭 페이지와 관련 페이지만.",
    s_grade: "사람 채점", s_nobundle: "번들 답변 없음",
    w_grade: "답변은 모드(RAG·번들)를 숨기고 섞은 뒤 사람이 채점했습니다. 같은 답변은 한 번만 채점하고, 거절은 질문이 범위 안이면 부적절, 밖이면 적절로 봅니다. 비교를 위해 같은 질문을 문서 검색(상위 5 청크)으로 답했을 때의 채점을 함께 둡니다.",
    w_nobundle: "별칭이 맞는 페이지가 없고 가장 가까운 페이지의 dense 코사인도 0.55에 못 미쳐 번들 답변을 만들지 않았습니다. 서비스에서는 이 질문이 문서 검색 경로로 넘어갑니다.",
    w_bundle_r1: "1차(12쪽): 매칭된 질문은 검수한 안내 페이지 전부(12쪽, 약 1만 토큰)를 컨텍스트로 받습니다. 인용은 kb_<페이지>#0 형식입니다.",
    w_bundle_r2: "2차(24쪽): 매칭된 질문은 매칭 페이지와 그 관련(related) 페이지만 컨텍스트로 받습니다(평균 3.7쪽, 약 3,700 토큰). 24쪽 전부를 넣으면 정답이 8/16으로 떨어졌고 한 GPU에 들어가지 않았습니다.",
    grade: "채점", blind_item: "블라인드 항목", rag_same: "같은 질문의 문서 검색(RAG) 답변", refused: "거절", note_lbl: "채점 메모", scope_in: "범위 안", scope_out: "범위 밖", path_bundle: "번들", path_none: "매칭 없음",
    gr_맞음: "맞음", gr_부분: "부분", gr_틀림: "틀림", gr_적절: "적절", gr_부적절: "부적절",
    p_aliases: "별칭 (매칭에 쓰는 이름)", p_related: "관련 페이지", p_backlinks: "이 페이지를 가리키는 페이지", p_body: "본문", p_used: "이 페이지가 쓰인 질문", p_matched: "매칭", p_context: "컨텍스트", p_verified: "사람 검수", p_author: "작성", p_none: "없음", p_round: "페이지",
    w_aliases: "질문 원문(ko·de)과 영어 번역문(en)에 이 이름이 나오면 페이지가 매칭됩니다. 별칭이 없으면 질문과 페이지 본문의 bge-m3 코사인 0.55 이상인 상위 1쪽을 씁니다.",
    w_related: "관련 페이지는 2차 설정에서 매칭 페이지와 함께 컨텍스트에 들어갑니다(1홉).",
    w_body: "페이지는 AI 에이전트가 초안을 쓰고 사람이 검수했습니다(data/kb_review.md). 생성 모델은 이 본문만 보고 답합니다.",
    w_used: "이 페이지가 매칭됐거나 컨텍스트에 들어간 질문과 그 채점입니다. 누르면 그 질문으로 이동합니다.",
    d_source: "원본 PDF", d_layout: "레이아웃 복원 → 블록", d_drop: "버린 것과 남긴 것", d_sections: "절", d_chunks: "청크", d_ex_overlap: "예시 1 · 문장 오버랩", d_ex_table: "예시 2 · 표 머리글 반복",
    w_source: "PDF는 저장소에 커밋하지 않고 내려받아 sha256으로 확인합니다. 라이선스는 퍼블릭 도메인·CC BY 계열만 썼습니다.",
    w_layout: "pdf-editor(MuPDF WASM)의 레이아웃 복원이 쪽마다 문단의 역할(본문·제목·목록·캡션·머리말·꼬리말·각주), 표(행·열 격자), 그림을 읽기 순서로 돌려줍니다. 머리말·꼬리말은 이웃 쪽과 비교해 찾습니다.",
    w_drop: "머리말·꼬리말·그림(안의 글자 포함)·목차 줄(점선 뒤 쪽 번호)·참고문헌 절은 버립니다. 표는 행마다 한 줄 | 칸 | 칸 |으로 적습니다.",
    w_sections: "제목 역할의 문단마다 절을 나눕니다. 학위논문은 제목 감지가 적어 절이 큽니다. 청크에는 절 경로를 기록하지만 본문 앞에 붙이지는 않습니다.",
    w_chunks: "bge-m3 토크나이저 토큰 384개 예산을 문장 단위로 채웁니다. 다음 청크는 이전 청크의 끝 문장들로 시작합니다(오버랩 48토큰까지). 한 문장이 예산을 넘을 때만(표·목록) 토큰 수로 자릅니다. 막대 하나가 청크 하나이고 폭은 문자 수, 색은 절입니다. 누르면 본문이 열립니다.",
    w_ex_overlap: "연속 청크 3개입니다. 색칠한 부분이 이웃 청크와 겹치는 문장입니다. 근거 문장이 경계에 걸쳐 잘리는 일을 줄입니다.",
    w_ex_table: "표 중간에서 시작하는 청크에는 그 표의 캡션과 머리글 행을 앞에 붙입니다(색칠). 문자 범위는 원문 위치 그대로라 정답 매핑은 바뀌지 않습니다.",
    d_lang: "언어", d_pages: "쪽수", d_license: "라이선스", d_sha: "sha256", d_tool: "추출기", d_chars: "본문 문자 수", d_blocks: "블록", d_count: "개", d_dropped: "버림", d_kept: "남김", d_chunk_n: "청크 수", d_tok: "토큰 (평균 · 최소 · 최대)", d_ov: "이전 청크와 겹치는 청크", d_ov_chars: "평균 겹침 문자 수", d_th: "표 머리글을 붙인 청크", d_span: "절을 걸치는 청크", d_range: "문자 범위", d_sec_chunks: "청크", d_no_table: "이 문서에는 표 중간에서 시작하는 청크가 없습니다.", d_raw_missing: "원본 블록 파일(data/raw/pdf, 커밋 안 함)이 없어 남긴 블록만 보여 줍니다.", d_open: "본문 열기", d_toc: "목차 줄", d_drop_sections: "버린 절",
    role_body: "본문", "role_list-item": "목록 항목", role_heading: "제목", role_caption: "캡션", role_footnote: "각주", role_other: "기타(회전·세로 글)", role_header: "머리말", role_footer: "꼬리말", role_table: "표", role_figure: "그림", role_image: "그림(이미지)", role_vector: "그림(벡터)",
    foot_pdf: "청크 파일 chunks_fixed_tok384_ov48_pdf_th.jsonl · scripts/build_pdf_docs.py · src/ragbench/chunking.py · scripts/export_site_docs.py",
    foot_okf: "data/kb/*.md · data/kb_review.md · eval/kb/results.json (1차) · eval/kb2/results.json (2차) · scripts/export_site_docs.py",
    note_v2: "코퍼스: 위키백과 한·영·독 45건. 검색은 채팅 서버와 같은 구성(영어 BM25 + dense, RRF, 리랭커 영어 입력), 답변 프롬프트 cite_v1.",
    note_service: "현재 채팅 서버 설정(configs/s7_pipeline_kb.json): 사람이 쓴 실무 질문 50개. 질문이 사람이 검수한 안내 페이지 24쪽 중 하나에 매칭되면 검색 없이 번들로 답하고(경로 kb), 아니면 문서 검색으로 답합니다(경로 rag).",
    s_kbmatch: "페이지 매칭", s_bundle: "번들 컨텍스트",
    w_kbmatch: "질문을 지식 번들 페이지의 별칭(ko/en/de)에 맞춰 봅니다. 별칭이 없으면 질문과 페이지 본문의 dense 코사인(bge-m3)이 0.55 이상인 상위 1개를 씁니다. 매칭되면 검색을 건너뛰고 번들로 답합니다.",
    w_bundle: "매칭된 질문은 문서 검색 대신 매칭된 페이지와 그 관련 페이지(24쪽 중 평균 3.9쪽, 약 3,400 토큰)를 컨텍스트로 받습니다. 인용은 kb_<페이지>#0 형식입니다.",
    kb_matched: "매칭된 페이지", kb_none: "매칭된 페이지 없음 → 문서 검색 경로", kb_how_alias: "별칭 일치", kb_how_dense: "dense 코사인", kb_best: "가장 가까운 페이지", kb_pages: "컨텍스트에 넣은 페이지", kb_verified: "사람 검수",
    k_kb: "번들 경로로 답한 질문", k_rag: "문서 검색 경로로 답한 질문",
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
    title: "RAG Pipeline Trace", subtitle: "From real run records: one question through retrieval, generation and validation; how PDF documents become chunks; the OKF knowledge-bundle pages and the human grades of bundle-only answers.",
    pair: "Language pair", show: "Show", question: "Question", wheel_hint: "Wheel ↓ short: next stage · long or ↑: show all", wait_hint: "Playback starts in 3 seconds or when you scroll down", play: "Play", pause: "Pause", replay: "Replay", next_stage: "Next stage ›", show_all: "Show all", speed: "Speed", stage_of: "stage", all: "All",
    set_v2: "Wikipedia questions", set_v2_s: "90 · 346 chunks", set_pdf: "PDF documents → chunks", set_pdf_s: "6 documents · 557 chunks",
    set_okf: "OKF knowledge bundle", set_okf_s: "24 pages · 40 questions", set_service: "Service (knowledge bundle)", set_service_s: "50 · 24 pages + 903 chunks",
    k_all: "All", k_missing: "Gold chunk not in the context", k_blocked: "Blocked or refused",
    k_r1: "Round 1 (all 12 pages)", k_r2: "Round 2 (24 pages, matched only)", k_correct: "correct", k_partial: "partial", k_wrong: "wrong", k_refuse_ok: "refused (appropriate)", k_refuse_bad: "refused (inappropriate)", k_nomatch: "no match",
    doc: "Document", page: "Page", target: "Show", okf_questions: "40 questions", okf_pages: "24 pages",
    note_pdf: "How 6 PDFs become 557 chunks (no questions, no retrieval). The layout reconstruction of pdf-editor yields blocks in reading order; headers, footers, figure text, table-of-contents lines and reference sections are dropped; headings split the text into sections; chunks are cut at sentence boundaries under a 384-token budget (bge-m3 tokenizer) and the trailing sentences repeat in the next chunk (overlap 48 tokens). A chunk that starts inside a table gets the caption and header row again.",
    note_okf: "A knowledge bundle in the spirit of OKF (Open Knowledge Format): 24 reviewed guide pages (aliases ko/en/de, related-page links, body) and the questions that matched them, answered from the bundle only, without document retrieval. The 40 questions were written by a person without seeing the pages; answers were graded by a person with the mode hidden and shuffled. Round 1 (12 pages): a matched question gets all pages as context. Round 2 (24 pages): the matched pages and their related pages only.",
    s_grade: "Human grade", s_nobundle: "No bundle answer",
    w_grade: "Answers of all modes (RAG, bundle) were shuffled with the mode hidden and graded by a person. Identical answers were graded once; a refusal counts as inappropriate for an in-scope question and appropriate for an out-of-scope one. The grade of the retrieval answer (top 5 chunks) to the same question is shown for comparison.",
    w_nobundle: "No page alias matched and the closest page's dense cosine is below 0.55, so no bundle answer was generated. In the service this question goes to the document-retrieval path.",
    w_bundle_r1: "Round 1 (12 pages): a matched question gets all reviewed guide pages (12, about 10k tokens) as the context. Citations use the form kb_<page>#0.",
    w_bundle_r2: "Round 2 (24 pages): a matched question gets the matched pages and their related pages only (3.7 pages, about 3,700 tokens on average). With all 24 pages the correct answers fell to 8 of 16 and the prompt did not fit one GPU.",
    grade: "Grade", blind_item: "blind item", rag_same: "Retrieval (RAG) answer to the same question", refused: "refused", note_lbl: "Grader's note", scope_in: "in scope", scope_out: "out of scope", path_bundle: "bundle", path_none: "no match",
    gr_맞음: "correct", gr_부분: "partial", gr_틀림: "wrong", gr_적절: "appropriate", gr_부적절: "inappropriate",
    p_aliases: "Aliases (names used for matching)", p_related: "Related pages", p_backlinks: "Pages linking here", p_body: "Body", p_used: "Questions that used this page", p_matched: "matched", p_context: "context", p_verified: "reviewed by a person", p_author: "author", p_none: "none", p_round: "page",
    w_aliases: "A page matches when one of these names occurs in the original question (ko, de) or its English translation (en). Without an alias match, the top page with a bge-m3 cosine of 0.55 or more between question and page text is used.",
    w_related: "In the round-2 setting the related pages enter the context together with the matched page (1 hop).",
    w_body: "Pages were drafted by an AI agent and reviewed by a person (data/kb_review.md). The generator answers from this body only.",
    w_used: "Questions where this page was matched or placed in the context, with their grades. Click to open the question.",
    d_source: "Source PDF", d_layout: "Layout reconstruction → blocks", d_drop: "Dropped and kept", d_sections: "Sections", d_chunks: "Chunks", d_ex_overlap: "Example 1 · sentence overlap", d_ex_table: "Example 2 · repeated table header",
    w_source: "PDFs are not committed; they are downloaded and checked against a sha256. Only public-domain and CC BY licenses were used.",
    w_layout: "The layout reconstruction of pdf-editor (MuPDF WASM) returns, per page, paragraphs with their role (body, heading, list item, caption, header, footer, footnote), tables as row/column grids and figures, in reading order. Headers and footers are found by comparing neighbouring pages.",
    w_drop: "Headers, footers, figures (including their text), table-of-contents lines (dot leaders followed by a page number) and reference sections are dropped. Tables are written one row per line as | cell | cell |.",
    w_sections: "Every heading paragraph starts a section. Heading detection found few headings in the theses, so their sections are large. Chunks record their section path but do not prepend it to the text.",
    w_chunks: "A budget of 384 bge-m3 tokens is filled sentence by sentence. The next chunk starts with the trailing sentences of the previous one (up to 48 tokens of overlap). Only a sentence longer than the budget (tables, lists) is cut by token count. One bar is one chunk; width is its character count, colour its section. Click to open the text.",
    w_ex_overlap: "Three consecutive chunks. The highlighted text is shared with the neighbouring chunk, so an evidence sentence rarely gets cut at a boundary.",
    w_ex_table: "A chunk that starts inside a table gets the table's caption and header row prepended (highlighted). The character span stays the original position, so gold mappings are unchanged.",
    d_lang: "language", d_pages: "pages", d_license: "license", d_sha: "sha256", d_tool: "extractor", d_chars: "text characters", d_blocks: "blocks", d_count: "", d_dropped: "dropped", d_kept: "kept", d_chunk_n: "chunks", d_tok: "tokens (mean · min · max)", d_ov: "chunks overlapping the previous one", d_ov_chars: "mean overlap, characters", d_th: "chunks with a repeated table header", d_span: "chunks spanning two sections", d_range: "character span", d_sec_chunks: "chunks", d_no_table: "No chunk of this document starts inside a table.", d_raw_missing: "The raw block file (data/raw/pdf, not committed) is absent, so only the kept blocks are shown.", d_open: "open text", d_toc: "table-of-contents lines", d_drop_sections: "dropped sections",
    role_body: "body", "role_list-item": "list item", role_heading: "heading", role_caption: "caption", role_footnote: "footnote", role_other: "other (rotated text)", role_header: "header", role_footer: "footer", role_table: "table", role_figure: "figure", role_image: "figure (image)", role_vector: "figure (vector)",
    foot_pdf: "chunk file chunks_fixed_tok384_ov48_pdf_th.jsonl · scripts/build_pdf_docs.py · src/ragbench/chunking.py · scripts/export_site_docs.py",
    foot_okf: "data/kb/*.md · data/kb_review.md · eval/kb/results.json (round 1) · eval/kb2/results.json (round 2) · scripts/export_site_docs.py",
    note_v2: "Corpus: 45 Wikipedia articles in Korean, English and German. Retrieval as in the chat server (English BM25 + dense, RRF, reranker on English text); answer prompt cite_v1.",
    note_service: "The current chat-server config (configs/s7_pipeline_kb.json) on 50 human-written practical questions. When a question matches one of the 24 reviewed guide pages, the bundle answers without retrieval (path kb); otherwise document retrieval answers (path rag).",
    s_kbmatch: "Page match", s_bundle: "Bundle context",
    w_kbmatch: "The question is matched against the aliases (ko/en/de) of the knowledge bundle pages; without an alias match, the best dense match (bge-m3 cosine of question vs page text) of 0.55 or more is used. On a match, retrieval is skipped and the bundle answers.",
    w_bundle: "A matched question gets the matched pages and their related pages (3.9 of 24 on average, about 3,400 tokens) as the context instead of retrieved chunks. Citations use the form kb_<page>#0.",
    kb_matched: "Matched pages", kb_none: "No page matched → document retrieval path", kb_how_alias: "alias match", kb_how_dense: "dense cosine", kb_best: "closest page", kb_pages: "Pages in the context", kb_verified: "reviewed by a person",
    k_kb: "Answered through the bundle", k_rag: "Answered through retrieval",
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
const DEFAULT_STAGES = ["input", "translate", "retrieve", "rrf", "rerank", "generate", "output", "answer"];
let STAGES = DEFAULT_STAGES;
// 서비스 세트(지식 번들 포함): 입력 검증 뒤 "페이지 매칭" 단계가 있고, 매칭되면 검색 단계 대신 번들 컨텍스트 단계가 온다
function stagesOf(r) {
  if (r.kind === "okf_q") return r.path === "kb" ? ["kbmatch", "bundle", "generate", "output", "answer", "grade"] : ["kbmatch", "nobundle"];
  if (!r.kb) return DEFAULT_STAGES;
  return r.path === "kb" ? ["input", "kbmatch", "bundle", "generate", "output", "answer"]
                         : ["input", "kbmatch", "translate", "retrieve", "rrf", "rerank", "generate", "output", "answer"];
}
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
  let pdfdocs, okf;
  [STATE.meta, STATE.chunks, pdfdocs, okf] = await Promise.all([getJSON("data/meta.json"), getJSON("data/chunks.json"), getJSON("data/pdfdocs.json"), getJSON("data/okf.json")]);
  await Promise.all(SETS.filter((s) => KIND[s] === "trace").map(async (s) => { STATE.rows[s] = await getJSON(`data/${s}.json`); }));
  STATE.pdfmeta = pdfdocs.meta;
  STATE.pdfdocs = pdfdocs.docs.map((d) => ({ ...d, kind: "pdf_doc", qid: d.id }));
  const pagesById = Object.fromEntries(okf.pages.map((p) => [p.id, p]));
  const promptOf = Object.fromEntries(okf.meta.rounds.map((x) => [x.round, x.prompt_version]));
  STATE.okf = { meta: okf.meta, pagesById, pages: okf.pages.map((p) => ({ ...p, kind: "okf_p", qid: p.id })), questions: okf.questions.map((q) => okfQuestionRow({ ...q, prompt: promptOf[q.round] }, pagesById)) };
  const h = new URLSearchParams(location.hash.slice(1));
  if (SETS.includes(h.get("set"))) STATE.set = h.get("set");
  STATE.view = h.get("view") === "pages" ? "pages" : "q";
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
  $("#f-pair").onchange = () => {
    if (KIND[STATE.set] === "okf") { STATE.view = $("#f-pair").value; $("#f-kind").innerHTML = ""; renderStatic(); buildList(); }
    else buildList(cur()?.qid);
  };
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
  $("#p-all").onclick = () => showAll();
  // 재생 중 사용자가 직접 스크롤하면(터치·스크롤 키·스크롤바) 바로 멈추고 전체 보기로 바꾼다.
  // 단계 전환 때 페이지가 하는 scrollIntoView는 이 이벤트들을 만들지 않으므로 구분된다.
  const interrupt = () => { if (STATE.playing) showAll(); };
  const scrollDown = () => { if (STATE.waiting) startFromWait(); else interrupt(); };
  // 대기 중 클릭·키 입력·선택 변경은 3초를 처음부터 다시 센다
  addEventListener("pointerdown", () => { if (STATE.waiting) armWait(); });
  addEventListener("change", () => { if (STATE.waiting) armWait(); });
  addEventListener("wheel", onWheel, { passive: false });
  addEventListener("touchmove", scrollDown, { passive: true });
  addEventListener("keydown", (e) => {
    if (e.target.matches("select, input, textarea") || (e.key === " " && e.target.matches("button, summary"))) return;   // 입력 칸 조작, 버튼 누르기는 제외
    if (["ArrowDown", "PageDown", "End", " "].includes(e.key)) scrollDown();
    else if (["ArrowUp", "PageUp", "Home"].includes(e.key)) interrupt();
    else if (STATE.waiting) armWait();
  });
  addEventListener("mousedown", (e) => { if (e.clientX >= document.documentElement.clientWidth) scrollDown(); });
  $("#p-restart").onclick = () => restart();
  $("#p-speed").onchange = (e) => { STATE.speed = Number(e.target.value); };
  document.addEventListener("click", (e) => {
    const pg = e.target.closest("[data-page]"); if (pg) return goto("okf", "pages", pg.dataset.page);
    const qq = e.target.closest("[data-q]"); if (qq) return goto("okf", "q", qq.dataset.q);
    const b = e.target.closest("[data-cid]"); if (!b) return;
    // OKF 세트에서 번들 페이지 ID(kb_<페이지>#0)를 누르면 조각 대화상자 대신 그 페이지로 간다
    if (STATE.set === "okf" && b.dataset.cid.startsWith("kb_")) return goto("okf", "pages", b.dataset.cid.replace(/^kb_/, "").replace(/#\d+$/, ""));
    openChunk(b.dataset.cid);
  });
  // 공유 링크(#set=..&q=..)로 들어오거나 주소창의 해시만 바뀐 경우
  window.addEventListener("hashchange", () => {
    const h = new URLSearchParams(location.hash.slice(1));
    const s = SETS.includes(h.get("set")) ? h.get("set") : STATE.set;
    const v = h.get("view") === "pages" ? "pages" : "q";
    if (s === STATE.set && v === STATE.view && h.get("q") === cur()?.qid) return;
    STATE.set = s; STATE.view = v; $("#f-pair").value = ""; $("#f-kind").innerHTML = "";
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
  document.querySelectorAll(".tab").forEach((b) => (b.onclick = () => { STATE.set = b.dataset.set; STATE.view = "q"; $("#f-pair").value = ""; $("#f-kind").innerHTML = ""; renderStatic(); buildList(); }));
  $("#set-note").textContent = t("note_" + STATE.set);
  const kind = KIND[STATE.set];
  const pairL = $("#f-pair").closest("label"), kindL = $("#f-kind").closest("label"), qSpan = $("#f-q").closest("label").querySelector("span");
  const kv = $("#f-kind").value || "all";
  const kindOpts = (kinds) => { $("#f-kind").innerHTML = kinds.map((k) => `<option value="${k}" ${k === kv ? "selected" : ""}>${esc(t("k_" + k))}</option>`).join(""); };
  // 정적 보기(PDF 청크화, OKF 페이지)에서는 재생 도크를 숨긴다
  $("#dock").hidden = kind === "chunking" || (kind === "okf" && STATE.view === "pages");
  pairL.hidden = kind === "chunking"; kindL.hidden = kind === "chunking";
  if (kind === "chunking") {
    qSpan.textContent = t("doc");
  } else if (kind === "okf") {
    pairL.querySelector("span").textContent = t("target");
    $("#f-pair").innerHTML = [["q", t("okf_questions")], ["pages", t("okf_pages")]].map(([v, l]) => `<option value="${v}" ${v === STATE.view ? "selected" : ""}>${esc(l)}</option>`).join("");
    $("#f-pair").disabled = false;
    kindOpts(STATE.view === "pages" ? ["all", "r1", "r2"] : ["all", "r1", "r2", "correct", "partial", "wrong", "refuse_ok", "refuse_bad", "nomatch"]);
    qSpan.textContent = STATE.view === "pages" ? t("page") : t("question");
  } else {
    const rows = STATE.rows[STATE.set];
    const pairs = [...new Set(rows.map((r) => r.group))].sort();
    const pv = $("#f-pair").value;
    $("#f-pair").innerHTML = `<option value="">${esc(t("all"))}</option>` + pairs.map((p) => `<option ${p === pv ? "selected" : ""}>${esc(p)}</option>`).join("");
    $("#f-pair").disabled = pairs.length < 2;
    kindOpts(STATE.set === "service" ? ["all", "kb", "rag", "blocked"] : ["all", "missing", "blocked"]);
  }
  const src = kind === "trace" ? `<code>${esc(STATE.meta.sets[STATE.set].config)}</code> · <code>${esc(STATE.meta.sets[STATE.set].answers)}</code> · <code>scripts/export_site_data.py</code>` : `<code>${esc(t(kind === "chunking" ? "foot_pdf" : "foot_okf"))}</code>`;
  $("#foot").innerHTML = (kind === "trace" ? `<p>${esc(t("foot1"))}</p><p>${esc(t("foot2"))}</p>` : "") + `<p>${esc(t("foot3"))}</p><p>${esc(t("foot4"))}</p><p>${src}</p>`;
}

// 다른 세트·보기의 항목으로 이동 (페이지 칩, 질문 줄, 공유 링크)
function goto(set, view, qid) {
  STATE.set = set; STATE.view = view; $("#f-pair").value = ""; $("#f-kind").innerHTML = "";
  renderStatic(); buildList(qid);
  scrollTo({ top: $("#question-card").offsetTop - 8, behavior: reduced() ? "auto" : "smooth" });
}

function matchesOkf(r, kind) {
  const g = r.human || {};
  switch (kind) {
    case "r1": return r.round === 1;
    case "r2": return r.round === 2;
    case "correct": return g.correctness === "맞음";
    case "partial": return g.correctness === "부분";
    case "wrong": return g.correctness === "틀림";
    case "refuse_ok": return g.refusal === "적절";
    case "refuse_bad": return g.refusal === "부적절";
    case "nomatch": return r.path !== "kb";
    default: return true;
  }
}

function matches(r, kind) {
  const inCtx = Object.keys(r.gold).some((g) => r.context_ids.includes(g));
  if (kind === "missing") return Object.keys(r.gold).length > 0 && !inCtx;
  if (kind === "blocked") return !r.output.ok;
  if (kind === "kb") return r.path === "kb";
  if (kind === "rag") return r.path === "rag";
  return true;
}

function buildList(keepQid) {
  const K = KIND[STATE.set], kind = $("#f-kind").value || "all";
  if (K === "chunking") STATE.list = STATE.pdfdocs;
  else if (K === "okf") STATE.list = STATE.view === "pages" ? STATE.okf.pages.filter((p) => kind === "all" || p.round === Number(kind.slice(1))) : STATE.okf.questions.filter((q) => matchesOkf(q, kind));
  else { const pair = $("#f-pair").value; STATE.list = STATE.rows[STATE.set].filter((r) => (!pair || r.group === pair) && matches(r, kind)); }
  const short = (s) => (s.length > 70 ? s.slice(0, 70) + "…" : s);
  const sel = $("#f-q");
  sel.innerHTML = STATE.list.length
    ? STATE.list.map((r, i) => `<option value="${i}">${esc(r.qid)} · ${esc(short(r.question ?? r.title))}</option>`).join("")
    : `<option>-</option>`;
  const k = STATE.list.findIndex((r) => r.qid === keepQid);
  STATE.idx = k >= 0 ? k : 0;
  sel.value = String(STATE.idx);
  show();
}

const cur = () => STATE.list[STATE.idx];
function step(d) { if (!STATE.list.length) return; STATE.idx = (STATE.idx + d + STATE.list.length) % STATE.list.length; $("#f-q").value = String(STATE.idx); show(); }

function setHash(r) {
  const view = KIND[STATE.set] === "okf" && STATE.view === "pages" ? "&view=pages" : "";
  history.replaceState(null, "", `#set=${STATE.set}${view}&q=${encodeURIComponent(r.qid)}`);
}

function show() {
  const wasWaiting = STATE.waiting;   // 아직 한 번도 재생하지 않았으면 새 질문도 대기부터 시작한다
  cancel();
  const r = cur();
  if (!r) { $("#question-card").innerHTML = `<p class="empty">-</p>`; $("#flow").innerHTML = ""; $("#stages").innerHTML = ""; return; }
  setHash(r);
  // 정적 보기: 재생 없이 전부 바로 그린다
  if (r.kind === "pdf_doc") { STAGES = []; STATE.revealed = 0; renderPdfDoc(r); return; }
  if (r.kind === "okf_p") { STAGES = []; STATE.revealed = 0; renderOkfPage(r); return; }
  STAGES = stagesOf(r);
  renderQuestion(r);
  renderFlow(r);
  renderStages(r);
  STATE.revealed = 0;
  syncPlayer();
  // 움직임 줄이기 설정이면 바로 전부 보여 준다. 첫 재생 전에는 대기하고, 그 뒤로는 질문을 바꾸면 바로 재생한다
  if (reduced()) { STATE.waiting = false; for (let i = 0; i < STAGES.length; i++) revealNow(i); syncPlayer(); }
  else if (wasWaiting) armWait();
  else run(0, false);
}

const isGold = (r, cid) => Object.prototype.hasOwnProperty.call(r.gold, cid);
const cidBtn = (r, cid) => `<button class="cid" data-cid="${esc(cid)}" title="${esc(STATE.chunks[cid]?.title || "")}">${isGold(r, cid) ? `<span class="star" aria-label="${esc(t("gold"))}">★</span>` : ""}${esc(cid)}</button>`;

function renderQuestion(r) {
  const pills = [`<span class="pill">${esc(r.qid)}</span>`, `<span class="pill">${esc(r.group)}</span>`];
  if (r.evidence_kind) pills.push(`<span class="pill">${esc(r.evidence_kind)}</span>`);
  if (r.kind === "okf_q") {
    pills.length = 1;
    pills.push(`<span class="pill">${esc(roundLabel(r.round))}</span>`, `<span class="pill">${esc(t(r.scope === "in" ? "scope_in" : "scope_out"))}</span>`,
      `<span class="pill ${r.path === "kb" ? "gold" : ""}">${esc(t(r.path === "kb" ? "path_bundle" : "path_none"))}</span>`);
    if (r.human) pills.push(gradePill(r.human, t("grade")));
    if (r.rag) pills.push(gradePill(r.rag, "RAG", true));
  } else if (r.kb) pills.push(`<span class="pill ${r.path === "kb" ? "gold" : ""}">${r.path === "kb" ? "kb" : "rag"}</span>`);
  if (Object.keys(r.gold).length) pills.push(`<span class="pill gold">★ ${esc(t("gold"))} ${Object.keys(r.gold).length}</span>`);
  $("#question-card").innerHTML = `<div class="q-meta">${pills.join("")}</div><p class="q-text">${esc(r.question)}</p>`;
}

function nodeVal(r, s) {
  const st = r.stages, m = setMeta(r);
  switch (s) {
    case "input": return st ? (st.input.ok ? t("pass") : t("blocked")) : t("pass");
    case "kbmatch": return r.kb.match.ids.length ? r.kb.match.ids.join(", ") : "-";
    case "bundle": return `${r.kb.passages.length} ${STATE.lang === "ko" ? "쪽" : "pages"}`;
    case "translate": return `${fmt(st.translation.seconds, 2)} ${t("s")}`;
    case "retrieve": return `${m.n_chunks} → ${st.parts.map((p) => p.n).join(" + ")}`;
    case "rrf": return `→ ${st.rrf.n}`;
    case "rerank": return `${st.rerank.n} → ${m.retrieval.context_k}`;
    case "generate": return r.gen ? `${fmt(r.gen.seconds, 1)} ${t("s")}` : m.prompt;
    case "output": return r.output.ok ? t("pass") : t("blocked");
    case "answer": return r.output.ok ? t("delivered") : t("fixed_msg");
    case "grade": return r.human ? gradeText(r.human) : "-";
    case "nobundle": return r.dense_best ? `${r.dense_best[0]} ${r.dense_best[1].toFixed(2)}` : "-";
  }
}

function renderFlow(r) {
  $("#flow").style.gridTemplateColumns = `repeat(${STAGES.length}, minmax(0, 1fr))`;
  $("#flow").innerHTML = STAGES.map((s, i) => {
    const blocked = (s === "output" && !r.output.ok) || (s === "input" && r.stages && !r.stages.input.ok);
    return `<button class="node${blocked ? " blocked" : ""}" data-stage="${s}" type="button"><span class="n-step">${i + 1}</span><span class="n-name">${esc(t("s_" + s))}</span><span class="n-val">${esc(nodeVal(r, s))}</span></button>`;
  }).join("");
  // 노드를 누르면 그 단계까지 바로 펼치고 그 단계로 이동한다
  document.querySelectorAll(".node").forEach((n, i) => (n.onclick = () => {
    cancel();
    for (let k = STATE.revealed; k <= i; k++) revealNow(k);
    mark(STATE.revealed - 1, false); syncPlayer(); scrollToStage(i, true);
  }));
}

function card(s, i, timing, body, what) {
  i = STAGES.indexOf(s);
  return `<article class="stage" data-stage="${s}" id="stage-${s}" hidden><div class="stage-head"><h2><span class="num">${i + 1}</span>${esc(t("s_" + s))}</h2>${timing ? `<span class="timing">${timing}</span>` : ""}</div><p class="what">${esc(what ?? t("w_" + s))}</p>${body}</article>`;
}
// 정적 보기의 카드: 숨기지 않고 번호만 붙인다
function staticCard(n, title, what, body) {
  return `<article class="stage"><div class="stage-head"><h2><span class="num">${n}</span>${esc(title)}</h2></div><p class="what">${esc(what)}</p>${body}</article>`;
}
function commitStages(out) {
  $("#stages").innerHTML = out.join("");
  // 애니메이션은 DOM을 바꾸므로, 멈추거나 건너뛸 때 되돌릴 최종 모습을 단계별로 저장해 둔다
  STATE.cardHTML = {};
  document.querySelectorAll(".stage").forEach((c) => { STATE.cardHTML[c.dataset.stage] = c.innerHTML; });
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

function renderKbMatch(r) {
  const mt = r.kb.match;
  const how = Object.entries(mt.alias).map(([id, forms]) => `<li><span class="ic ok">✓</span><span>${esc(id)} · ${esc(t("kb_how_alias"))}: ${esc(forms.join("; "))}</span></li>`)
    .concat(mt.dense.map(([id, sc]) => `<li><span class="ic ok">✓</span><span>${esc(id)} · ${esc(t("kb_how_dense"))} ${sc.toFixed(2)}</span></li>`));
  const best = r.kb.dense_best ? `<div class="gold-line">${esc(t("kb_best"))}: ${esc(r.kb.dense_best[0])} (${r.kb.dense_best[1].toFixed(2)})</div>` : "";
  return (how.length ? `<ul class="checks">${how.join("")}</ul>` : `<ul class="checks"><li><span class="ic na">–</span><span>${esc(t("kb_none"))}</span></li></ul>`) + best;
}

function renderBundle(r) {
  const pages = r.kb.passages.map((p) => `<button class="ctx${r.kb.match.ids.includes(p.id) ? " gold" : ""}" data-cid="${esc(p.cid)}">${r.kb.match.ids.includes(p.id) ? "★ " : ""}${esc(p.title)}</button>`).join("");
  return `<div class="col-title">${esc(t("kb_pages"))} · ${r.kb.passages.length} · ${esc(t("kb_verified"))} ${r.kb.verified}/${r.kb.passages.length}</div><div class="ctx-list">${pages}</div>`;
}

// OKF 세트에는 meta.sets 항목이 없다: 프롬프트 이름만 질문 행에서 가져온다
const setMeta = (r) => STATE.meta.sets[STATE.set] || { prompt: r.prompt || "cite_refuse_v1", retrieval: {}, n_chunks: 0 };
function renderStages(r) {
  const st = r.stages, m = setMeta(r);
  const out = [];
  // 1. 입력 검증
  const inOk = st ? st.input.ok : true;
  if (STAGES.includes("input")) out.push(card("input", 0, st ? ms(st.input.ms) : "", `<ul class="checks"><li><span class="ic ${inOk ? "ok" : "no"}">${inOk ? "✓" : "✕"}</span>${esc(inOk ? `${t("pass")} · ${r.question.length} / 1000` : st.input.reason)}</li></ul>`));
  if (r.kb) {
    out.push(card("kbmatch", 0, "", renderKbMatch(r)));
    if (r.kind === "okf_q" && r.path !== "kb") {
      out.push(card("nobundle", 0, "", renderNoBundle(r)));
      return commitStages(out);
    }
    if (r.path === "kb") {
      out.push(card("bundle", 0, `${r.kb.passages.length} ${STATE.lang === "ko" ? "쪽" : "pages"}`, renderBundle(r), r.kind === "okf_q" ? t(r.round === 1 ? "w_bundle_r1" : "w_bundle_r2") : undefined));
      out.push(card("generate", 0, r.gen ? `${fmt(r.gen.seconds, 2)} ${t("s")} · ${esc(m.prompt)}` : esc(m.prompt),
        `<div class="col-title">${esc(t("context"))}</div><div class="ctx-list">${r.context_ids.map((c) => `<button class="ctx gold" data-cid="${esc(c)}">${esc(c)}</button>`).join("")}</div>` +
        (r.gen ? `<dl class="kv"><dt>${esc(t("prompt_tok"))}</dt><dd>${r.gen.prompt_tokens}</dd><dt>${esc(t("out_tok"))}</dt><dd>${r.gen.completion_tokens}</dd><dt>${esc(t("gen_time"))}</dt><dd>${fmt(r.gen.seconds, 2)} ${t("s")}</dd></dl>` : "") +
        `<details><summary>${esc(t("system_prompt"))} (${esc(m.prompt)})</summary><pre class="sys">${esc(STATE.meta.prompts[m.prompt])}\n\nContext:\n\n[${esc(r.context_ids[0])}] …\n…\n\nQuestion: ${esc(r.question)}</pre></details>`));
      out.push(card("output", 0, "", renderChecks(r)));
      out.push(card("answer", 0, "", renderDelivered(r)));
      if (STAGES.includes("grade")) out.push(card("grade", 0, r.human ? `${t("blind_item")} ${esc(r.human.item)}` : "", renderGrade(r)));
      return commitStages(out);
    }
  }
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
  commitStages(out);
}

const SAFE = {
  ko: "제공된 문서에서 이 질문에 답할 근거를 찾지 못했습니다.",
  en: "I could not find supporting evidence for this question in the provided documents.",
  de: "Für diese Frage habe ich in den vorliegenden Dokumenten keine Belege gefunden.",
};

function renderDelivered(r) {
  if (r.output.ok) return `<div class="answer final">${renderAnswer(r)}</div>`;
  // 서비스 경로(사람이 쓴 질문)는 저장된 답변이 이미 고정 문구이고 모델 원문은 NO_ANSWER다
  const served = STATE.set === "service" || STATE.set === "okf";
  const shown = served ? r.answer : SAFE[r.q_lang] || SAFE.en;
  const raw = served ? (r.raw_answer || (r.output.reason === "refusal_sentinel" ? "NO_ANSWER" : "")) : r.answer;
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
  $("#p-hint").textContent = STATE.waiting ? t("wait_hint") : STATE.playing ? t("wheel_hint") : "";
  $("#p-hint").classList.toggle("wait", STATE.waiting);
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

// 첫 재생 전 대기: WAIT_MS 동안 조작이 없으면 재생을 시작한다
const WAIT_MS = 3000;
let waitTimer = null;
function armWait() {
  STATE.waiting = true;
  clearTimeout(waitTimer);
  waitTimer = setTimeout(startFromWait, WAIT_MS);
  syncPlayer();
}
function startFromWait() {
  if (!STATE.waiting) return;
  clearTimeout(waitTimer);
  STATE.waiting = false;
  run(STATE.revealed, false);
}

function cancel() {
  RUN += 1;
  STATE.playing = false;
  STATE.waiting = false;              // 버튼·노드로 직접 조작하면 대기도 끝난다 (show()는 호출 전에 대기 여부를 따로 기억한다)
  clearTimeout(waitTimer);
  // 애니메이션 도중이던 카드는 최종 모습으로 되돌린다
  document.querySelectorAll(".stage.anim").forEach(restore);
  if (document.querySelector(".node")) mark(Math.max(0, STATE.revealed - 1), false);
  syncPlayer();
}

// 재생 중 휠: 아래로 짧게 = 다음 단계(재생 계속), 아래로 길게 또는 위로 = 전체 보기.
// 휠 이벤트 묶음(제스처) 하나를 한 번의 조작으로 보고, 마지막 이벤트 뒤 WHEEL_IDLE ms가 지나면 제스처가 끝난 것으로 본다.
const WHEEL_LONG = 300, WHEEL_IDLE = 250;
let wheelSum = 0, wheelTimer = null;
let wheelSwallow = false;                        // 대기 중 스크롤로 재생을 시작한 그 휠 동작은 끝날 때까지 단계 조작으로 쓰지 않는다
function onWheel(e) {
  const dy = e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? innerHeight : 1);   // 줄·페이지 단위를 픽셀로
  if (STATE.waiting && dy > 0) {
    startFromWait();
    wheelSwallow = true;
  }
  if (wheelSwallow) {
    if (STATE.playing) e.preventDefault();
    clearTimeout(wheelTimer);
    wheelTimer = setTimeout(() => { wheelSwallow = false; wheelSum = 0; }, WHEEL_IDLE);
    return;
  }
  if (!STATE.playing) { wheelSum = 0; return; }
  if (!dy) return;
  clearTimeout(wheelTimer);
  if (dy < 0) { wheelSum = 0; showAll(); return; }
  e.preventDefault();                                   // 재생 중에는 짧은 휠이 페이지를 움직이지 않고 단계만 넘긴다
  const first = wheelSum === 0;
  wheelSum += dy;
  if (wheelSum > WHEEL_LONG) { wheelSum = 0; showAll(); return; }
  if (first) skipToNext();
  wheelTimer = setTimeout(() => { wheelSum = 0; }, WHEEL_IDLE);
}

function skipToNext() {
  // 지금 단계를 완성된 모습으로 두고 다음 단계부터 재생을 이어 간다
  const next = STATE.revealed;
  cancel();
  if (next < STAGES.length) run(next, false);
}

function showAll() {
  cancel();
  for (let i = STATE.revealed; i < STAGES.length; i++) revealNow(i);
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
  STATE.waiting = false;
  clearTimeout(waitTimer);
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
  async grade(el, id) {
    prep(el, ".reveal, .gold-line");
    await sleep(350);
    for (const x of el.querySelectorAll(".reveal")) { if (id !== RUN) return; showEl(x); x.querySelector(".pill")?.classList.add("popin"); await sleep(400); }
    await sleep(200); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async nobundle(el, id) {
    prep(el, ".checks li, .gold-line");
    await sleep(350);
    for (const li of el.querySelectorAll(".checks li")) { if (id !== RUN) return; showEl(li, true); await sleep(300); }
    await sleep(200); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async kbmatch(el, id) {
    prep(el, ".checks li, .gold-line");
    await sleep(350);
    for (const li of el.querySelectorAll(".checks li")) { if (id !== RUN) return; showEl(li, true); await sleep(300); }
    await sleep(200); if (id !== RUN) return;
    el.querySelectorAll(".gold-line").forEach((g) => showEl(g));
    await sleep(500);
  },
  async bundle(el, id) {
    prep(el, ".ctx");
    await sleep(300);
    for (const c of el.querySelectorAll(".ctx")) { if (id !== RUN) return; showEl(c); c.classList.add("popin"); await sleep(120); }
    await sleep(500);
  },
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

// ---------- OKF 세트: 번들 전용 질문 (행 변환, 채점 카드) ----------
// eval/kb·kb2의 번들 답변을 서비스 세트의 kb 경로와 같은 모양으로 바꿔 같은 카드(매칭·번들·생성·출력 검증·답변)를 재사용한다
function okfQuestionRow(q, pagesById) {
  const matched = q.path === "bundle";
  const ids = q.match.ids || [], related = q.match.related || [];
  const ctx = matched ? q.pages : [];
  return {
    ...q, kind: "okf_q", group: `round ${q.round}`, q_lang: "ko", gold: {}, path: matched ? "kb" : "none",
    context_ids: matched ? q.context_ids : [],
    kb: {
      match: { alias: q.match.alias || {}, dense: q.match.dense || [], ids, related, canonical_names: q.match.canonical_names || [] },
      passages: ctx.map((id) => ({ id, cid: `kb_${id}#0`, title: pagesById[id]?.title || id })),
      verified: ctx.filter((id) => pagesById[id]?.verified).length, dense_best: q.dense_best,
    },
    output: matched
      ? { ok: !q.blocked, reason: q.reason, cited: q.blocked ? [] : [...new Set([...(q.answer || "").matchAll(CITE)].map((m) => m[1]))], refused: ["refusal_sentinel", "refusal_text"].includes(q.reason) }
      : { ok: false, reason: null, cited: [], refused: false },
  };
}

const roundLabel = (n) => (STATE.lang === "ko" ? `${n}차` : `round ${n}`);
function gradeText(g) {
  if (!g) return "";
  return g.correctness ? t("gr_" + g.correctness) : g.refusal ? `${t("refused")} · ${t("gr_" + g.refusal)}` : "";
}
function gradeClass(g) {
  return g.correctness === "맞음" || g.refusal === "적절" ? "good" : g.correctness === "부분" ? "warn" : "bad";
}
function gradePill(g, label, small) {
  if (!g) return "";
  return `<span class="pill ${gradeClass(g)}${small ? " soft" : ""}">${label ? esc(label) + ": " : ""}${esc(gradeText(g))}</span>`;
}

function ragLine(r) {
  return r.rag ? `<div class="gold-line">${esc(t("rag_same"))}: ${gradePill(r.rag)} <span class="pill soft">${esc(t("blind_item"))} ${esc(r.rag.item)}</span>${r.rag.note ? ` · ${esc(r.rag.note)}` : ""}</div>` : "";
}

function renderGrade(r) {
  const g = r.human;
  if (!g) return `<p class="empty">-</p>` + ragLine(r);
  return `<div class="reveal"><span class="pill big ${gradeClass(g)}">${esc(t("grade"))}: ${esc(gradeText(g))}</span> <span class="pill soft">${esc(t("blind_item"))} ${esc(g.item)}</span></div>` +
    (g.note ? `<div class="reveal note"><b>${esc(t("note_lbl"))}</b> · ${esc(g.note)}</div>` : "") + ragLine(r);
}

function renderNoBundle(r) {
  const best = r.dense_best ? `<li><span class="ic na">–</span><span>${esc(t("kb_best"))}: ${esc(r.dense_best[0])} (${r.dense_best[1].toFixed(2)} &lt; 0.55)</span></li>` : "";
  return `<ul class="checks"><li><span class="ic no">✕</span><span>${esc(t("kb_none"))}</span></li>${best}</ul>` + ragLine(r);
}

// ---------- OKF 세트: 페이지 보기 (정적) ----------
const mdInline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
function mdList(items) {
  // 들여쓰기(칸 수)로 중첩한다
  let html = "";
  const stack = [];
  for (const it of items) {
    const ind = it.match(/^\s*/)[0].length, ordered = /^\s*\d+\./.test(it), text = it.replace(/^\s*(?:[-*]|\d+\.)\s+/, "");
    while (stack.length && stack[stack.length - 1].ind > ind) html += `</li></${stack.pop().tag}>`;
    if (!stack.length || stack[stack.length - 1].ind < ind) { const tag = ordered ? "ol" : "ul"; stack.push({ ind, tag }); html += `<${tag}><li>${mdInline(text)}`; }
    else html += `</li><li>${mdInline(text)}`;
  }
  while (stack.length) html += `</li></${stack.pop().tag}>`;
  return html;
}
// 페이지 본문(마크다운 부분집합: 제목, 글머리, 번호, 표, 굵게, 코드)을 HTML로
function md(src) {
  const lines = src.split("\n"), out = [];
  const isList = (ln) => /^\s*(?:[-*]|\d+\.)\s+/.test(ln), isTable = (ln) => /^\s*\|/.test(ln), isHead = (ln) => /^#{1,6}\s/.test(ln);
  let i = 0;
  while (i < lines.length) {
    const ln = lines[i];
    if (isHead(ln)) { const lvl = Math.min(ln.match(/^#+/)[0].length + 2, 6); out.push(`<h${lvl}>${mdInline(ln.replace(/^#+\s*/, ""))}</h${lvl}>`); i++; continue; }
    if (isTable(ln)) {
      const rows = [];
      while (i < lines.length && isTable(lines[i])) rows.push(lines[i++]);
      const cells = (r) => r.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => mdInline(c.trim()));
      const body = rows.filter((r) => !/^\s*\|?\s*:?-{2,}/.test(r));
      if (body.length) out.push(`<table class="md-t"><thead><tr>${cells(body[0]).map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>${body.slice(1).map((r) => `<tr>${cells(r).map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
      continue;
    }
    if (isList(ln)) { const items = []; while (i < lines.length && isList(lines[i])) items.push(lines[i++]); out.push(mdList(items)); continue; }
    if (!ln.trim()) { i++; continue; }
    const para = [];
    while (i < lines.length && lines[i].trim() && !isHead(lines[i]) && !isTable(lines[i]) && !isList(lines[i])) para.push(lines[i++]);
    out.push(`<p>${mdInline(para.join(" "))}</p>`);
  }
  return out.join("");
}

const pageChip = (id, star) => { const p = STATE.okf.pagesById[id]; return `<button class="ctx${star ? " gold" : ""}" data-page="${esc(id)}" title="${esc(id)}">${star ? "★ " : ""}${esc(p ? p.title : id)}</button>`; };

function renderOkfPage(p) {
  const pills = [`<span class="pill">${esc(p.id)}</span>`, `<span class="pill">${esc(roundLabel(p.round))} ${esc(t("p_round"))}</span>`,
    `<span class="pill ${p.verified ? "good" : "bad"}">${p.verified ? "✓ " : "✕ "}${esc(t("p_verified"))}</span>`, `<span class="pill">${p.n_chars} ${esc(STATE.lang === "ko" ? "자" : "chars")}</span>`];
  $("#question-card").innerHTML = `<div class="q-meta">${pills.join("")}</div><p class="q-text">${esc(p.title)}</p>`;
  $("#flow").innerHTML = "";
  const langs = [["ko", "한국어"], ["en", "English"], ["de", "Deutsch"]];
  const aliases = `<div class="alias-rows">${langs.map(([l, name]) => `<div class="alias-row"><span class="alias-lang">${name}</span><div class="ctx-list">${(p.names[l] || []).map((n) => `<span class="ctx static">${esc(n)}</span>`).join("") || `<span class="empty">${esc(t("p_none"))}</span>`}</div></div>`).join("")}</div>`;
  const related = `<div class="col-title">${esc(t("p_related"))} · ${p.related.length}</div><div class="ctx-list">${p.related.map((id) => pageChip(id)).join("") || `<span class="empty">${esc(t("p_none"))}</span>`}</div>` +
    `<div class="col-title">${esc(t("p_backlinks"))} · ${p.backlinks.length}</div><div class="ctx-list">${p.backlinks.map((id) => pageChip(id)).join("") || `<span class="empty">${esc(t("p_none"))}</span>`}</div>`;
  const body = `<div class="md">${md(p.body)}</div><p class="note">${esc(t("p_author"))}: ${esc(p.author)}</p>`;
  const used = STATE.okf.questions.filter((q) => q.kb.match.ids.includes(p.id) || (q.pages || []).includes(p.id));
  const rows = used.map((q) => `<li class="q-row" data-q="${esc(q.qid)}"><span class="pill">${esc(q.qid)}</span><span class="pill soft">${q.kb.match.ids.includes(p.id) ? esc(t("p_matched")) : esc(t("p_context"))}</span><span class="q-row-text">${esc(q.question)}</span>${q.human ? gradePill(q.human) : `<span class="pill soft">${esc(t("path_none"))}</span>`}</li>`).join("");
  $("#stages").innerHTML = [
    staticCard(1, t("p_aliases"), t("w_aliases"), aliases),
    staticCard(2, t("p_related"), t("w_related"), related),
    staticCard(3, t("p_body"), t("w_body"), body),
    staticCard(4, t("p_used"), t("w_used"), rows ? `<ul class="q-rows">${rows}</ul>` : `<p class="empty">${esc(t("p_none"))}</p>`),
  ].join("");
}

// ---------- PDF 세트: 문서가 청크가 되는 과정 (정적) ----------
async function ensurePdfChunks() {
  if (!STATE.pdfChunks) STATE.pdfChunks = getJSON("data/pdfchunks.json").then((d) => { Object.assign(STATE.chunks, d); return d; });
  return STATE.pdfChunks;
}
const SEC_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#6250d6", "#d6a12a", "#d03b7a", "#2ab0c8", "#8a8a3a"];

function hbars(rows, dropped) {
  // rows: [key, count]; 가로 막대 (최댓값 기준)
  const max = Math.max(1, ...rows.map((r) => r[1]));
  return `<ul class="hbars">${rows.map(([k, n]) => `<li class="hbar${dropped.has(k) ? " dropped" : ""}"><span class="hb-label">${esc(t("role_" + k))}${dropped.has(k) ? ` <span class="hb-x">✕ ${esc(t("d_dropped"))}</span>` : ""}</span><span class="bar"><span style="width:${(100 * n / max).toFixed(1)}%"></span></span><span class="hb-n">${n}</span></li>`).join("")}</ul>`;
}

function renderPdfDoc(d) {
  const pills = [`<span class="pill">${esc(d.lang)}</span>`, `<span class="pill">${d.pages} ${esc(STATE.lang === "ko" ? "쪽" : "pages")}</span>`, `<span class="pill">${esc(d.license)}</span>`, `<span class="pill gold">${d.stats.n_chunks} ${esc(t("d_chunk_n"))}</span>`];
  $("#question-card").innerHTML = `<div class="q-meta">${pills.join("")}</div><p class="q-text"><a href="${esc(d.url)}" rel="noopener">${esc(d.title)}</a></p>`;
  $("#flow").innerHTML = "";
  $("#stages").innerHTML = `<p class="empty">…</p>`;
  ensurePdfChunks().then(() => { if (cur() === d) renderPdfDocCards(d); });
}

function renderPdfDocCards(d) {
  const unit = t("d_count");
  // 1. 원본
  const source = `<dl class="kv"><dt>${esc(t("d_lang"))}</dt><dd>${esc(d.lang)}</dd><dt>${esc(t("d_pages"))}</dt><dd>${d.pages}</dd><dt>${esc(t("d_license"))}</dt><dd>${esc(d.license)}</dd><dt>${esc(t("d_sha"))}</dt><dd><code>${esc(d.sha256.slice(0, 16))}…</code></dd><dt>${esc(t("d_tool"))}</dt><dd>${esc(d.extractor.tool)} · <code>${esc(d.extractor.pdf_editor_commit.slice(0, 7))}</code></dd><dt>PDF</dt><dd><a href="${esc(d.pdf_url)}" rel="noopener">${esc(d.pdf_url)}</a></dd></dl>`;
  // 2. 레이아웃 복원 블록 (원본 블록 파일이 있을 때)
  const dropped = new Set(["header", "footer", "figure", "image", "vector"]);
  let layout, drop;
  if (d.raw) {
    const rows = Object.entries(d.raw.paragraphs).sort((a, b) => b[1] - a[1]);
    rows.push(["table", d.raw.tables], ...Object.entries(d.raw.figures).map(([k, n]) => [k, n]));
    layout = hbars(rows, dropped);
    const dr = d.raw.dropped;
    drop = `<div class="cols"><div><div class="col-title">✕ ${esc(t("d_dropped"))}</div><ul class="checks">` +
      [["header", dr.header], ["footer", dr.footer], ["figure", dr.figure]].map(([k, n]) => `<li><span class="ic no">✕</span><span>${esc(t("role_" + k))} · ${n}${unit}</span></li>`).join("") +
      `<li><span class="ic no">✕</span><span>${esc(t("d_toc"))} · ${dr.toc_lines}${unit}</span></li><li><span class="ic no">✕</span><span>${esc(t("d_drop_sections"))} · ${dr.sections.length}${unit}${dr.sections.length ? ` (${esc(dr.sections.join(", "))})` : ""}</span></li></ul></div>` +
      `<div><div class="col-title">✓ ${esc(t("d_kept"))}</div><ul class="checks">${Object.entries(d.kept).map(([k, n]) => `<li><span class="ic ok">✓</span><span>${esc(t("role_" + k.replace("paragraph:", "")))} · ${n}${unit}</span></li>`).join("")}</ul><div class="gold-line">${esc(t("d_chars"))}: ${d.n_chars.toLocaleString()}</div></div></div>`;
  } else {
    layout = `<p class="empty">${esc(t("d_raw_missing"))}</p>`;
    drop = `<div class="col-title">✓ ${esc(t("d_kept"))}</div><ul class="checks">${Object.entries(d.kept).map(([k, n]) => `<li><span class="ic ok">✓</span><span>${esc(t("role_" + k.replace("paragraph:", "")))} · ${n}${unit}</span></li>`).join("")}</ul>`;
  }
  // 3. 절
  const secRows = d.sections.map((s, i) => `<li class="sec-row"><span class="swatch" style="background:${SEC_COLORS[i % SEC_COLORS.length]}"></span><span class="sec-name">${esc(s.path.join(" › ") || "-")}</span><span class="sec-n">${(s.end - s.start).toLocaleString()} ${esc(STATE.lang === "ko" ? "자" : "chars")}</span><span class="sec-n">${s.chunks.length ? `#${s.chunks[0]}–#${s.chunks[s.chunks.length - 1]} (${s.chunks.length})` : "-"}</span></li>`).join("");
  const sections = `<div class="gold-line">${d.sections.length} ${esc(t("d_sections"))}</div><ol class="sec-list">${secRows}</ol>`;
  // 4. 청크 지도 + 통계
  const st = d.stats;
  const stats = `<dl class="kv"><dt>${esc(t("d_chunk_n"))}</dt><dd>${st.n_chunks}</dd><dt>${esc(t("d_tok"))}</dt><dd>${st.tokens_mean} · ${st.tokens_min} · ${st.tokens_max}</dd><dt>${esc(t("d_ov"))}</dt><dd>${st.n_overlap} / ${st.n_chunks - 1}</dd><dt>${esc(t("d_ov_chars"))}</dt><dd>${st.overlap_chars_mean}</dd><dt>${esc(t("d_th"))}</dt><dd>${st.n_th}</dd><dt>${esc(t("d_span"))}</dt><dd>${st.n_spanning}</dd></dl>`;
  const map = `<div class="seg-map">${d.chunks.map((c) => `<button type="button" class="seg${c.th ? " th" : ""}" style="flex:${c.end - c.start} 0 0;background:${SEC_COLORS[c.section % SEC_COLORS.length]}" data-cid="${esc(d.id)}#${c.idx}" title="#${c.idx} · ${c.tokens} tok · ${esc(d.sections[c.section].path.join(" › "))}${c.th ? " · table header" : ""}"></button>`).join("")}</div>` +
    `<div class="legend"><span>${esc(STATE.lang === "ko" ? "폭 = 문자 수, 색 = 절, 테두리 = 표 머리글 반복" : "width = characters, colour = section, outline = repeated table header")}</span></div>`;
  // 5. 예시: 오버랩
  const chunkBox = (c, html, extra) => `<div class="chunk-ex"><div class="chunk-head"><button class="cid" data-cid="${esc(d.id)}#${c.idx}">${esc(d.id)}#${c.idx}</button><span class="timing">${c.tokens} tok · ${esc(t("d_range"))} ${c.start.toLocaleString()}–${c.end.toLocaleString()}${extra || ""}</span></div><pre class="chunk-text">${html}</pre></div>`;
  let exOverlap = `<p class="empty">-</p>`;
  if (d.examples.overlap) {
    const trio = d.examples.overlap.map((i) => d.chunks[i]);
    exOverlap = `<div class="chunk-stack">${trio.map((c, k) => {
      const text = STATE.chunks[`${d.id}#${c.idx}`]?.text || "";
      const head = k > 0 ? c.ov_prev : 0, tail = k < trio.length - 1 ? trio[k + 1].ov_prev : 0;
      const html = (head ? `<mark class="ov">${esc(text.slice(0, head))}</mark>` : "") + esc(text.slice(head, text.length - tail)) + (tail ? `<mark class="ov">${esc(text.slice(text.length - tail))}</mark>` : "");
      return chunkBox(c, html, head ? ` · ${esc(STATE.lang === "ko" ? "겹침" : "overlap")} ${head}` : "");
    }).join("")}</div>`;
  }
  // 6. 예시: 표 머리글
  let exTable = `<p class="empty">${esc(t("d_no_table"))}</p>`;
  if (d.examples.table != null) {
    const c = d.chunks[d.examples.table], text = STATE.chunks[`${d.id}#${c.idx}`]?.text || "";
    exTable = `<div class="chunk-stack">${chunkBox(c, `<mark class="th">${esc(text.slice(0, c.th))}</mark>${esc(text.slice(c.th))}`, ` · ${esc(STATE.lang === "ko" ? "붙인 머리글" : "prefix")} ${c.th}`)}</div>`;
  }
  $("#stages").innerHTML = [
    staticCard(1, t("d_source"), t("w_source"), source),
    staticCard(2, t("d_layout"), t("w_layout"), layout),
    staticCard(3, t("d_drop"), t("w_drop"), drop),
    staticCard(4, t("d_sections"), t("w_sections"), sections),
    staticCard(5, t("d_chunks"), t("w_chunks"), stats + map),
    staticCard(6, t("d_ex_overlap"), t("w_ex_overlap"), exOverlap),
    staticCard(7, t("d_ex_table"), t("w_ex_table"), exTable),
  ].join("");
}

init().catch((e) => { document.querySelector("main").insertAdjacentHTML("afterbegin", `<p class="empty">Failed to load data: ${esc(e.message)}</p>`); });
