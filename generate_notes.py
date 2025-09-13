# This Python script fetches notes from a Notion database and converts them to HTML.
# هذا السكربت يجيب المذكرات من Notion ويحوّلها إلى HTML (كل صفحة ملف منفصل + Index).

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
    elif block_type == 'quote':
        return f"<blockquote class='border-l-4 border-gray-300 pl-4 italic text-gray-700 my-4'>{html_content}</blockquote>"
    elif block_type == 'callout':
        icon = block['callout'].get('icon', {}).get('emoji', '💡')
        return f"<div class='bg-green-100 p-4 rounded-lg my-4 flex items-center'><span class='mr-2'>{icon}</span> {html_content}</div>"
    elif block_type == 'code':
        language = block['code'].get('language', '')
        return f"<pre class='bg-gray-900 text-white p-4 rounded-lg overflow-x-auto my-4'><code class='{language}'>{html_content}</code></pre>"
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
    """Generates HTML files for each Notion page and an index page."""
    # Create notes directory if it doesn't exist
    if not os.path.exists("notes"):
        os.makedirs("notes")

    pages = get_notion_pages()
    index_links = ""

    for page in pages:
        # Extract title and slug
        title = page['properties']['Name']['title'][0]['plain_text']
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower())
        filename = f"notes/{slug}.html" # Save in the 'notes' directory

        last_edited = page['last_edited_time'].split('T')[0]

        # Get content
        blocks = get_page_content(page['id'])
        content_html = "".join([parse_notion_block_to_html(b) for b in blocks])

        # Build page HTML
        page_html = f"""
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link rel="preconnect" href="https://fonts.googleapis.com">
            <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
            <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
            <style>
                body {{ font-family: 'Tajawal', sans-serif; }}
                .container {{ max-width: 1000px; }}
            </style>
        </head>
        <body class="bg-gray-50 text-gray-800">
            <div class="container mx-auto p-8">
                <a href="../personal_newsletter.html" class="text-blue-600 hover:underline mb-4 block">&larr; العودة للمذكرات</a>
                <h1 class="text-4xl md:text-5xl font-bold text-gray-900 mb-4">{title}</h1>
                <p class="text-sm text-gray-500 mb-8">نشرت في: {last_edited}</p>
                {content_html}
            </div>
        </body>
        </html>
        """

        with open(filename, "w", encoding="utf-8") as f:
            f.write(page_html)

        # Add link to index, pointing to the new location
        index_links += f"""
        <div class="bg-gray-50 rounded-lg p-6 shadow-md hover:shadow-xl transition-shadow duration-300">
            <h3 class="text-xl font-bold text-gray-900 mb-2">{title}</h3>
            <p class="text-sm text-gray-500 mb-4">نشرت في: {last_edited}</p>
            <a href="notes/{slug}.html" class="text-blue-600 font-semibold hover:underline">اقرأ المزيد &rarr;</a>
        </div>
        """

    # Update index (personal_newsletter.html)
    with open("personal_newsletter.html", "r", encoding="utf-8") as f:
        index_html = f.read()

    new_html = re.sub(
        r'<!-- Notes Container Section -->[\s\S]*<!-- End Notes Container Section -->',
        f'<!-- Notes Container Section -->\n<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">{index_links}</div>\n<!-- End Notes Container Section -->',
        index_html
    )

    with open("personal_newsletter.html", "w", encoding="utf-8") as f:
        f.write(new_html)

# Run script
if __name__ == "__main__":
    generate_notes_html()
