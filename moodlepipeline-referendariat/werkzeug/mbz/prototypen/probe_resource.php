<?php
define('CLI_SCRIPT', true);
require($argv[1] . '/config.php');
require_once($CFG->dirroot . '/course/modlib.php');
require_once($CFG->dirroot . '/lib/resourcelib.php');
global $DB;
\core\session\manager::set_user(get_admin());
$c = $DB->get_record('course', ['id' => 6]);
$cm = null;
foreach (get_fast_modinfo($c)->get_instances_of('resource') as $x) { if ($x->name === 'Klassen-Dashboard') $cm = $x; }
if (!$cm) {
    $m = (object)['modulename' => 'resource', 'module' => $DB->get_field('modules', 'id', ['name' => 'resource']), 'section' => 2,
        'visible' => 1, 'course' => $c->id, 'name' => 'Klassen-Dashboard', 'introeditor' => ['text' => '', 'format' => FORMAT_HTML, 'itemid' => 0],
        'display' => RESOURCELIB_DISPLAY_EMBED, 'files' => file_get_unused_draft_itemid(), 'cmidnumber' => ''];
    $r = add_moduleinfo($m, $c);
    rebuild_course_cache($c->id, true);
    $cm = get_fast_modinfo($c->id)->get_cm($r->coursemodule);
}
$ctx = context_module::instance($cm->id);
$fs = get_file_storage();
$fs->delete_area_files($ctx->id, 'mod_resource', 'content');
$fs->create_file_from_pathname(['contextid' => $ctx->id, 'component' => 'mod_resource', 'filearea' => 'content', 'itemid' => 0,
    'filepath' => '/', 'filename' => 'klassendashboard.html', 'sortorder' => 1], $argv[2]);
$DB->set_field('resource', 'revision', time() % 100000, ['id' => $cm->instance]);
rebuild_course_cache($c->id, true);
echo $cm->id, "\n";
