import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from convert import ConversionLog, convert_ini_to_orca, parse_ini


FIXTURE = Path(__file__).parent / 'fixtures' / 'sample_safe.ini'
PRINTER_NAME = 'PrusaToOrca - Original Prusa/MK4:Input Shaper 0.4 nozzle'


def read_bundle(path):
    with zipfile.ZipFile(path) as zf:
        return {
            name: json.loads(zf.read(name).decode('utf-8'))
            for name in zf.namelist()
            if name.endswith('.json')
        }


class SafeImportTests(unittest.TestCase):
    def test_dry_run_does_not_write_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / 'out'
            result = convert_ini_to_orca(FIXTURE, out_dir, dry_run=True)

            self.assertIn('bundle', result)
            self.assertFalse(out_dir.exists())

    def test_profiles_are_prefixed_and_zip_paths_are_sanitized(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / 'out'
            bundle_path = convert_ini_to_orca(FIXTURE, out_dir)
            bundle = read_bundle(bundle_path)

            self.assertEqual(bundle_path.parent, out_dir)
            self.assertTrue(bundle_path.name.startswith('PrusaToOrca - '))

            profile_files = [name for name in bundle if name != 'bundle_structure.json']
            for name in profile_files:
                self.assertNotRegex(Path(name).name, r'[\\/:*?\x00-\x1f\x7f]')

            names = [data['name'] for name, data in bundle.items() if name != 'bundle_structure.json']
            self.assertTrue(all(name.startswith('PrusaToOrca - ') for name in names))

    def test_strict_compatibility_limits_filament_and_process_to_imported_printer(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = convert_ini_to_orca(FIXTURE, Path(tmp))
            bundle = read_bundle(bundle_path)

            for name, data in bundle.items():
                if name.startswith(('filament/', 'process/')):
                    self.assertEqual(data['compatible_printers'], [PRINTER_NAME])
                    self.assertEqual(data['compatible_printers_condition'], '')

    def test_strict_compatibility_includes_all_imported_printers(self):
        with tempfile.TemporaryDirectory() as tmp:
            ini_path = Path(tmp) / 'multi_printer.ini'
            ini_path.write_text(
                '\n'.join([
                    '[printer:Printer A]',
                    'nozzle_diameter = 0.4',
                    '',
                    '[printer:Printer B]',
                    'nozzle_diameter = 0.6',
                    '',
                    '[filament:Shared PLA]',
                    'filament_type = PLA',
                    'temperature = 210',
                    '',
                    '[print:Shared Process]',
                    'layer_height = 0.2',
                ]),
                encoding='utf-8',
            )
            bundle_path = convert_ini_to_orca(ini_path, Path(tmp) / 'out')
            bundle = read_bundle(bundle_path)

            expected = ['PrusaToOrca - Printer A', 'PrusaToOrca - Printer B']
            for name, data in bundle.items():
                if name.startswith(('filament/', 'process/')):
                    self.assertEqual(data['compatible_printers'], expected)
                    self.assertEqual(data['compatible_printers_condition'], '')

    def test_loose_compatibility_leaves_filament_and_process_global(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle_path = convert_ini_to_orca(FIXTURE, Path(tmp), compatibility='loose')
            bundle = read_bundle(bundle_path)

            for name, data in bundle.items():
                if name.startswith(('filament/', 'process/')):
                    self.assertEqual(data['compatible_printers'], [])
                    self.assertEqual(data['compatible_printers_condition'], '')

    def test_utf8_bom_keeps_first_printer_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            bom_path = Path(tmp) / 'bom.ini'
            bom_path.write_bytes(('\ufeff' + FIXTURE.read_text(encoding='utf-8')).encode('utf-8'))

            sections = parse_ini(bom_path)
            self.assertIn('printer:Original Prusa/MK4:Input Shaper 0.4 nozzle', sections)

    def test_custom_mapping_copies_ignored_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            ini_path = Path(tmp) / 'custom.ini'
            ini_path.write_text(
                '\n'.join([
                    '[filament:Mapped PLA]',
                    'filament_type = PLA',
                    'filament_spool_weight = 750',
                    '',
                    '[printer:Printer A]',
                    'nozzle_diameter = 0.4',
                ]),
                encoding='utf-8',
            )
            log = ConversionLog()
            bundle_path = convert_ini_to_orca(
                ini_path,
                Path(tmp) / 'out',
                log=log,
                custom_mappings={
                    'filament': {
                        'filament_spool_weight': {
                            'target': 'filament_custom_spool_weight',
                            'as_list': True,
                        }
                    }
                },
            )
            bundle = read_bundle(bundle_path)
            filament = next(data for name, data in bundle.items() if name.startswith('filament/'))

            self.assertEqual(filament['filament_custom_spool_weight'], ['750'])
            skipped = [key for section in log.sections for key, _ in section.skipped]
            self.assertNotIn('filament_spool_weight', skipped)


if __name__ == '__main__':
    unittest.main()
