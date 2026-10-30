<?php
// Sicherung als neuen Kurs einspielen, angemeldet als Administrator (php einspielen_als_admin.php <moodle> <mbz> [kat]).
// Anders als admin/cli/restore_backup.php setzt das Skript den Benutzer: sonst verwirft Moodle beim Einspielen die
// Rechte-Änderungen der Aktivitäten (z. B. „Lernende legen keine Einträge an“), weil ohne $USER keine Rolle
// überschreibbar ist – im Browser übernimmt Moodle sie.
define('CLI_SCRIPT', true);
require($argv[1] . '/config.php');
require_once($CFG->dirroot . '/backup/util/includes/restore_includes.php');
$admin = get_admin();
\core\session\manager::set_user($admin);
$kat = (int)($argv[3] ?? 1);
$dir = restore_controller::get_tempdir_name(SITEID, $admin->id);
$pfad = make_backup_temp_directory($dir);
get_file_packer('application/vnd.moodle.backup')->extract_to_pathname($argv[2], $pfad);
[$voll, $kurz] = restore_dbops::calculate_course_names(0, 'Einspielen', 'einspielen');
$id = restore_dbops::create_new_course($voll, $kurz, $kat);
$rc = new restore_controller($dir, $id, backup::INTERACTIVE_NO, backup::MODE_GENERAL, $admin->id, backup::TARGET_NEW_COURSE);
$rc->execute_precheck();
$rc->execute_plan();

$rc->destroy();
echo "== Restored course ID: $id ==\n";
