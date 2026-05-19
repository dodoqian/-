#!/usr/bin/env python3
"""Generate self-contained quiz.html from the question bank JSON."""

import json
import re

def escape_js_string(s):
    """Escape a string for safe embedding in a JavaScript template literal."""
    return s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')

def main():
    with open('deepseek_json_20260519_1e3487.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    tf_questions = data['true_false_questions']
    mc_questions = data['multiple_choice_questions']

    # Build compact JS data strings
    tf_js = []
    for q in tf_questions:
        tf_js.append({
            'id': q['id'],
            's': q['statement'],
            'a': q['answer'],
            'e': q['explanation']
        })

    mc_js = []
    for q in mc_questions:
        mc_js.append({
            'id': q['id'],
            'q': q['question'],
            'o': q['options'],
            'a': q['answer'],
            'e': q['explanation']
        })

    tf_json = json.dumps(tf_js, ensure_ascii=False, separators=(',', ':'))
    mc_json = json.dumps(mc_js, ensure_ascii=False, separators=(',', ':'))

    html = HTML_TEMPLATE.replace('/* __TF_DATA__ */', tf_json).replace('/* __MC_DATA__ */', mc_json)

    with open('quiz.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'Generated quiz.html ({len(html)} bytes)')
    print(f'  True/False: {len(tf_questions)} questions')
    print(f'  Multiple Choice: {len(mc_questions)} questions')

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人工智能训练师 - 在线答题工具</title>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #f0f4f8;
  color: #1e293b;
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 20px;
}
.app { width: 100%; max-width: 720px; margin-top: 20px; }

/* Header */
.header {
  text-align: center; padding: 24px 0 16px;
}
.header h1 {
  font-size: 1.5rem; font-weight: 700; color: #1e40af;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
.header .subtitle { font-size: 0.85rem; color: #64748b; margin-top: 4px; }

/* Cards */
.card {
  background: #fff; border-radius: 16px; padding: 28px 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04);
  margin-bottom: 16px;
}

/* Setup Screen */
.setup-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 20px; }
.mode-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }
.mode-card {
  padding: 20px 12px; border: 2px solid #e2e8f0; border-radius: 12px;
  text-align: center; cursor: pointer; transition: all 0.2s;
}
.mode-card:hover { border-color: #93c5fd; background: #f8fafc; }
.mode-card.active { border-color: #2563eb; background: #eff6ff; }
.mode-card .icon { font-size: 2rem; display: block; margin-bottom: 8px; }
.mode-card .label { font-weight: 600; font-size: 0.95rem; }
.mode-card .desc { font-size: 0.75rem; color: #64748b; margin-top: 4px; }

.count-row { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; flex-wrap: wrap; }
.count-row .label-text { font-weight: 600; font-size: 0.9rem; white-space: nowrap; }
.count-options { display: flex; gap: 8px; flex-wrap: wrap; }
.count-btn {
  padding: 8px 20px; border: 2px solid #e2e8f0; border-radius: 20px;
  background: #fff; cursor: pointer; font-size: 0.9rem; font-weight: 500;
  transition: all 0.15s;
}
.count-btn:hover { border-color: #93c5fd; }
.count-btn.active { border-color: #2563eb; background: #eff6ff; color: #1e40af; font-weight: 600; }

.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px 28px; border: none; border-radius: 10px; font-size: 1rem;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn:active { transform: scale(0.97); }
.btn-primary { background: #2563eb; color: #fff; width: 100%; }
.btn-primary:hover { background: #1d4ed8; }
.btn-outline { background: #fff; border: 2px solid #e2e8f0; color: #475569; }
.btn-outline:hover { background: #f8fafc; }
.btn-danger { background: #fef2f2; border: 2px solid #fecaca; color: #dc2626; }
.btn-danger:hover { background: #fee2e2; }
.btn-success { background: #f0fdf4; border: 2px solid #bbf7d0; color: #16a34a; }
.btn-success:hover { background: #dcfce7; }
.btn-sm { padding: 6px 14px; font-size: 0.82rem; border-radius: 8px; }

/* Quiz Screen */
.quiz-header {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.progress-bar-wrap { flex: 1; min-width: 200px; }
.progress-info { display: flex; justify-content: space-between; font-size: 0.82rem; color: #64748b; margin-bottom: 6px; }
.progress-bar {
  height: 8px; background: #e2e8f0; border-radius: 4px; overflow: hidden;
}
.progress-fill { height: 100%; background: #2563eb; border-radius: 4px; transition: width 0.3s; }

.quiz-question {
  font-size: 1.08rem; font-weight: 500; line-height: 1.7; margin-bottom: 24px;
  padding: 16px; background: #f8fafc; border-radius: 10px; border-left: 4px solid #2563eb;
}
.quiz-question .q-tag {
  display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 2px 8px;
  border-radius: 4px; margin-right: 8px; vertical-align: 2px;
}
.tag-tf { background: #dbeafe; color: #1e40af; }
.tag-mc { background: #fef3c7; color: #92400e; }

.options-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 24px; }
.option-item {
  display: flex; align-items: center; gap: 12px; padding: 14px 16px;
  border: 2px solid #e2e8f0; border-radius: 10px; cursor: pointer;
  transition: all 0.15s; font-size: 0.95rem;
}
.option-item:hover { border-color: #93c5fd; background: #f8fafc; }
.option-item.selected { border-color: #2563eb; background: #eff6ff; }
.option-item.correct { border-color: #16a34a; background: #f0fdf4; }
.option-item.wrong { border-color: #dc2626; background: #fef2f2; }
.option-item .opt-letter {
  width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0;
  background: #f1f5f9; color: #64748b;
}
.option-item.selected .opt-letter { background: #2563eb; color: #fff; }
.option-item.correct .opt-letter { background: #16a34a; color: #fff; }
.option-item.wrong .opt-letter { background: #dc2626; color: #fff; }
.option-item.disabled { pointer-events: none; opacity: 0.85; }

.answer-feedback {
  padding: 16px; border-radius: 10px; margin-bottom: 20px; font-size: 0.92rem; line-height: 1.6;
}
.feedback-correct { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
.feedback-wrong { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
.feedback-icon { font-size: 1.3rem; margin-right: 6px; }

.quiz-actions { display: flex; gap: 10px; }

/* Result Screen */
.result-score {
  text-align: center; padding: 32px 0;
}
.score-circle {
  width: 140px; height: 140px; border-radius: 50%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; margin: 0 auto 16px;
  border: 6px solid;
}
.score-circle.great { border-color: #16a34a; color: #16a34a; }
.score-circle.good { border-color: #2563eb; color: #2563eb; }
.score-circle.ok { border-color: #d97706; color: #d97706; }
.score-circle.poor { border-color: #dc2626; color: #dc2626; }
.score-num { font-size: 2.8rem; font-weight: 800; line-height: 1; }
.score-unit { font-size: 1rem; }
.score-text { font-size: 1.05rem; font-weight: 600; color: #475569; }
.score-detail { display: flex; justify-content: center; gap: 32px; margin: 16px 0 24px; }
.score-stat { text-align: center; }
.score-stat .val { font-size: 1.5rem; font-weight: 700; }
.score-stat .lbl { font-size: 0.78rem; color: #64748b; }

.result-list { margin-top: 16px; }
.result-item {
  padding: 14px; border-radius: 10px; margin-bottom: 8px; font-size: 0.9rem; line-height: 1.6;
}
.result-item.correct { background: #f0fdf4; border: 1px solid #bbf7d0; }
.result-item.wrong { background: #fef2f2; border: 1px solid #fecaca; }
.result-item .result-badge {
  display: inline-block; font-size: 0.72rem; padding: 1px 8px; border-radius: 10px;
  font-weight: 600; margin-right: 8px;
}
.badge-correct { background: #16a34a; color: #fff; }
.badge-wrong { background: #dc2626; color: #fff; }
.result-item .explanation-text { font-size: 0.83rem; color: #64748b; margin-top: 6px; padding-top: 6px; border-top: 1px dashed #e2e8f0; }

/* Wrong Answer Book */
.wrong-book-empty { text-align: center; padding: 40px 20px; color: #64748b; }
.wrong-book-empty .big-icon { font-size: 3rem; margin-bottom: 12px; }
.wrong-book-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.wrong-filter { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.wrong-filter .filter-btn {
  padding: 5px 14px; font-size: 0.8rem; border-radius: 16px; border: 1.5px solid #e2e8f0;
  background: #fff; cursor: pointer; transition: all 0.15s;
}
.wrong-filter .filter-btn.active { background: #eff6ff; border-color: #2563eb; color: #1e40af; }

/* Tabs for bottom nav */
.nav-tabs { display: flex; gap: 0; margin-bottom: 16px; background: #fff; border-radius: 12px; padding: 4px; }
.nav-tab {
  flex: 1; text-align: center; padding: 10px; border: none; background: none;
  cursor: pointer; font-size: 0.88rem; font-weight: 500; color: #64748b;
  border-radius: 10px; transition: all 0.15s;
}
.nav-tab:hover { color: #1e40af; }
.nav-tab.active { background: #2563eb; color: #fff; font-weight: 600; }

/* Utility */
.hidden { display: none !important; }
.text-center { text-align: center; }
.mt-12 { margin-top: 12px; }
.mb-12 { margin-bottom: 12px; }

@media (max-width: 600px) {
  .mode-grid { grid-template-columns: 1fr; }
  .quiz-actions { flex-direction: column; }
  .nav-tabs { flex-direction: column; }
  .score-detail { gap: 16px; }
}
</style>
</head>
<body>
<div class="app">
  <div class="header">
    <h1>&#x1F4DD; 人工智能训练师</h1>
    <div class="subtitle">理论知识复习 · 在线答题工具</div>
  </div>

  <!-- Navigation Tabs -->
  <div class="nav-tabs" id="navTabs">
    <button class="nav-tab active" data-screen="setup">&#x1F3E0; 答题</button>
    <button class="nav-tab" data-screen="wrongBook">&#x1F4DA; 错题本 <span id="wrongCountBadge"></span></button>
  </div>

  <!-- Setup Screen -->
  <div id="screenSetup">
    <div class="card">
      <div class="setup-title">选择答题模式</div>
      <div class="mode-grid" id="modeGrid">
        <div class="mode-card active" data-mode="tf">
          <span class="icon">&#x2705;</span>
          <div class="label">判断题</div>
          <div class="desc">对错判断 · 300题</div>
        </div>
        <div class="mode-card" data-mode="mc">
          <span class="icon">&#x1F4DD;</span>
          <div class="label">选择题</div>
          <div class="desc">四选一 · 300题</div>
        </div>
        <div class="mode-card" data-mode="mixed">
          <span class="icon">&#x1F504;</span>
          <div class="label">混合模式</div>
          <div class="desc">判断+选择 · 600题</div>
        </div>
      </div>

      <div class="count-row">
        <span class="label-text">题目数量</span>
        <div class="count-options" id="countOptions">
          <button class="count-btn" data-count="10">10题</button>
          <button class="count-btn active" data-count="20">20题</button>
          <button class="count-btn" data-count="30">30题</button>
          <button class="count-btn" data-count="50">50题</button>
          <button class="count-btn" data-count="100">100题</button>
          <button class="count-btn" data-count="0">全部</button>
        </div>
      </div>

      <button class="btn btn-primary" id="btnStart">&#x25B6; 开始答题</button>
    </div>
  </div>

  <!-- Quiz Screen -->
  <div id="screenQuiz" class="hidden">
    <div class="card">
      <div class="quiz-header">
        <div class="progress-bar-wrap">
          <div class="progress-info">
            <span id="progressLabel">第 1/20 题</span>
            <span id="scoreLabel">得分: 0</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%"></div>
          </div>
        </div>
        <button class="btn btn-outline btn-sm" id="btnQuit">退出</button>
      </div>

      <div class="quiz-question" id="questionText"></div>
      <div class="options-list" id="optionsList"></div>
      <div class="answer-feedback hidden" id="answerFeedback"></div>

      <div class="quiz-actions">
        <button class="btn btn-primary hidden" id="btnNext">下一题</button>
      </div>
    </div>
  </div>

  <!-- Result Screen -->
  <div id="screenResult" class="hidden">
    <div class="card">
      <div class="result-score" id="resultScore"></div>
      <div class="text-center" style="display: flex; gap: 10px; justify-content: center;">
        <button class="btn btn-primary" id="btnRetry">&#x1F504; 再来一局</button>
        <button class="btn btn-outline" id="btnHome">&#x1F3E0; 返回首页</button>
      </div>
      <div class="result-list mt-12" id="resultList"></div>
    </div>
  </div>

  <!-- Wrong Answer Book Screen -->
  <div id="screenWrongBook" class="hidden">
    <div class="card">
      <div class="wrong-book-header">
        <h3 style="font-size:1.05rem;">&#x1F4DA; 错题本</h3>
        <div style="display:flex;gap:8px;">
          <button class="btn btn-danger btn-sm hidden" id="btnClearWrong" style="font-size:0.78rem;">清空错题本</button>
        </div>
      </div>
      <div class="wrong-filter" id="wrongFilter">
        <button class="filter-btn active" data-filter="all">全部</button>
        <button class="filter-btn" data-filter="tf">判断题</button>
        <button class="filter-btn" data-filter="mc">选择题</button>
      </div>
      <div id="wrongBookContent"></div>
    </div>
  </div>
</div>

<script>
(function() {

// ─── Question Bank ────────────────────────────────────────────────
var TF_BANK = /* __TF_DATA__ */;
var MC_BANK = /* __MC_DATA__ */;

// ─── State ─────────────────────────────────────────────────────────
var STATE = {
  screen: 'setup',
  mode: 'tf',       // 'tf' | 'mc' | 'mixed'
  count: 20,
  questions: [],    // prepared questions for this session
  currentIndex: 0,
  score: 0,
  answered: false,
  sessionResults: [], // { question, userAnswer, correct, ... }
};

// ─── Helpers ───────────────────────────────────────────────────────
function shuffle(arr) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
  }
  return a;
}

function getWrongBook() {
  try {
    return JSON.parse(localStorage.getItem('quiz_wrong_book') || '[]');
  } catch(e) { return []; }
}

function saveWrongBook(book) {
  try { localStorage.setItem('quiz_wrong_book', JSON.stringify(book)); } catch(e) {}
}

function addToWrongBook(item) {
  var book = getWrongBook();
  // Avoid exact duplicates (same type + id)
  var dup = book.some(function(b) {
    return b.type === item.type && b.id === item.id;
  });
  if (!dup) {
    book.unshift(item); // newest first
    saveWrongBook(book);
  }
}

function removeFromWrongBook(type, id) {
  var book = getWrongBook();
  book = book.filter(function(b) { return !(b.type === type && b.id === id); });
  saveWrongBook(book);
}

// ─── Prepare Questions ─────────────────────────────────────────────
function prepareQuestions() {
  var pool = [];
  if (STATE.mode === 'tf' || STATE.mode === 'mixed') {
    TF_BANK.forEach(function(q) { pool.push({ type: 'tf', data: q }); });
  }
  if (STATE.mode === 'mc' || STATE.mode === 'mixed') {
    MC_BANK.forEach(function(q) { pool.push({ type: 'mc', data: q }); });
  }
  pool = shuffle(pool);
  var n = STATE.count || pool.length;
  return pool.slice(0, n);
}

// ─── Render: Setup ─────────────────────────────────────────────────
function renderSetup() {
  document.querySelectorAll('#modeGrid .mode-card').forEach(function(el) {
    el.classList.toggle('active', el.dataset.mode === STATE.mode);
  });
  document.querySelectorAll('#countOptions .count-btn').forEach(function(el) {
    el.classList.toggle('active', parseInt(el.dataset.count) === STATE.count);
  });
}

// ─── Render: Quiz ──────────────────────────────────────────────────
function renderQuestion() {
  var q = STATE.questions[STATE.currentIndex];
  var questionEl = document.getElementById('questionText');
  var optionsEl = document.getElementById('optionsList');
  var feedbackEl = document.getElementById('answerFeedback');
  var btnNext = document.getElementById('btnNext');
  var progressFill = document.getElementById('progressFill');
  var progressLabel = document.getElementById('progressLabel');
  var scoreLabel = document.getElementById('scoreLabel');

  STATE.answered = false;
  feedbackEl.classList.add('hidden');
  btnNext.classList.add('hidden');
  optionsEl.innerHTML = '';

  var total = STATE.questions.length;
  var idx = STATE.currentIndex;
  progressLabel.textContent = '第 ' + (idx + 1) + '/' + total + ' 题';
  scoreLabel.textContent = '得分: ' + STATE.score;
  progressFill.style.width = ((idx / total) * 100) + '%';

  if (q.type === 'tf') {
    questionEl.innerHTML = '<span class="q-tag tag-tf">判断题</span> ' + q.data.s;
    var labels = ['✔ 正确', '✘ 错误'];
    var values = [true, false];
    values.forEach(function(v, i) {
      var div = document.createElement('div');
      div.className = 'option-item';
      div.innerHTML = '<span class="opt-letter">' + (i === 0 ? 'Y' : 'N') + '</span>' + labels[i];
      div.addEventListener('click', function() { submitAnswer(v); });
      optionsEl.appendChild(div);
    });
  } else {
    questionEl.innerHTML = '<span class="q-tag tag-mc">选择题</span> ' + q.data.q;
    var letters = ['A', 'B', 'C', 'D'];
    q.data.o.forEach(function(opt, i) {
      var div = document.createElement('div');
      div.className = 'option-item';
      div.innerHTML = '<span class="opt-letter">' + letters[i] + '</span>' + opt;
      div.addEventListener('click', function() { submitAnswer(letters[i]); });
      optionsEl.appendChild(div);
    });
  }
}

function submitAnswer(userAnswer) {
  if (STATE.answered) return;
  STATE.answered = true;

  var q = STATE.questions[STATE.currentIndex];
  var isCorrect;
  if (q.type === 'tf') {
    isCorrect = (userAnswer === q.data.a);
  } else {
    isCorrect = (userAnswer === q.data.a);
  }

  if (isCorrect) {
    STATE.score++;
  } else {
    // Add to wrong book
    addToWrongBook({
      type: q.type,
      id: q.data.id,
      statement: q.type === 'tf' ? q.data.s : q.data.q,
      options: q.type === 'mc' ? q.data.o : null,
      correctAnswer: q.type === 'tf' ? (q.data.a ? '对' : '错') : q.data.a,
      userAnswer: q.type === 'tf' ? (userAnswer ? '对' : '错') : userAnswer,
      explanation: q.data.e
    });
  }

  STATE.sessionResults.push({
    q: q,
    userAnswer: userAnswer,
    isCorrect: isCorrect
  });

  // Highlight options
  var options = document.querySelectorAll('#optionsList .option-item');
  options.forEach(function(opt) { opt.classList.add('disabled'); });

  var feedbackEl = document.getElementById('answerFeedback');
  feedbackEl.classList.remove('hidden', 'feedback-correct', 'feedback-wrong');

  if (isCorrect) {
    feedbackEl.classList.add('feedback-correct');
    feedbackEl.innerHTML = '<span class="feedback-icon">&#x2705;</span> <strong>回答正确！</strong>';
    // Highlight correct option
    highlightCorrectOption(q, userAnswer, true);
  } else {
    feedbackEl.classList.add('feedback-wrong');
    var correctDisplay = q.type === 'tf' ? (q.data.a ? '正确' : '错误') : q.data.a + '. ' + q.data.o[q.data.a.charCodeAt(0) - 65];
    feedbackEl.innerHTML = '<span class="feedback-icon">&#x274C;</span> <strong>回答错误！</strong> 正确答案：' + correctDisplay;
    highlightCorrectOption(q, userAnswer, false);
  }

  if (q.data.e) {
    feedbackEl.innerHTML += '<div style="margin-top:8px;font-size:0.83rem;color:inherit;opacity:0.85;">&#x1F4A1; ' + q.data.e + '</div>';
  }

  var btnNext = document.getElementById('btnNext');
  btnNext.classList.remove('hidden');
  var isLast = STATE.currentIndex >= STATE.questions.length - 1;
  btnNext.textContent = isLast ? '查看结果' : '下一题';
}

function highlightCorrectOption(q, userAnswer, isCorrect) {
  var options = document.querySelectorAll('#optionsList .option-item');
  if (q.type === 'tf') {
    var tfValues = [true, false];
    options.forEach(function(opt, i) {
      var val = tfValues[i];
      if (val === q.data.a) opt.classList.add('correct');
      if (val === userAnswer && !isCorrect) opt.classList.add('wrong');
      if (val === userAnswer && isCorrect) opt.classList.add('correct');
    });
  } else {
    var letters = ['A', 'B', 'C', 'D'];
    var correctIdx = q.data.a.charCodeAt(0) - 65;
    var userIdx = userAnswer.charCodeAt(0) - 65;
    options[correctIdx].classList.add('correct');
    if (!isCorrect) options[userIdx].classList.add('wrong');
  }
}

function nextQuestion() {
  STATE.currentIndex++;
  if (STATE.currentIndex >= STATE.questions.length) {
    showScreen('result');
    renderResult();
  } else {
    renderQuestion();
  }
}

// ─── Render: Result ────────────────────────────────────────────────
function renderResult() {
  var total = STATE.questions.length;
  var score = STATE.score;
  var pct = total > 0 ? Math.round((score / total) * 100) : 0;

  var circleClass = pct >= 90 ? 'great' : pct >= 70 ? 'good' : pct >= 50 ? 'ok' : 'poor';
  var comment = pct >= 90 ? '太棒了！' : pct >= 70 ? '很不错！' : pct >= 50 ? '继续加油！' : '多多练习！';

  var html = '<div class="score-circle ' + circleClass + '">';
  html += '<span class="score-num">' + pct + '</span><span class="score-unit">分</span>';
  html += '</div>';
  html += '<div class="score-text">' + comment + '</div>';
  html += '<div class="score-detail">';
  html += '<div class="score-stat"><div class="val" style="color:#16a34a">' + score + '</div><div class="lbl">正确</div></div>';
  html += '<div class="score-stat"><div class="val" style="color:#dc2626">' + (total - score) + '</div><div class="lbl">错误</div></div>';
  html += '<div class="score-stat"><div class="val" style="color:#64748b">' + total + '</div><div class="lbl">总题数</div></div>';
  html += '</div>';
  document.getElementById('resultScore').innerHTML = html;

  // Review list
  var listHtml = '<h4 style="margin-bottom:12px;">&#x1F4CB; 答题详情</h4>';
  STATE.sessionResults.forEach(function(r, i) {
    var cls = r.isCorrect ? 'correct' : 'wrong';
    var badgeCls = r.isCorrect ? 'badge-correct' : 'badge-wrong';
    var badgeText = r.isCorrect ? '✔ 正确' : '✘ 错误';
    var q = r.q;
    var qText = q.type === 'tf' ? q.data.s : q.data.q;
    var qLabel = q.type === 'tf' ? '[判断] ' : '[选择] ';
    var correctStr = q.type === 'tf' ? (q.data.a ? '正确' : '错误') : q.data.a + '. ' + q.data.o[q.data.a.charCodeAt(0)-65];
    var userStr = q.type === 'tf' ? (r.userAnswer ? '正确' : '错误') : r.userAnswer + '. ' + (q.data.o[r.userAnswer.charCodeAt(0)-65] || '');

    listHtml += '<div class="result-item ' + cls + '">';
    listHtml += '<span class="result-badge ' + badgeCls + '">' + badgeText + '</span>';
    listHtml += '<span style="font-size:0.78rem;color:#64748b;">' + qLabel + '</span>';
    listHtml += qText;
    listHtml += '<div style="margin-top:4px;font-size:0.82rem;">';
    listHtml += '你的答案：<strong>' + userStr + '</strong> &nbsp;|&nbsp; ';
    listHtml += '正确答案：<strong>' + correctStr + '</strong>';
    listHtml += '</div>';
    if (q.data.e) {
      listHtml += '<div class="explanation-text">&#x1F4A1; ' + q.data.e + '</div>';
    }
    listHtml += '</div>';
  });
  document.getElementById('resultList').innerHTML = listHtml;
}

// ─── Render: Wrong Book ────────────────────────────────────────────
function renderWrongBook(filter) {
  filter = filter || 'all';
  var book = getWrongBook();
  var filtered = filter === 'all' ? book : book.filter(function(b) { return b.type === filter; });

  var contentEl = document.getElementById('wrongBookContent');
  var clearBtn = document.getElementById('btnClearWrong');

  if (book.length === 0) {
    clearBtn.classList.add('hidden');
    contentEl.innerHTML = '<div class="wrong-book-empty"><div class="big-icon">&#x1F4ED;</div><p>错题本为空</p><p style="font-size:0.82rem;">答错的题目会自动进入错题本</p></div>';
    return;
  }

  clearBtn.classList.remove('hidden');

  if (filtered.length === 0) {
    contentEl.innerHTML = '<div class="wrong-book-empty"><p>该分类下没有错题</p></div>';
    return;
  }

  var html = '<div style="font-size:0.82rem;color:#64748b;margin-bottom:12px;">共 ' + filtered.length + ' 题</div>';
  filtered.forEach(function(item, idx) {
    var typeLabel = item.type === 'tf' ? '[判断]' : '[选择]';
    html += '<div class="result-item wrong" style="position:relative;">';
    html += '<span class="result-badge badge-wrong">#' + (idx + 1) + '</span>';
    html += '<span style="font-size:0.78rem;color:#64748b;">' + typeLabel + '</span> ';
    html += item.statement;
    if (item.options) {
      html += '<div style="font-size:0.82rem;color:#64748b;margin-top:4px;">';
      var letters = ['A','B','C','D'];
      item.options.forEach(function(o, oi) { html += letters[oi] + '. ' + o + '<br>'; });
      html += '</div>';
    }
    html += '<div style="margin-top:4px;font-size:0.82rem;">你的答案：<strong style="color:#dc2626;">' + item.userAnswer + '</strong> &nbsp;|&nbsp; 正确答案：<strong style="color:#16a34a;">' + item.correctAnswer + '</strong></div>';
    if (item.explanation) {
      html += '<div class="explanation-text">&#x1F4A1; ' + item.explanation + '</div>';
    }
    html += '<button class="btn btn-sm btn-success" style="position:absolute;top:12px;right:12px;" data-type="' + item.type + '" data-id="' + item.id + '" onclick="event.stopPropagation();removeFromWrongBook(\'' + item.type + '\',' + item.id + ');renderWrongBook(currentWrongFilter);">移除</button>';
    html += '</div>';
  });
  contentEl.innerHTML = html;
}

var currentWrongFilter = 'all';
window.removeFromWrongBook = removeFromWrongBook;
window.renderWrongBook = renderWrongBook;

// ─── Screen Management ─────────────────────────────────────────────
function showScreen(screen) {
  STATE.screen = screen;
  document.getElementById('screenSetup').classList.toggle('hidden', screen !== 'setup');
  document.getElementById('screenQuiz').classList.toggle('hidden', screen !== 'quiz');
  document.getElementById('screenResult').classList.toggle('hidden', screen !== 'result');
  document.getElementById('screenWrongBook').classList.toggle('hidden', screen !== 'wrongBook');

  document.querySelectorAll('#navTabs .nav-tab').forEach(function(tab) {
    var target = screen === 'setup' || screen === 'quiz' || screen === 'result' ? 'setup' : 'wrongBook';
    tab.classList.toggle('active', tab.dataset.screen === target);
  });

  // Update wrong count badge
  var book = getWrongBook();
  var badge = document.getElementById('wrongCountBadge');
  if (book.length > 0) {
    badge.textContent = '(' + book.length + ')';
  } else {
    badge.textContent = '';
  }
}

// ─── Event Handlers ────────────────────────────────────────────────
document.getElementById('modeGrid').addEventListener('click', function(e) {
  var card = e.target.closest('.mode-card');
  if (!card) return;
  STATE.mode = card.dataset.mode;
  renderSetup();
});

document.getElementById('countOptions').addEventListener('click', function(e) {
  var btn = e.target.closest('.count-btn');
  if (!btn) return;
  STATE.count = parseInt(btn.dataset.count);
  renderSetup();
});

document.getElementById('btnStart').addEventListener('click', function() {
  STATE.questions = prepareQuestions();
  STATE.currentIndex = 0;
  STATE.score = 0;
  STATE.sessionResults = [];
  showScreen('quiz');
  renderQuestion();
});

document.getElementById('btnNext').addEventListener('click', nextQuestion);

document.getElementById('btnQuit').addEventListener('click', function() {
  if (STATE.answered || STATE.currentIndex === 0) {
    showScreen('setup');
  } else {
    if (confirm('确定要退出吗？当前进度将不保存。')) {
      showScreen('setup');
    }
  }
});

document.getElementById('btnRetry').addEventListener('click', function() {
  STATE.questions = prepareQuestions();
  STATE.currentIndex = 0;
  STATE.score = 0;
  STATE.sessionResults = [];
  showScreen('quiz');
  renderQuestion();
});

document.getElementById('btnHome').addEventListener('click', function() {
  showScreen('setup');
});

document.getElementById('btnClearWrong').addEventListener('click', function() {
  if (confirm('确定要清空全部错题吗？此操作不可撤销。')) {
    saveWrongBook([]);
    renderWrongBook(currentWrongFilter);
    updateWrongBadge();
  }
});

document.getElementById('navTabs').addEventListener('click', function(e) {
  var tab = e.target.closest('.nav-tab');
  if (!tab) return;
  var target = tab.dataset.screen;
  if (target === 'wrongBook') {
    showScreen('wrongBook');
    renderWrongBook(currentWrongFilter);
  } else {
    showScreen('setup');
  }
});

document.getElementById('wrongFilter').addEventListener('click', function(e) {
  var btn = e.target.closest('.filter-btn');
  if (!btn) return;
  currentWrongFilter = btn.dataset.filter;
  document.querySelectorAll('#wrongFilter .filter-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.filter === currentWrongFilter);
  });
  renderWrongBook(currentWrongFilter);
});

function updateWrongBadge() {
  var book = getWrongBook();
  var badge = document.getElementById('wrongCountBadge');
  badge.textContent = book.length > 0 ? '(' + book.length + ')' : '';
  if (book.length === 0) {
    document.getElementById('btnClearWrong').classList.add('hidden');
  }
}

// ─── Init ──────────────────────────────────────────────────────────
showScreen('setup');
updateWrongBadge();

})();
</script>
</body>
</html>'''

if __name__ == '__main__':
    main()
