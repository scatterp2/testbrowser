import json
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote_plus

from browser import Browser

HAR_PATH = Path('accounts.google.com_Archive [26-05-13 19-01-55].har')


class HarBackedRpcTests(unittest.TestCase):
    def setUp(self):
        self.browser = object.__new__(Browser)

    def test_parse_name_step_batchexecute_next_step(self):
        har = json.loads(HAR_PATH.read_text(encoding='utf-8'))
        entry = har['log']['entries'][34]
        parsed = self.browser._parse_batchexecute_response(entry['response']['content']['text'])
        self.assertEqual(self.browser._find_lifecycle_step(parsed), 'steps/signup/birthdaygender')

    def test_parse_birthdaygender_batchexecute_next_step(self):
        har = json.loads(HAR_PATH.read_text(encoding='utf-8'))
        entry = har['log']['entries'][66]
        parsed = self.browser._parse_batchexecute_response(entry['response']['content']['text'])
        self.assertEqual(self.browser._find_lifecycle_step(parsed), 'steps/signup/collectemailphone')

    def test_birthdaygender_rpc_payload_matches_har_shape(self):
        captured = {}

        def fake_submit(rpcid, inner_data_array, source_path):
            captured['rpcid'] = rpcid
            captured['inner_data_array'] = inner_data_array
            captured['source_path'] = source_path
            return True

        self.browser.current_url = 'https://accounts.google.com/lifecycle/steps/signup/birthdaygender?continue=https%3A%2F%2Faccounts.google.com%2F'
        self.browser.current_html = ''
        self.browser.submit_wiz_batchexecute = fake_submit

        ok = self.browser.submit_birthdaygender_form(3, 'January', 1970, 'Rather not say', recaptcha_token='<token>')

        self.assertTrue(ok)
        self.assertEqual(captured['rpcid'], 'eOY7Bb')
        self.assertEqual(captured['source_path'], '/lifecycle/steps/signup/birthdaygender')
        self.assertEqual(captured['inner_data_array'], [
            [1970, 1, 3],
            1,
            None,
            None,
            None,
            None,
            [None, None, 'https://accounts.google.com/'],
            ['<token>'],
        ])

    def test_name_rpc_payload_matches_har_shape(self):
        har = json.loads(HAR_PATH.read_text(encoding='utf-8'))
        entry = har['log']['entries'][34]
        post_text = entry['request']['postData']['text']
        params = parse_qs(post_text, keep_blank_values=True)
        f_req = json.loads(unquote_plus(params['f.req'][0]))
        rpcid, inner_json, unused, mode = f_req[0][0]

        self.assertEqual(rpcid, 'E815hb')
        self.assertIsNone(unused)
        self.assertEqual(mode, 'generic')
        self.assertEqual(json.loads(inner_json), ['steve', 'boils', None, None, None, [], None, 1])


if __name__ == '__main__':
    unittest.main()
