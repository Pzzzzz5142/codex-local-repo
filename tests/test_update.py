import hashlib
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('update', Path(__file__).resolve().parents[1] / 'scripts/update.py')
update = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.record = ('Package: chatgpt\nVersion: 26.908.40834\nArchitecture: amd64\n'
                       'Filename: pool/main/c/chatgpt/chatgpt_26.908.40834_amd64.deb\n'
                       f'SHA256: {"a" * 64}\nDescription: desktop\n continuation\n')

    def test_real_debian_record_with_continuation(self):
        self.assertEqual(update.parse_packages(self.record)['Version'], '26.908.40834')

    def test_reject_wrong_arch_and_missing_package(self):
        for text in [self.record.replace('amd64', 'arm64'), self.record.replace('Package: chatgpt', 'Package: codex')]:
            with self.assertRaises(ValueError):
                update.parse_packages(text)

    def test_select_newest_stable_version_numerically(self):
        newer = self.record.replace('26.908.40834', '26.1001.100')
        for text in [newer + '\n' + self.record, self.record + '\n' + newer]:
            self.assertEqual(update.parse_packages(text)['Version'], '26.1001.100')

    def test_duplicate_and_conflicting_records(self):
        self.assertEqual(update.parse_packages(self.record + '\n' + self.record)['Version'], '26.908.40834')
        with self.assertRaises(ValueError):
            update.parse_packages(self.record + '\n' + self.record.replace('SHA256: a', 'SHA256: b'))

    def test_reject_unexpected_download_and_shell_injection(self):
        for text in [self.record.replace('pool/main/c/chatgpt/', 'https://evil.example/'),
                     self.record.replace('Version: 26.908.40834', 'Version: $(id)'),
                     self.record.replace('SHA256: a', 'SHA256: z')]:
            with self.assertRaises(ValueError):
                update.parse_packages(text)

    def test_signed_index_integrity(self):
        data = self.record.encode()
        release = f'SHA256:\n {hashlib.sha256(data).hexdigest()} {len(data)} {update.INDEX}\n'
        update.verify_index(release, data)
        with self.assertRaises(ValueError):
            update.verify_index(release, data + b'tampered')
        with self.assertRaises(ValueError):
            update.verify_index(release.replace(update.INDEX, 'other/Packages'), data)


if __name__ == '__main__':
    unittest.main()
