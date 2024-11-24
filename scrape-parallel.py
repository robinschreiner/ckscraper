import os
import requests
import time
from bs4 import BeautifulSoup
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Folder to save recipes
OUTPUT_DIR = Path("recipes")
OUTPUT_DIR.mkdir(exist_ok=True)

# Define a typical User-Agent
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

# Function to fetch a webpage
def fetch_page(url):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.text

# Function to parse a recipe
def parse_recipe(url):
    html_content = fetch_page(url)
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract title
    full_title = soup.title.get_text(strip=True)  # Get <title> content
    title = full_title.split(" von ")[0].strip()  # Remove everything after " von "
    
    # Extract ingredients
    ingredients_table = soup.find("table", class_="ingredients table-header")
    ingredients = []
    if ingredients_table:
        rows = ingredients_table.find_all("tr")
        for row in rows:
            amount = row.find("td", class_="td-left").get_text(strip=True)
            ingredient = row.find("td", class_="td-right").get_text(strip=True)
            ingredients.append(f"{amount} {ingredient}")
    
    # Extract nutritional values
    nutrition_section = soup.find("div", class_="recipe-nutrition_content ds-box ds-grid")
    nutrition = []
    if nutrition_section:
        nutrition_items = nutrition_section.find_all("div", class_="ds-col-3")
        for item in nutrition_items:
            label = item.find("h5").get_text(strip=True)
            value = item.get_text(strip=True).replace(label, "").strip()
            nutrition.append(f"{label}: {value}")
    
    # Extract recipe details
    meta_section = soup.find("small", class_="ds-recipe-meta rds-recipe-meta")
    recipe_details = []
    if meta_section:
        badges = meta_section.find_all("span", class_="rds-recipe-meta__badge")
        for badge in badges:
            recipe_details.append(badge.get_text(strip=True))
    
    # Extract description
    description_div = meta_section.find_next_sibling("div", class_="ds-box")
    description = description_div.get_text(strip=True) if description_div else "No description available."
    
    # Format the recipe content
    recipe_content = (
        f"{title}\n\n"
        f"Ingredients:\n" + "\n".join(ingredients) + "\n\n"
        f"Nutrition:\n" + "\n".join(nutrition) + "\n\n"
        f"Details:\n" + "\n".join(recipe_details) + "\n\n"
        f"Description:\n{description}"
    )
    
    return title, recipe_content

# Function to save the recipe to a text file
def save_recipe(title, content):
    # Replace any invalid characters in the title for filenames
    sanitized_title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
    filename = OUTPUT_DIR / f"{sanitized_title}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")

# Function to process a single recipe URL
def process_recipe(url):
    try:
        print(f"Scraping: {url}")
        title, content = parse_recipe(url)
        save_recipe(title, content)
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")

# Function to scrape recipes in parallel
def scrape_recipes_parallel(url_list, max_workers=5):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(process_recipe, url_list)

# Load URLs from a file
def load_urls_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]
    return urls

# Main function
if __name__ == "__main__":
    # Example: Load URLs from a file called 'urls.txt'
    url_file = "urls.txt"  # Place your file with URLs here
    if not os.path.exists(url_file):
        print(f"URL file '{url_file}' not found.")
        exit(1)
    
    recipe_urls = load_urls_from_file(url_file)
    print(f"Loaded {len(recipe_urls)} URLs.")
    
    # Scrape recipes in parallel
    scrape_recipes_parallel(recipe_urls, max_workers=10)  # Adjust max_workers as needed
