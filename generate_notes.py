# This Python script fetches notes from a Notion database and converts them to HTML.
# هذا السكربت يجيب المذكرات من Notion ويحولها لـ HTML.

import os
import requests
import json
import re

# Get the Notion API token and database ID from GitHub secrets
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_notion_pages():
    """Fetches all pages from the Notion database."""
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    data = response.json()
    return data.get("results", [])

def get_page_content(page_id):
    """Fetches the content (blocks) of a specific Notion page."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=headers)
    data = response.json()
    return data.get("results", [])

def parse_notion_block_to_html(block):
    """Converts a Notion block to its HTML equivalent."""
    block_type = block['type']
    html_content = ""

    if 'rich_text' in block[block_type]:
        for text_part in block[block_type]['rich_text']:
            plain_text = text_part['plain_text']
            annotations = text_part['annotations']

            # Add basic styling based on Notion's annotations
            if annotations['bold']:
                plain_text = f"<strong>{plain_text}</strong>"
            if annotations['italic']:
                plain_text = f"<em>{plain_text}</em>"
            if annotations['underline']:
                plain_text = f"<u>{plain_text}</u>"
            if annotations['strikethrough']:
                plain_text = f"<s>{plain_text}</s>"
            if annotations['code']:
                plain_text = f"<code>{plain_text}</code>"
            
            html_content += plain_text

    # Convert block types to HTML tags
    if block_type == 'paragraph':
        return f"<p class='text-gray-600 mb-4'>{html_content}</p>"
    elif block_type == 'heading_1':
        return f"<h1 class='text-4xl font-bold text-gray-900 mt-8 mb-4'>{html_content}</h1>"
    elif block_type == 'heading_2':
        return f"<h2 class='text-3xl font-bold text-gray-900 mt-6 mb-3'>{html_content}</h2>"
    elif block_type == 'bulleted_list_item':
        return f"<li class='text-gray-600'>{html_content}</li>"
    elif block_type == 'numbered_list_item':
        return f"<li class='text-gray-600'>{html_content}</li>"
    elif block_type == 'image':
        image_url = block['image']['file']['url']
        return f"<img src='{image_url}' alt='Image from Notion' class='w-full rounded-lg my-6'>"
    elif block_type == 'divider':
        return f"<hr class='my-8 border-t border-gray-200'>"
    else:
        # Fallback for unsupported block types
        return f"<p class='text-gray-600 mb-4'>[Unsupported block type: {block_type}]</p>"

def generate_notes_html():
    """Generates the full HTML content for the notes section."""
    pages = get_notion_pages()
    notes_html_content = ""

    for page in pages:
        # Extract title and date
        title = page['properties']['Name']['title'][0]['plain_text']
        last_edited = page['last_edited_time']
        formatted_date = last_edited.split('T')[0] # Get only the date part

        # Fetch page content
        page_content = get_page_content(page['id'])
        content_html = ""
        for block in page_content:
            content_html += parse_notion_block_to_html(block)

        # Create the note card
        note_card = f"""
        <div class="bg-gray-50 rounded-lg p-6 shadow-md hover:shadow-xl transition-shadow duration-300">
            <h3 class="text-xl font-bold text-gray-900 mb-2">{title}</h3>
            <p class="text-sm text-gray-500 mb-4">نشرت في: {formatted_date}</p>
            {content_html}
        </div>
        """
        notes_html_content += note_card

    return notes_html_content

# Main function to update the HTML file
if __name__ == "__main__":
    html_content = generate_notes_html()
    
    # Read the main HTML file
    with open("personal_newsletter.html", "r", encoding="utf-8") as file:
        main_html = file.read()

    # Find the notes section and replace its content
    start_tag = '<!-- Notes Container Section -->'
    end_tag = '<!-- End Notes Container Section -->'
    
    # Use regex to find and replace the content between the tags
    new_html = re.sub(
        r'<!-- Notes Container Section -->[\s\S]*<!-- End Notes Container Section -->',
        f'<!-- Notes Container Section -->\n{html_content}\n        <!-- End Notes Container Section -->',
        main_html
    )

    # Write the updated HTML back to the file
    with open("personal_newsletter.html", "w", encoding="utf-8") as file:
        file.write(new_html)
