from browser import Browser
import hashlib
import random

def main():
    browser = Browser()
    
    print("--- Step 1: Navigate to Sign In ---")
    browser.fetch("https://accounts.google.com/signin")
    # print(browser.render_page()) # Optional: View page
    
    print("\n--- Step 2: Click Create Account ---")
    # Look for "Create account" link/button
    browser.click_button("Create account")
    # The click_handler should detect WIZ and auto-navigate or we might need to fetch manually if it's a simple link
    # Assuming the click extracted the URL and we need to fetch it if auto-nav didn't happen
    if 'signup' not in browser.current_url:
        # Fallback: Find the link manually if click_button didn't trigger fetch
        for a in browser.soup.find_all('a'):
            if 'Create account' in a.get_text():
                href = a.get('href')
                if href:
                    browser.fetch(href)
                    break
    
    print(f"Current URL: {browser.current_url}")
    
    print("\n--- Step 3: Fill Name Page ---")
    # Fill First and Last Name
    browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'})
    # Submit via RPC
    browser.submit_wiz_rpc('userspace.NameSubmit')
    
    print(f"Current URL: {browser.current_url}")
    # print(browser.render_page())
    
    print("\n--- Step 4: Select Username ---")
    # The previous step should have landed us on the username page
    # We need to pick a suggestion. Usually the first one or a generated one.
    # For this demo, we assume the logic picks 'steveboils' + random
    # In a real scenario, we'd parse the suggestions from the DOM.
    # Let's simulate filling the custom username field if available, or clicking a suggestion.
    # Google often auto-selects the first available. If we need to type:
    rand_num = str(random.randint(100000, 999999))
    username = f"steveboils{rand_num}"
    
    # Try to fill the username field (often id="username" or similar)
    browser.fill_form(0, {'username': username})
    
    # Click Next
    browser.click_button("Next")
    
    print(f"Current URL: {browser.current_url}")
    
    print("\n--- Step 5: Birthday & Gender ---")
    # Fill Birthday
    browser.fill_form(0, {
        'month': '1', # January
        'day': '15',
        'year': '1990',
        'gender': '1' # Male
    })
    browser.click_button("Next")
    
    print(f"Current URL: {browser.current_url}")
    # print(browser.render_page())
    
    print("\n--- Step 6: Password Creation ---")
    # Generate Password: MD5(email) + "!"
    email = f"{username}@gmail.com"
    md5_hash = hashlib.md5(email.encode()).hexdigest()
    password = f"{md5_hash}!"
    
    print(f"Generated Password for {email}: {password}")
    
    browser.fill_form(0, {
        'password': password,
        'confirm_password': password
    })
    browser.click_button("Next")
    
    print(f"Current URL: {browser.current_url}")
    
    print("\n--- Final Page Content ---")
    print(browser.render_page())

if __name__ == "__main__":
    main()
