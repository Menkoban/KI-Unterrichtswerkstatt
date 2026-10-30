<?php
// Zählt einen eingespielten Kurs in der Moodle-Datenbank nach (php zaehlen.php <moodle-ordner>).
define('CLI_SCRIPT', true);
require($argv[1] . '/config.php');
global $DB;
$c = 2;
$course = $DB->get_record('course', ['id' => $c]);
echo "Kurs: {$course->fullname} | {$course->shortname} | Format {$course->format} | Abschluss {$course->enablecompletion}\n";
echo "Beschreibung: " . strip_tags($course->summary) . "\n";
foreach ($DB->get_records('course_sections', ['course' => $c], 'section') as $s) {
    $n = $s->sequence ? count(explode(',', $s->sequence)) : 0;
    echo "Abschnitt {$s->section}: " . ($s->name ?: '-') . " | sichtbar {$s->visible} | {$n} Aktivitäten\n";
}
$mods = $DB->get_records_sql("SELECT m.name, COUNT(*) n FROM {course_modules} cm JOIN {modules} m ON m.id=cm.module WHERE cm.course=? GROUP BY m.name", [$c]);
foreach ($mods as $m) echo "  {$m->name}: {$m->n}\n";
$ctx = context_course::instance($c);
$q = $DB->count_records_sql("SELECT COUNT(DISTINCT qv.questionid) FROM {quiz_slots} s JOIN {quiz} z ON z.id=s.quizid JOIN {question_references} r ON r.itemid=s.id AND r.component='mod_quiz' AND r.questionarea='slot' JOIN {question_versions} qv ON qv.questionbankentryid=r.questionbankentryid WHERE z.course=?", [$c]);
echo "Fragen in Tests: $q\n";
foreach ($DB->get_records('quiz', ['course' => $c]) as $z) {
    $n = $DB->count_records('quiz_slots', ['quizid' => $z->id]);
    echo "  Test {$z->name}: {$n} Fragen, Versuche {$z->attempts}, Note {$z->grade}, reviewrightanswer {$z->reviewrightanswer}, browsersecurity {$z->browsersecurity}\n";
}
foreach ($DB->get_records('badge', ['courseid' => $c]) as $b) echo "Abzeichen {$b->name}: status {$b->status}\n";
foreach ($DB->get_records('glossary', ['course' => $c]) as $g) echo "Glossar {$g->name}: " . $DB->count_records('glossary_entries', ['glossaryid' => $g->id]) . " Einträge, " . $DB->count_records('glossary_categories', ['glossaryid' => $g->id]) . " Kategorien\n";
foreach ($DB->get_records('data', ['course' => $c]) as $d) echo "Datenbank {$d->name}: " . $DB->count_records('data_fields', ['dataid' => $d->id]) . " Felder\n";
foreach ($DB->get_records('assign', ['course' => $c]) as $a) echo "Aufgabe {$a->name}: grade {$a->grade}, teamsubmission {$a->teamsubmission}, completionsubmit {$a->completionsubmit}\n";
$av = $DB->get_records_sql("SELECT cm.id, cm.availability FROM {course_modules} cm WHERE cm.course=? AND cm.availability IS NOT NULL", [$c]);
echo "Aktivitäten mit Voraussetzung: " . count($av) . "\n";
foreach ($av as $a) echo "  " . $a->availability . "\n";
echo "Gruppen: " . $DB->count_records('groups', ['courseid' => $c]) . "\n";
$hidden = $DB->get_records_sql("SELECT cm.id, m.name FROM {course_modules} cm JOIN {modules} m ON m.id=cm.module WHERE cm.course=? AND cm.visible=0", [$c]);
echo "Einzeln verborgen: " . count($hidden) . "\n";
$f = $DB->count_records_sql("SELECT COUNT(*) FROM {files} WHERE contextid IN (SELECT id FROM {context} WHERE path LIKE ?) AND filename <> '.'", [$ctx->path . '%']);
echo "Dateien im Kurs: $f\n";
