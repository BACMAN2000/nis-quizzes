/**
 * NIS English Quizzes — Google Apps Script Web App (doPost endpoint)
 * ------------------------------------------------------------------
 * Receives the JSON each quiz POSTs on submit and stores it in the bound
 * Google Sheet, using a SEPARATE TAB per skill:
 *   • "Reading"   — auto-marked reading score + every answer
 *   • "Listening" — auto-marked listening score + every answer
 *   • "Writing"   — one row per writing task (full text + word count + provisional ref)
 *
 * Reading exams that include A2 Writing Parts 6/7 write the score to the
 * "Reading" tab AND the writing answers to the "Writing" tab automatically.
 *
 * DEPLOY (do this once per spreadsheet):
 *   1. Open your Google Sheet → Extensions → Apps Script.
 *   2. Replace the code with this file, Save.
 *   3. Deploy → Manage deployments → edit your existing Web App deployment
 *      → Version: "New version" → Deploy.  (Keeps the SAME /exec URL, so you
 *      do NOT need to change anything in the quiz pages.)
 *   4. Execute as: Me.  Who has access: Anyone.
 *
 * The reading + writing quizzes share one Web App URL → paste this into THAT
 * spreadsheet's script (you'll get Reading + Writing tabs). The listening quiz
 * uses its own URL → paste the same script into that spreadsheet too.
 */

var TEACHER_EMAIL  = 'pbaca@nordic-school.edu.pe'; // set '' to disable emails
var SEND_EMAIL     = true;
var SPREADSHEET_ID = '';   // leave '' if this script is bound to the Sheet; otherwise paste the Sheet ID

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, service: 'NIS Quizzes endpoint' }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var ss   = SPREADSHEET_ID ? SpreadsheetApp.openById(SPREADSHEET_ID)
                              : SpreadsheetApp.getActiveSpreadsheet();
    var skill = (data.skill || 'Other');

    if (skill === 'Writing') {
      writeWritingRows_(ss, data, 'Writing Quiz');
    } else {
      // Reading or Listening: score row to the skill tab
      writeScoreRow_(ss, skill, data);
      // If this exam also carried writing answers (A2), log them on the Writing tab
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

/* ---------- Reading / Listening: one row with score + all answers ---------- */
function writeScoreRow_(ss, skill, d) {
  var headers = ['Timestamp', 'Name', 'Grade', 'Email', 'Level', 'Exam',
                 'Score', 'Total', 'Percent', 'CEFR', 'Minutes', 'Tab switches', 'Answers'];
  var sheet = getOrCreateTab_(ss, skill, headers);
  var answers = (d.detail || []).map(function (q) {
    var u = stripHtml_(q.user), c = stripHtml_(q.correctAns);
    return 'Q' + q.q + ': ' + u + ' (correct: ' + c + ') ' + (q.ok ? '✓' : '✗');
  }).join('  |  ');
  sheet.appendRow([
    new Date(), d.name || '', d.grade || '', d.email || '', d.level || '', d.examTitle || d.examType || '',
    d.score, d.total, (d.percent != null ? d.percent + '%' : ''), d.cefrLabel || '',
    d.durationMinutes || '', d.tabSwitches || 0, answers
  ]);
}

/* ---------- Writing: one row per task (full text persisted) ---------- */
function writeWritingRows_(ss, d, sourceLabel) {
  var headers = ['Timestamp', 'Name', 'Grade', 'Email', 'Level', 'Source',
                 'Task', 'Words', 'Answer', 'Provisional band (auto — verify by hand)', 'Auto notes'];
  var sheet = getOrCreateTab_(ss, 'Writing', headers);
  var tasks = d.writingEvaluation || d.writingAnswers || [];
  tasks.forEach(function (t) {
    var band = (t.provisionalBand != null ? t.provisionalBand
              : t.band != null ? t.band : '');
    sheet.appendRow([
      new Date(), d.name || '', d.grade || '', d.email || '', d.level || '', sourceLabel,
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
  var subject = '[NIS ' + skill + '] ' + (d.name || 'Student') + ' — ' + (d.level || '');
  var lines = [
    'Student: ' + (d.name || ''),
    'Grade: '   + (d.grade || ''),
    'Level: '   + (d.level || ''),
    'Exam: '    + (d.examTitle || d.examType || skill)
  ];
  if (skill !== 'Writing') {
    lines.push('Score: ' + d.score + ' / ' + d.total + ' (' + d.percent + '%)');
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
