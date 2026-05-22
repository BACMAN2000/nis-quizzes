/**
 * NIS English Quizzes — Google Apps Script Web App (doPost endpoint)
 * ------------------------------------------------------------------
 * Drop-in replacement for the existing "Reading Test" script. It keeps your
 * current columns and adds two things you asked for:
 *   1) an "Answers" column (every answer the student gave), and
 *   2) a separate "Writing" tab (full writing text + word count + a provisional
 *      auto-estimate you verify by hand).
 *
 * Tabs created automatically:
 *   • "Reading"   — score + stats (Strongest/Weakest/Verdict) + Answers
 *   • "Listening" — same layout (if you also paste this in the Listening sheet)
 *   • "Writing"   — one row per writing task
 *
 * Works with BOTH ways the quizzes send data:
 *   • Reading / Writing → fetch() JSON body  (e.postData.contents)
 *   • Listening         → hidden-form POST    (e.parameter.data)
 *
 * NOTE on tabs: your old data stays in the "Resultados" tab untouched. New
 * Reading submissions go to the new "Reading" tab (with the Answers column).
 * If you'd rather keep writing into "Resultados", change READING_TAB below to
 * "Resultados" (but then add an "Answers" header to that sheet yourself).
 *
 * DEPLOY: paste this over Código.gs → Save → Implementar (Deploy) →
 * Administrar implementaciones → edit the Web App → Nueva versión → Implementar.
 * Same /exec URL, so nothing changes in the quiz pages.
 */

var TEACHER_EMAIL = 'pbaca@nordic-school.edu.pe';  // '' to disable emails
var SCHOOL_NAME   = 'NIS English';
var SEND_EMAIL    = true;

var READING_TAB   = 'Reading';
var LISTENING_TAB = 'Listening';
var WRITING_TAB   = 'Writing';

function doGet() {
  return json_({ ok: true, service: 'NIS Quizzes endpoint' });
}

function doPost(e) {
  try {
    var data  = parseInput_(e);
    var skill = data.skill || (data.breakdown ? 'Listening' : 'Reading');

    if (skill === 'Writing') {
      writeWritingRows_(data, 'Writing Quiz');
    } else {
      writeScoreRow_(skill === 'Listening' ? LISTENING_TAB : READING_TAB, data);
      var w = data.writingEvaluation || data.writingAnswers || [];
      if (w.length) writeWritingRows_(data, skill + ' (Parts 6–7)');  // A2 reading has writing
    }

    if (SEND_EMAIL && TEACHER_EMAIL) { try { sendEmails(data, skill); } catch (_) {} }
    return json_({ ok: true });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message || err) });
  }
}

/* Accept a JSON body (fetch) OR a form field "data" (hidden-form POST). */
function parseInput_(e) {
  if (e && e.postData && e.postData.contents) { try { return JSON.parse(e.postData.contents); } catch (_) {} }
  if (e && e.parameter && e.parameter.data)   { try { return JSON.parse(e.parameter.data); } catch (_) {} }
  return {};
}

/* ---------- Reading / Listening: keeps your columns, adds Answers ---------- */
function writeScoreRow_(tabName, d) {
  var headers = ['Timestamp', 'Student', 'Email', 'Grade', 'Level', 'Level name',
                 'Exam', 'Score', 'Total', '%', 'CEFR', 'Duration (min)',
                 'Strongest', 'Weakest', 'Verdict', 'Answers'];
  var sh = getSheet_(tabName, headers);

  var grade    = d.grade || d.klass || '';
  var minutes  = d.durationMinutes || d.elapsed_min || '';
  var pct      = (d.percent != null) ? d.percent : (d.total ? Math.round(d.score / d.total * 100) : '');

  // Strongest / Weakest single part (by %), from the parts array
  var strongest = '', weakest = '';
  if (d.parts && d.parts.length) {
    var sorted = d.parts.slice().sort(function (a, b) { return b.pct - a.pct; });
    strongest = sorted[0].name + ' (' + sorted[0].pct + '%)';
    weakest   = sorted[sorted.length - 1].name + ' (' + sorted[sorted.length - 1].pct + '%)';
  }

  // Every answer
  var answers = '';
  if (d.detail && d.detail.length) {
    answers = d.detail.map(function (q) {
      return 'Q' + q.q + ': ' + stripHtml_(q.user) +
             ' (correct: ' + stripHtml_(q.correctAns) + ') ' + (q.ok ? '✓' : '✗');
    }).join('  |  ');
  } else if (d.answers) {
    answers = JSON.stringify(d.answers);  // listening stores its answers object
  }

  sh.appendRow([
    new Date(), d.name || '', d.email || '', grade, d.level || '', d.levelName || '',
    d.examTitle || d.examType || tabName, d.score, d.total,
    (pct !== '' ? pct + '%' : ''), d.cefrLabel || '', minutes,
    strongest, weakest, d.verdict || '', answers
  ]);
}

/* ---------- Writing: one row per task, full text persisted ---------- */
function writeWritingRows_(d, sourceLabel) {
  var headers = ['Timestamp', 'Student', 'Email', 'Grade', 'Level', 'Source',
                 'Task', 'Words', 'Answer', 'Provisional band (auto — verify by hand)', 'Auto notes'];
  var sh = getSheet_(WRITING_TAB, headers);
  var grade = d.grade || d.klass || '';
  var tasks = d.writingEvaluation || d.writingAnswers || [];
  tasks.forEach(function (t) {
    var band = (t.provisionalBand != null ? t.provisionalBand : t.band != null ? t.band : '');
    sh.appendRow([
      new Date(), d.name || '', d.email || '', grade, d.level || '', sourceLabel,
      t.part || t.label || t.prompt || '', t.wordCount || '',
      (t.text || ''), (band !== '' ? band + ' / 5' : ''), (t.feedback || '')
    ]);
  });
}

/* ---------- email (teacher + student) ---------- */
function sendEmails(d, skill) {
  var grade = d.grade || d.klass || '';
  var pct = (d.percent != null) ? d.percent : (d.total ? Math.round(d.score / d.total * 100) : '');
  var tasks = d.writingEvaluation || d.writingAnswers || [];

  // --- Teacher email (full) ---
  var subject = '[' + SCHOOL_NAME + ' · ' + skill + '] ' + (d.name || 'Student') + ' — ' + (d.level || '');
  var lines = ['Student: ' + (d.name || ''), 'Grade: ' + grade, 'Email: ' + (d.email || ''),
               'Level: ' + (d.level || ''), 'Exam: ' + (d.examTitle || d.examType || skill)];
  if (skill !== 'Writing' && d.score != null) lines.push('Score: ' + d.score + ' / ' + d.total + (pct !== '' ? ' (' + pct + '%)' : ''));
  if (tasks.length) {
    lines.push('', '--- Writing (mark by hand) ---');
    tasks.forEach(function (t) { lines.push('', (t.part || t.label || '') + ' [' + (t.wordCount || 0) + ' words]:', (t.text || '(blank)')); });
  }
  MailApp.sendEmail(TEACHER_EMAIL, subject, lines.join('\n'));

  // --- Student email (their own result) ---
  var sEmail = d.email || '';
  if (sEmail && /^\S+@\S+\.\S+$/.test(sEmail)) {
    var body;
    if (skill === 'Writing') {
      body = 'Hi ' + (d.name || '') + ',\n\nYour writing (' + (d.level || '') + ') has been submitted to your teacher, who will read it and give you a mark by hand.\n\nThank you!\n— ' + SCHOOL_NAME;
    } else {
      body = 'Hi ' + (d.name || '') + ',\n\nHere is your ' + skill + ' result (' + (d.level || '') + '):\n\n' +
             'Score: ' + d.score + ' / ' + d.total + (pct !== '' ? '  (' + pct + '%)' : '') + '\n';
      if (d.parts && d.parts.length) {
        body += '\nBy part:\n' + d.parts.map(function (p) { return '  • ' + p.name + ': ' + p.pct + '%'; }).join('\n') + '\n';
      }
      body += '\nWell done — keep practising!\n— ' + SCHOOL_NAME;
    }
    MailApp.sendEmail(sEmail, 'Your ' + skill + ' result — ' + SCHOOL_NAME, body);
  }
}

/* ---------- helpers ---------- */
function getSheet_(name, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    sh.getRange(1, 1, 1, headers.length).setValues([headers])
      .setBackground('#0f766e').setFontColor('#ffffff').setFontWeight('bold').setHorizontalAlignment('center');
    sh.setFrozenRows(1);
  }
  return sh;
}
function stripHtml_(s) { return String(s == null ? '' : s).replace(/<[^>]*>/g, '').trim(); }
function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
