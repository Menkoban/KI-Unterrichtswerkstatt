<?php
// Probekurs „Klassen-Dashboard“: 10 Testlernende, eine Lehrkraft, Feedback „Selbsteinschätzung Meilenstein 1“ mit
// Antworten, verborgene Datenbank „Bewertung Lehrkraft“ (Kürzel, Meilenstein, Stufen). Nur für das Test-Moodle.
define('CLI_SCRIPT', true);
require($argv[1] . '/config.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/user/lib.php');
require_once($CFG->dirroot . '/lib/enrollib.php');
global $DB, $USER;
\core\session\manager::set_user(get_admin());

$c = $DB->get_record('course', ['shortname' => 'KD-PROBE']);
if (!$c) {
    $c = create_course((object)['fullname' => 'Probe Klassen-Dashboard EG1a', 'shortname' => 'KD-PROBE', 'category' => 1,
        'format' => 'tiles', 'numsections' => 2, 'enablecompletion' => 1]);
}
$ctx = context_course::instance($c->id);
$plugin = enrol_get_plugin('manual');
$inst = $DB->get_record('enrol', ['courseid' => $c->id, 'enrol' => 'manual']);
$rolle = ['student' => $DB->get_field('role', 'id', ['shortname' => 'student']),
          'editingteacher' => $DB->get_field('role', 'id', ['shortname' => 'editingteacher'])];
$namen = ['Lena', 'Jonas', 'Mia', 'Emil', 'Hanna', 'Paul', 'Lea', 'Ben', 'Clara', 'Finn'];
$users = [];
foreach (array_merge(['lehrkraft' => 'Lehrkraft'], array_combine(array_map(fn($i) => sprintf('s%02d', $i + 1), array_keys($namen)), $namen)) as $login => $vor) {
    $u = $DB->get_record('user', ['username' => $login]);
    if (!$u) {
        $id = user_create_user((object)['username' => $login, 'password' => 'Test-2026!', 'firstname' => $vor, 'lastname' => 'Test',
            'email' => $login . '@example.invalid', 'auth' => 'manual', 'confirmed' => 1, 'mnethostid' => $CFG->mnet_localhost_id]);
        $u = $DB->get_record('user', ['id' => $id]);
    }
    $plugin->enrol_user($inst, $u->id, $login === 'lehrkraft' ? $rolle['editingteacher'] : $rolle['student']);
    $users[$login] = $u;
}
$sec = $DB->get_record('course_sections', ['course' => $c->id, 'section' => 2]);
course_update_section($c, $sec, ['name' => 'Material für Lehrkräfte', 'visible' => 0]);
course_update_section($c, $DB->get_record('course_sections', ['course' => $c->id, 'section' => 1]), ['name' => 'Meilenstein 1']);

function modul($c, $name, $sec, $daten) {
    global $DB;
    $cms = get_fast_modinfo($c)->get_instances_of($name);
    foreach ($cms as $cm) { if ($cm->name === $daten['name']) return $cm; }
    $m = (object)array_merge(['modulename' => $name, 'module' => $DB->get_field('modules', 'id', ['name' => $name]),
        'section' => $sec, 'visible' => 1, 'course' => $c->id, 'introeditor' => ['text' => '', 'format' => FORMAT_HTML, 'itemid' => 0],
        'cmidnumber' => ''], $daten);
    $r = add_moduleinfo($m, $c);
    rebuild_course_cache($c->id, true); return get_fast_modinfo($c->id)->get_cm($r->coursemodule);
}
// Feedback mit drei Kriterien
$fbcm = modul($c, 'feedback', 1, ['name' => 'Selbsteinschätzung Meilenstein 1', 'anonymous' => 2, 'multiple_submit' => 0,
    'email_notification' => 0, 'autonumbering' => 0, 'page_after_submit_editor' => ['text' => '', 'format' => FORMAT_HTML, 'itemid' => 0],
    'publish_stats' => 0, 'completionsubmit' => 1, 'page_after_submit' => '', 'page_after_submitformat' => FORMAT_HTML, 'site_after_submit' => '']);
$fb = $DB->get_record('feedback', ['id' => $fbcm->instance]);
$krit = ['Fehlerbild und Vermutungen', 'Eigener Prüfplan', 'Sicher gearbeitet'];
if (!$DB->record_exists('feedback_item', ['feedback' => $fb->id])) {
    foreach ($krit as $i => $k) {
        $DB->insert_record('feedback_item', (object)['feedback' => $fb->id, 'template' => 0, 'name' => $k, 'label' => 'K' . ($i + 1),
            'presentation' => 'r>>>>>1 trifft wenig zu|2 teilweise|3 überwiegend|4 voll', 'typ' => 'multichoice',
            'hasvalue' => 1, 'position' => $i + 1, 'required' => 1, 'dependitem' => 0, 'dependvalue' => '', 'options' => '']);
    }
}
$items = array_values($DB->get_records('feedback_item', ['feedback' => $fb->id], 'position'));
$selbst = [[3,3,4],[4,4,4],[2,2,3],[3,2,3],[2,3,3],[4,3,4],[3,3,3],[1,2,3],[3,4,4]];   // s10 fehlt
foreach ($selbst as $i => $werte) {
    $u = $users[sprintf('s%02d', $i + 1)];
    if ($DB->record_exists('feedback_completed', ['feedback' => $fb->id, 'userid' => $u->id])) continue;
    $cid = $DB->insert_record('feedback_completed', (object)['feedback' => $fb->id, 'userid' => $u->id, 'timemodified' => time(),
        'random_response' => 0, 'anonymous_response' => 2, 'courseid' => $c->id]);
    foreach ($items as $j => $it) {
        $DB->insert_record('feedback_value', (object)['course_id' => $c->id, 'item' => $it->id, 'completed' => $cid, 'tmp_completed' => 0, 'value' => $werte[$j]]);
    }
}
// Datenbank für die Stufen der Lehrkraft (verborgen im Lehrkraftbereich)
$dcm = modul($c, 'data', 2, ['name' => 'Bewertung Lehrkraft (Daten des Dashboards)', 'approval' => 0, 'manageapproved' => 1]);
$data = $DB->get_record('data', ['id' => $dcm->instance]);
require_once($CFG->dirroot . '/mod/data/lib.php');
foreach (['lernende' => 'text', 'meilenstein' => 'text', 'stufen' => 'text'] as $fname => $ftyp) {
    if (!$DB->record_exists('data_fields', ['dataid' => $data->id, 'name' => $fname])) {
        $f = data_get_field_new($ftyp, $data); $f->define_default_field(); $f->field->name = $fname; $f->field->description = $fname; $f->insert_field();
    }
}
echo json_encode(['kurs' => $c->id, 'feedback_cm' => $fbcm->id, 'data_cm' => $dcm->id, 'data_id' => $data->id]) . "\n";
