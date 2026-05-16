from browser import Browser


def main():
    browser = Browser()

    print("--- Navigate to Google sign-in ---")
    if not browser.fetch("https://accounts.google.com/signin"):
        return

    print("\n--- Open signup ---")
    browser.click_button("Create account")
    print(f"Current URL: {browser.current_url}")

    print("\n--- Drive completable signup steps ---")
    result = browser.drive_signup_until_blocked()
    print(f"Current URL: {browser.current_url}")
    print(f"Result: {result}")

    print("\n--- Final Page Content ---")
    browser.render_page()


if __name__ == "__main__":
    main()
