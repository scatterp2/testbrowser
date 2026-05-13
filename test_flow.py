#!/usr/bin/env python3
"""Test script for Google signup flow"""
from browser import Browser
def main():
    browser = Browser()
    print("=== Testing Google Signup Flow ===\n")
    # Step 1: Go to sign-in page
    print("\n[Step 1] Fetching Google sign-in page...")
    if not browser.fetch("https://accounts.google.com/signin"):
        print("Failed to fetch sign-in page")
        return
    browser.render_page()
    # Step 2: Click "Create account" button (not link)
    print("\n[Step 2] Looking for 'Create account' button...")
    if browser.click_button("Create account"):
        browser.render_page()
        # Extract WIZ data
        print("\n[Step 2b] Extracting WIZ global data...")
        wiz_data = browser.extract_wiz_data()
        if wiz_data:
            print(f"WIZ tokens found: {list(wiz_data.get('tokens', {}).keys())}")
            print(f"WIZ actions found: {wiz_data.get('actions', [])}")
        # Step 3: Fill in name and submit
        print("\n[Step 3] Filling name form...")
        if browser.fill_form(0, {'firstName': 'steve', 'lastName': 'boils'}):
            print("Form filled successfully")
            print("\n[Step 4] Submitting form...")
            if browser.submit_form(0):
                browser.render_page()
                # Check if we reached the username page (page 3)
                if 'username' in browser.current_html.lower() or 'choose your username' in browser.current_html.lower():
                    print("\n✓✓✓ SUCCESS: Reached username selection page (Page 3)! ✓✓✓")
                else:
                    print("\n✗ Did not reach username page yet - checking content...")
                    # Show what we got
                    title = browser.current_soup.find('title')
                    if title:
                        print(f"Current page title: {title.get_text(strip=True)}")
            else:
                print("Form submission failed")
        else:
            print("Failed to fill form")
    else:
        print("Could not find 'Create account' button")
if __name__ == "__main__":
    main()
