import wikipedia

try:
    print("Searching Wikipedia for 'eukaryotic cell'...")
    # wikipedia.set_rate_limiting(True) # Be polite
    page = wikipedia.page("eukaryotic cell", auto_suggest=True)
    print(f"Page Title: {page.title}")
    print(f"Images found: {len(page.images)}")
    for img in page.images[:10]:
        print(f" - {img}")
        
    print("\nAttempting 'lion'...")
    page = wikipedia.page("lion", auto_suggest=True)
    print(f"Page Title: {page.title}")
    for img in page.images[:5]:
        print(f" - {img}")

except Exception as e:
    print(f"Error: {e}")
