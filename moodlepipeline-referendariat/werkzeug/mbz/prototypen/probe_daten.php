<?php
// Testdaten für den Probekurs mit Stufen: s01 bis s10 einschreiben, Selbsteinschätzungen beider Meilensteine,
// Ergebnisse der gestuften Aufgaben entlang festgelegter Wege (nur Test-Moodle).
define('CLI_SCRIPT', true);
require($argv[1] . '/config.php');
require_once($CFG->libdir . '/gradelib.php');
global $DB;
set_config('noemailever', 1);
$kurs = (int)$argv[2];
$c = $DB->get_record('course', ['id' => $kurs]);
$inst = $DB->get_record('enrol', ['courseid' => $kurs, 'enrol' => 'manual']);
$pl = enrol_get_plugin('manual');
if (!$inst) { $pl->add_default_instance($c); $inst = $DB->get_record('enrol', ['courseid' => $kurs, 'enrol' => 'manual']); }
$st = $DB->get_field('role', 'id', ['shortname' => 'student']);
$pl->enrol_user($inst, $DB->get_field('user', 'id', ['username' => 'lehrkraft']), $DB->get_field('role', 'id', ['shortname' => 'editingteacher']));
// Selbsteinschätzungen (null = nicht abgegeben)
$selbst = ['Selbsteinschätzung Meilenstein 1' => [[3,3,4],[4,4,4],[2,2,3],[3,2,3],[2,3,3],[4,3,4],[3,3,3],[1,2,3],[3,4,4],null],
           'Selbsteinschätzung Meilenstein 2' => [[3,3,3],[4,4,4],[2,2,3],null,[3,3,4],[3,3,3],[3,3,3],[2,2,2],[4,4,4],null]];
// Wege: Stufe je Kachel (0 Grundlagen, 1 Standard, 2 Vertiefung), null = noch nicht bearbeitet
$wege = [[1,1,2,2,2,2],[1,2,1,1,1,2],[1,0,0,1,1,1],[1,1,1,1,null,null],[1,2,2,2,2,2],[1,0,0,0,1,1],[1,1,1,2,2,2],[1,0,0,0,0,1],[1,2,2,2,2,2],[1,1,0,null,null,null]];
$kz = ['g', 's', 'v'];
for ($i = 1; $i <= 10; $i++) {
    $u = $DB->get_record('user', ['username' => sprintf('s%02d', $i)]);
    $pl->enrol_user($inst, $u->id, $st);
    foreach ($selbst as $name => $liste) {
        $w = $liste[$i - 1];
        $fb = $DB->get_record('feedback', ['course' => $kurs, 'name' => $name]);
        if (!$w || !$fb || $DB->record_exists('feedback_completed', ['feedback' => $fb->id, 'userid' => $u->id])) { continue; }
        $items = array_values($DB->get_records_select('feedback_item', 'feedback = ? AND hasvalue = 1', [$fb->id], 'position'));
        $cid = $DB->insert_record('feedback_completed', (object)['feedback' => $fb->id, 'userid' => $u->id, 'timemodified' => time(),
            'random_response' => 0, 'anonymous_response' => 2, 'courseid' => $kurs]);
        foreach ($items as $j => $it) {
            $DB->insert_record('feedback_value', (object)['course_id' => $kurs, 'item' => $it->id, 'completed' => $cid, 'tmp_completed' => 0, 'value' => $w[$j]]);
        }
    }
    $weg = $wege[$i - 1];
    foreach ($weg as $n => $stufe) {
        if ($stufe === null) { continue; }
        $naechste = $weg[$n + 1] ?? null;
        $prozent = $naechste === null ? 70 : ($naechste > $stufe ? 92 : ($naechste < $stufe ? 30 : 70));
        foreach ([1, 2] as $a) {
            $cm = $DB->get_record('course_modules', ['course' => $kurs, 'idnumber' => 'stufe-k' . ($n + 1) . '-' . $kz[$stufe] . '-' . $a]);
            if (!$cm) { continue; }
            $quiz = $DB->get_record('quiz', ['id' => $cm->instance]);
            grade_update('mod/quiz', $kurs, 'mod', 'quiz', $quiz->id, 0, [$u->id => (object)['userid' => $u->id, 'rawgrade' => $quiz->grade * $prozent / 100]]);
        }
    }
}
grade_regrade_final_grades($kurs);
$cm = $DB->get_record_sql("SELECT cm.id FROM {course_modules} cm JOIN {modules} m ON m.id = cm.module AND m.name = 'data'
    JOIN {data} d ON d.id = cm.instance WHERE cm.course = ? AND d.name LIKE 'Klassen-Dashboard%'", [$kurs]);
$res = $DB->get_record_sql("SELECT cm.id FROM {course_modules} cm JOIN {modules} m ON m.id = cm.module AND m.name = 'resource' JOIN {resource} r ON r.id = cm.instance WHERE cm.course = ? AND r.name = 'Lernstand-Dashboard'", [$kurs]);
echo json_encode(['dashboard_cm' => $cm->id, 'lernstand_cm' => $res ? $res->id : null]), "\n";
