import unittest

from browser import Browser


def make_browser(html, url='https://accounts.google.com/lifecycle/steps/signup/name'):
    browser = object.__new__(Browser)
    browser.current_url = url
    browser.current_html = html
    browser.current_soup = None
    browser.wiz_data = {}
    browser.pending_form_data = {}
    return browser


class SignupClassificationTests(unittest.TestCase):
    def test_classifies_phone_required_step(self):
        browser = make_browser('''
            <main><h1>Verify your phone number</h1>
            <label for="phone">Phone number</label><input id="phone" autocomplete="tel"></main>
        ''', 'https://accounts.google.com/lifecycle/steps/signup/phone')

        self.assertEqual(browser.classify_signup_step(), 'phone')
        step, can_fill = browser.fill_current_signup_step({'phoneNumber': '+15555550123'})

        self.assertEqual(step, 'phone')
        self.assertTrue(can_fill)
        self.assertEqual(browser.pending_form_data['phoneNumber'], '+15555550123')

    def test_classifies_phone_optional_storage_experiment(self):
        browser = make_browser('''
            <main><h1>Add a phone number?</h1>
            <p>You get 5 GB of storage until a number is supplied.</p>
            <button>Skip</button><button>Next</button></main>
        ''', 'https://accounts.google.com/lifecycle/steps/signup/storage')

        self.assertEqual(browser.classify_signup_step(), 'phone_optional')

    def test_classifies_locale_flow_that_skips_phone(self):
        browser = make_browser('''
            <main><h1>Create a password</h1>
            <label>Password<input name="Passwd" type="password"></label>
            <label>Confirm<input name="ConfirmPasswd" type="password"></label></main>
        ''', 'https://accounts.google.com/lifecycle/steps/signup/password?gl=CO')

        self.assertEqual(browser.classify_signup_step(), 'password')
        step, can_fill = browser.fill_current_signup_step({'password': 'Secret123!!'})

        self.assertEqual(step, 'password')
        self.assertTrue(can_fill)
        self.assertEqual(browser.pending_form_data['confirm'], 'Secret123!!')

    def test_interaction_script_is_data_driven_not_har_rpc_driven(self):
        browser = make_browser('<input aria-label="First name"><button>Next</button>')
        script = browser._build_interaction_script({'firstName': 'Ada'}, submit_text='Next')

        self.assertIn('Ada', script)
        self.assertIn('firstName', script)
        self.assertNotIn('E815hb', script)
        self.assertNotIn('batchexecute', script)


if __name__ == '__main__':
    unittest.main()
