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
    pages = get_notion_pages()
    index_links = ""

    for page in pages:
        # Extract title and slug
        title = page['properties']['Name']['title'][0]['plain_text']
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower())  # "My Note" -> "my-note"
        filename = f"{slug}.html"

        last_edited = page['last_edited_time'].split('T')[0]

        # Get content
        blocks = get_page_content(page['id'])
        content_html = "".join([parse_notion_block_to_html(b) for b in blocks])

        # Build page HTML
        page_html = f"""
        <html>
          <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <link rel="stylesheet" href="style.css">
          </head>
          <body class="prose lg:prose-xl mx-auto p-8">
            <h1>{title}</h1>
            <p class="text-sm text-gray-500">نشرت في: {last_edited}</p>
            {content_html}
          </body>
        </html>
        """

        with open(filename, "w", encoding="utf-8") as f:
            f.write(page_html)

        # Add link to index
        index_links += f"<li><a href='{filename}' class='text-blue-600 hover:underline'>{title}</a> ({last_edited})</li>\n"

    # Update index (personal_newsletter.html)
    with open("personal_newsletter.html", "r", encoding="utf-8") as f:
        index_html = f.read()

    new_html = re.sub(
        r'<!-- Notes Container Section -->[\s\S]*<!-- End Notes Container Section -->',
        f'<!-- Notes Container Section -->\n<ul>{index_links}</ul>\n<!-- End Notes Container Section -->',
        index_html
    )

    with open("personal_newsletter.html", "w", encoding="utf-8") as f:
        f.write(new_html)

# Run script
if __name__ == "__main__":
    generate_notes_html()
