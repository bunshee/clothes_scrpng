import time
from playwright.sync_api import sync_playwright

def debug_pullandbear_page(url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) # Keep headless=False for visual debugging
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()

        print(f"Navigating to: {url}...")
        page.goto(url, wait_until="load")
        time.sleep(5) # Give it some time to load everything

        print("Taking screenshot...")
        page.screenshot(path="pullandbear_debug_screenshot.png")
        print("Screenshot saved to pullandbear_debug_screenshot.png")

        print("Saving page HTML...")
        with open("pullandbear_debug_page.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("Page HTML saved to pullandbear_debug_page.html")

        browser.close()
        print("Browser closed.")

if __name__ == "__main__":
    pullandbear_url = "https://www.pullandbear.com/fr/homme/nouveautes-n6280"
    debug_pullandbear_page(pullandbear_url)
