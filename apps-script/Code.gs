/**
 * NIS English Quizzes — Google Apps Script Web App (doPost endpoint)
 * ------------------------------------------------------------------
 * ONE script for all three quizzes. It auto-detects the input format and the
 * skill, then stores each submission in a SEPARATE TAB:
 *   • "Reading"   — auto-marked reading score + every answer
 *   • "Listening" — auto-marked listening score + every answer
 *   • "Writing"   — one row per writing task (full text + word count + provisional ref)
 *
 * It handles BOTH ways the quizzes send data:
 *   • Reading / Writing → fetch() with a JSON body  (e.postData.contents)
 *   • Listening         → hidden-form POST           (e.parameter.data)
 *
 * A Reading exam that includes A2 Writing Parts 6/7 writes the score to the
 * "Reading" tab AND the writing answers to the "Writing" tab automatically.
 *
 * DEPLOY (once per spreadsheet — do it on BOTH the Reading/Writing sheet and the
 * Listening sheet, since each quiz family points at its own Web App URL):
 *   1. Open the Google Sheet → Extensions → Apps Script.
 *   2. Replace the code with this file, Save.
 *   3. Deploy → Manage deployments → edit the existing Web App deployment →
 *      Version: "New version" → Deploy.  (Same /exec URL — nothing to change in
 *      the quiz pages.)  Execute as: Me.  Who has access: Anyone.
 *
 * Because you open Apps Script FROM the sheet, the script is bound to it and
 * SPREADSHEET_ID can stay ''.
 */

var TEACHER_EMAIL  = 'pbaca@nordic-school.edu.pe'; // set '' to disable emails
var SEND_EMAIL     = true;
var SPREADSHEET_ID = '';   // leave '' when the script is bound to the Sheet

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, service: 'NIS Quizzes endpoint' }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var data  = parseInput_(e);
    var ss    = SPREADSHEET_ID ? SpreadsheetApp.openById(SPREADSHEET_ID)
                               : SpreadsheetApp.getActiveSpreadsheet();
    var skill = data.skill || (data.breakdown ? 'Listening' : 'Reading');

    if (skill === 'Writing') {
      writeWritingRows_(ss, data, 'Writing Quiz');
    } else {
      writeScoreRow_(ss, skill, data);
      var w = data.writingEvaluation || data.writingAnswers || [];
      if (w.length) writeWritingRows_(ss, data, skill + ' (Parts 6–7)');
    }

    if (SEND_EMAIL && TEACHER_EMAIL) { try { sendEmail_(skill, data); } catch (_) {} }

    return ContentService.createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/* Accept JSON body (fetch) OR form field "data" (hidden-form POST). */
function parseInput_(e) {
  if (e && e.postData && e.postData.contents) {
    try { return JSON.parse(e.postData.contents); } catch (_) {}
  }
  if (e && e.parameter && e.parameter.data) {
    try { return JSON.parse(e.parameter.data); } catch (_) {}
  }
  return {};
}

/* ---------- Reading / Listening: one row with score + all answers ---------- */
function writeScoreRow_(ss, skill, d) {
  var headers = ['Timestamp', 'Name', 'Grade/Class', 'Email', 'Level', 'Exam',
                 'Score', 'Total', 'Percent', 'CEFR', 'Minutes', 'Tab switches', 'Answers'];
  var sheet = getOrCreateTab_(ss, skill, headers);

  var grade   = d.grade || d.klass || '';
  var minutes = d.durationMinutes || d.elapsed_min || '';
  var pct     = (d.percent != null) ? d.percent
              : (d.total ? Math.round(d.score / d.total * 100) : '');

  var answers = '';
  if (d.detail && d.detail.length) {                 // Reading quiz format
    answers = d.detail.map(function (q) {
      return 'Q' + q.q + ': ' + stripHtml_(q.user) +
             ' (correct: ' + stripHtml_(q.correctAns) + ') ' + (q.ok ? '✓' : '✗');
    }).join('  |  ');
  } else if (d.answers) {                            // Listening quiz format (object)
    answers = JSON.stringify(d.answers);
  }

  sheet.appendRow([
    new Date(), d.name || '', grade, d.email || '', d.level || '',
    d.examTitle || d.examType || skill,
    d.score, d.total, (pct !== '' ? pct + '%' : ''), d.cefrLabel || '',
    minutes, d.tabSwitches || 0, answers
  ]);
}

/* ---------- Writing: one row per task (full text persisted) ---------- */
function writeWritingRows_(ss, d, sourceLabel) {
  var headers = ['Timestamp', 'Name', 'Grade/Class', 'Email', 'Level', 'Source',
                 'Task', 'Words', 'Answer', 'Provisional band (auto — verify by hand)', 'Auto notes'];
  var sheet = getOrCreateTab_(ss, 'Writing', headers);
  var grade = d.grade || d.klass || '';
  var tasks = d.writingEvaluation || d.writingAnswers || [];
  tasks.forEach(function (t) {
    var band = (t.provisionalBand != null ? t.provisionalBand
              : t.band != null ? t.band : '');
    sheet.appendRow([
      new Date(), d.name || '', grade, d.email || '', d.level || '', sourceLabel,
      t.part || t.label || t.prompt || '', t.wordCount || '',
      (t.text || ''), (band !== '' ? band + ' / 5' : ''), (t.feedback || '')
    ]);
  });
}

/* ---------- helpers ---------- */
function getOrCreateTab_(ss, name, headers) {
  var sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function stripHtml_(s) {
  return String(s == null ? '' : s).replace(/<[^>]*>/g, '').trim();
}

function sendEmail_(skill, d) {
  var grade = d.grade || d.klass || '';
  var subject = '[NIS ' + skill + '] ' + (d.name || 'Student') + ' — ' + (d.level || '');
  var lines = [
    'Student: ' + (d.name || ''),
    'Grade/Class: ' + grade,
    'Level: ' + (d.level || ''),
    'Exam: '  + (d.examTitle || d.examType || skill)
  ];
  if (skill !== 'Writing' && d.score != null) {
    lines.push('Score: ' + d.score + ' / ' + d.total);
  }
  var tasks = d.writingEvaluation || d.writingAnswers || [];
  if (tasks.length) {
    lines.push('', '--- Writing (mark by hand) ---');
    tasks.forEach(function (t) {
      lines.push('', (t.part || t.label || '') + '  [' + (t.wordCount || 0) + ' words]:', (t.text || '(blank)'));
    });
  }
  MailApp.sendEmail(TEACHER_EMAIL, subject, lines.join('\n'));
}
