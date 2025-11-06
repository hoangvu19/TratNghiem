async function fetchQuestions(){
  const res = await fetch('data/questions.json');
  return res.json();
}

const el = id=>document.getElementById(id);
let questions = [];
let current = 0;
let selected = {};
let submitted = false;

// Deduplication helpers: normalize text, compute Jaccard similarity on token sets
function normalizeText(s){
  if(!s) return '';
  // remove diacritics, lower-case, remove punctuation
  try{
    s = s.normalize('NFD').replace(/\p{M}/gu, '');
  }catch(e){
    // fallback: common unicode combining marks range
    s = s.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  return s.toLowerCase().replace(/["'`\-–—\(\)\[\]{}.,:;?!\/\\]/g,' ').replace(/\s+/g,' ').trim();
}

function tokensFromText(s){
  const n = normalizeText(s);
  return Array.from(new Set(n.split(/\s+/).filter(t=>t && t.length>1)));
}

function jaccardSimilarity(aTokens,bTokens){
  const A = new Set(aTokens); const B = new Set(bTokens);
  let inter = 0;
  for(const t of A) if(B.has(t)) inter++;
  const uni = new Set([...A,...B]).size;
  return uni === 0 ? 0 : inter/uni;
}

function dedupeQuestions(list, threshold=0.6){
  // keep first occurrence, drop any item whose content is very similar to a kept one
  const kept = [];
  const keptTokens = [];
  for(const q of list){
    const content = (q.question||'') + ' ' + ((q.choices && q.choices.join(' ')) || (q.shortAnswer||''));
    const toks = tokensFromText(content);
    let isDup = false;
    for(const kt of keptTokens){
      // quick substring check: if one content contains other (after normalize) treat as duplicate
      const a = normalizeText(content);
      const b = normalizeText(kt._raw || '');
      if(a && b && (a.includes(b) || b.includes(a))){ isDup = true; break; }
      const sim = jaccardSimilarity(toks, kt.tokens||[]);
      if(sim >= threshold){ isDup = true; break; }
    }
    if(!isDup){ kept.push(q); keptTokens.push({ tokens: toks, _raw: content }); }
  }
  return kept;
}

async function start(){
  questions = await fetchQuestions();
  // remove duplicates / near-duplicates so users won't see repeated questions
  const before = questions.length;
  try{
    questions = dedupeQuestions(questions, 0.65);
  }catch(e){ console.warn('Deduplication failed:', e); }
  const removed = before - questions.length;
  // show a short notice to user (dedupe info); prefer visible #notice, fallback to import-result
  const noticeEl = el('notice') || el('import-result');
  if(noticeEl){
    if(removed>0) noticeEl.textContent = `Đã loại ${removed} câu trùng/giống trước khi bắt đầu.`; else noticeEl.textContent = '';
  }
  // read mode/options
  const mode = el('mode').value;
  const num = Math.min(Math.max(1, parseInt(el('num').value||10)), questions.length);
  const optShuffle = !!el('opt-shuffle') && el('opt-shuffle').checked;
  const optLimit = !!el('opt-limit') && el('opt-limit').checked;
  const optTextCheck = !!el('opt-text-check') && el('opt-text-check').checked;
  // attach options to global for use in render/submit
  window.__quizOptions = { optShuffle, optLimit, optTextCheck };
  // shuffle pool if requested (before slicing)
  if(optShuffle) questions = shuffle(questions.slice());
  questions = questions.slice(0,num);
  submitted = false;
  if(mode === 'quiz') showQuiz(); else if(mode === 'short_practice') startShortPractice(); else showAnswers();
}

function startShortPractice(){
  // open a minimal short-answer practice UI using same quiz-area
  el('quiz-area').classList.remove('hidden');
  el('answers-area').classList.add('hidden');
  el('result-area').classList.add('hidden');
  current = 0; selected = {};
  el('q-total').textContent = questions.length;
  renderQuestion();
}

function shuffle(a){
  for(let i=a.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]
  }
  return a;
}

function showQuiz(){
  el('quiz-area').classList.remove('hidden');
  el('answers-area').classList.add('hidden');
  el('result-area').classList.add('hidden');
  current = 0; selected = {};
  el('q-total').textContent = questions.length;
  renderQuestion();
}

function renderQuestion(){
  const q = questions[current];
  el('q-index').textContent = current+1;
  el('question').textContent = q.question;
  const choices = el('choices'); choices.innerHTML='';
  if(q.type === 'mcq'){
    q.choices.forEach((c,i)=>{
      const li = document.createElement('li'); li.textContent = c; li.dataset.idx = i;
      const opts = window.__quizOptions || {};
      const limitNow = !!opts.optLimit && !submitted;
      if(selected[q.id] === i) li.classList.add('selected');
      // if already submitted, mark correct/wrong and disable selection
      if(submitted){
        if(typeof q.answer === 'number'){
          if(i === q.answer) li.classList.add('correct');
          if(selected[q.id] === i && selected[q.id] !== q.answer) li.classList.add('wrong');
        }
        // do not add click handler when submitted
      } else {
        li.addEventListener('click',()=>{
          // if limit option is on, lock this question after selecting and show immediate feedback
          selected[q.id]=i;
          if(limitNow && typeof q.answer === 'number'){
            // mark correct/wrong on this render and prevent further changes by setting a flag
            // store a locked map on window
            window.__locked = window.__locked || {};
            window.__locked[q.id] = true;
          }
          renderQuestion();
        });
      }
      // if this question was locked by limit option, show correct/wrong visuals immediately
      if(window.__locked && window.__locked[q.id]){
        if(typeof q.answer === 'number'){
          if(i === q.answer) li.classList.add('correct');
          if(selected[q.id] === i && selected[q.id] !== q.answer) li.classList.add('wrong');
        }
        // remove pointer events to prevent changes
        li.style.pointerEvents = 'none';
      }
      choices.appendChild(li);
    });
    // show correct answer text if submitted
    if(submitted){
      const info = document.createElement('div'); info.style.marginTop='8px'; info.style.fontStyle='italic';
      if(typeof q.answer === 'number'){
        info.textContent = 'Đáp án đúng: ' + q.choices[q.answer];
      } else if(q.shortAnswer){
        info.textContent = 'Đáp án: ' + q.shortAnswer;
      }
      choices.appendChild(info);
    }
  } else {
    const ta = document.createElement('textarea'); ta.value = selected[q.id]||''; ta.rows=4; ta.style.width='100%';
    ta.addEventListener('input',e=>selected[q.id]=e.target.value);
    // if Limit option is on and not submitted, we show immediate check button
    const opts = window.__quizOptions || {};
    const showCheck = opts.optLimit;
    const textCheck = opts.optTextCheck;
    const feedbackDiv = document.createElement('div'); feedbackDiv.style.marginTop='8px';

    const checkAnswer = async ()=>{
      const user = (selected[q.id]||'').trim();
      if(user.length===0){ feedbackDiv.textContent = 'Bạn chưa nhập trả lời.'; return; }
      // client-side fuzzy check when q.shortAnswer exists
      let score = null; let verdict = '';
      // simple text-based check: token overlap (AI removed)
      const a = tokensFromText(q.shortAnswer||''); const b = tokensFromText(user);
      const sim = jaccardSimilarity(a,b);
      score = Math.round(sim*100);
      verdict = `Độ khớp: ${score}%`;
      feedbackDiv.textContent = verdict;
      // if optLimit show green/red
      if(opts.optLimit){
        feedbackDiv.style.fontWeight='bold';
        if(score>=70) feedbackDiv.style.color='green'; else feedbackDiv.style.color='crimson';
      }
    };

    if(showCheck){
      const btn = document.createElement('button'); btn.textContent = 'Kiểm tra'; btn.style.marginTop='8px';
      btn.addEventListener('click', checkAnswer);
      choices.appendChild(btn);
    }

    if(submitted){
      ta.disabled = true;
      const ans = document.createElement('div'); ans.style.marginTop='8px'; ans.style.fontStyle='italic'; ans.textContent = 'Đáp án ngắn: ' + (q.shortAnswer||'');
      choices.appendChild(ans);
    }
    choices.appendChild(ta);
    choices.appendChild(feedbackDiv);
  }
}

function prev(){ if(current>0){current--; renderQuestion();} }
function next(){ if(current<questions.length-1){current++; renderQuestion();} }

function submit(){
  // mark submitted and show per-question correct/wrong
  submitted = true;
  // re-render current question to show markings
  renderQuestion();
  // compute score for mcq and show basic result; short answers require AI grading or manual check
  let correct=0; let total=0;
  questions.forEach((q)=>{
    if(q.type === 'mcq'){
      total++;
      const user = selected[q.id];
      if(user === q.answer) correct++;
    }
  });
  // show result panel
  el('quiz-area').classList.add('hidden');
  el('answers-area').classList.add('hidden');
  el('result-area').classList.remove('hidden');
  el('score').textContent = `Bạn đạt ${correct} / ${total} (đúng). Short-answer: dùng nút Kiểm tra/AI để chấm từng câu.`;
}

function showAnswers(){
  el('quiz-area').classList.add('hidden');
  el('answers-area').classList.remove('hidden');
  el('result-area').classList.add('hidden');
  const container = el('answers-list'); container.innerHTML='';
  questions.forEach((q,idx)=>{
    const div = document.createElement('div'); div.className='item';
    const h = document.createElement('div'); h.innerHTML = `<strong>${idx+1}.</strong> ${q.question}`;
    const sa = document.createElement('div'); sa.style.marginTop='6px'; sa.innerHTML = `<em>Đáp án ngắn:</em> ${q.shortAnswer || ''}`;
    div.appendChild(h); div.appendChild(sa); container.appendChild(div);
  });
}

function restart(){ el('result-area').classList.add('hidden'); el('quiz-area').classList.remove('hidden'); current=0; selected={}; renderQuestion(); }

// event wiring
el('start').addEventListener('click', start);
el('prev').addEventListener('click', prev);
el('next').addEventListener('click', next);
el('submit').addEventListener('click', submit);
el('restart').addEventListener('click', restart);

// initial: hide all
window.addEventListener('load',()=>{
  el('quiz-area').classList.add('hidden'); el('answers-area').classList.add('hidden'); el('result-area').classList.add('hidden');
});

// Server link helpers
function setServerLink(){
  const a = el('server-link');
  let url = 'http://localhost:8000';
  try{ if(location && location.origin && location.origin !== 'null') url = location.origin; }catch(e){}
  a.href = url; a.textContent = url;
}

setServerLink();

el('open-server').addEventListener('click',()=>{
  const url = el('server-link').href; window.open(url, '_blank');
});
el('copy-server').addEventListener('click',async ()=>{
  const url = el('server-link').href;
  try{ await navigator.clipboard.writeText(url); alert('Đã sao chép: '+url); }catch(e){ prompt('Copy URL này:', url); }
});

// Import / Export bulk questions
function parseImportText(text){
  const lines = text.split(/\r?\n/).map(l=>l.trim()).filter(l=>l.length>0);
  const out = [];
  let i=0; let idBase = Date.now()%100000;
  while(i<lines.length){
    const qline = lines[i++];
    // next lines may contain choices (start with A. B. C.) or ShortAnswer
    const choices = [];
    let answerIndex = null;
    let shortAnswer = '';
    while(i<lines.length && /^([A-Da-d]\.|\*?[A-Da-d]\.)/.test(lines[i]) || /^Đáp án:|^ShortAnswer:|^Đáp án ngắn:|^Answer:/i.test(lines[i])){
      const ln = lines[i++];
      const m = ln.match(/^\*?([A-Da-d])\.\s*(.*)$/);
      if(m){
        const label = m[1].toUpperCase(); const text = m[2];
        const idx = label.charCodeAt(0)-65; choices.push(text);
        if(/^[*]/.test(ln) || /^\*/.test(ln) || ln.startsWith('*')) answerIndex = idx;
      } else {
        const am = ln.match(/(Đáp án|Answer)\s*[:\-]?\s*([A-Da-d0-9]+)/i);
        if(am){
          const v = am[2].toUpperCase(); if(/[A-D]/.test(v)) answerIndex = v.charCodeAt(0)-65; else if(/^[0-9]+$/.test(v)) answerIndex = parseInt(v,10)-1;
        }
        const sm = ln.match(/^(ShortAnswer:|Đáp án ngắn:)\s*(.*)$/i);
        if(sm) shortAnswer = sm[2];
      }
    }
    const q = { id: idBase++, question: qline };
    if(choices.length>0){ q.type='mcq'; q.choices = choices; q.answer = (answerIndex===null?null:answerIndex); q.shortAnswer = shortAnswer || null; }
    else { q.type='short'; q.shortAnswer = shortAnswer || ''; }
    out.push(q);
  }
  return out;
}

el('import-parse').addEventListener('click',()=>{
  const t = el('import-area').value; if(!t.trim()){ alert('Dán nội dung vào ô trước.'); return; }
  const parsed = parseImportText(t);
  if(parsed.length===0){ el('import-result').textContent='Không tìm được câu nào.'; return; }
  // append to questions source and show count
  fetch('data/questions.json').then(r=>r.json()).then(existing=>{
    const merged = existing.concat(parsed.map((p,idx)=>({ id: existing.length+idx+1, ...p })));
    // overwrite in-memory questions and allow export
    questions = merged;
    el('import-result').textContent = `Đã thêm ${parsed.length} câu. Tổng hiện có ${merged.length} câu.`;
  }).catch(err=>{ alert('Không thể đọc data/questions.json: '+err.message); });
});

el('export-json').addEventListener('click',()=>{
  const data = JSON.stringify(questions, null, 2);
  const blob = new Blob([data], {type:'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href = url; a.download = 'questions_export.json'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
});

// quick error catch for fetch when opened via file://
window.addEventListener('error',e=>{
  if(e.message && e.message.includes('Failed to fetch')){
    console.warn('Could not load questions.json via fetch when opened with file://. Run a local HTTP server (e.g. python -m http.server) or use a browser that allows file fetch.');
  }
});