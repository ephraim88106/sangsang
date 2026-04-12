import os
import re

def refactor_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the start of the fixed-side-ad block
    ad_start_marker = '<div class="fixed-side-ad">'
    ad_start_index = content.find(ad_start_marker)
    
    if ad_start_index == -1:
        print(f"No fixed-side-ad found in {file_path}")
        return

    # Check for the comment before it
    comment_marker = '<!-- 우측 고정 사이드바 광고 -->'
    comment_index = content.find(comment_marker)
    
    actual_start_index = ad_start_index
    if comment_index != -1 and 0 < ad_start_index - comment_index < 100:
        # Check if there are only whitespace/newlines between them
        between = content[comment_index + len(comment_marker) : ad_start_index]
        if not between.strip():
            actual_start_index = comment_index

    # Find the end of the block. It should be before </body>
    body_end_marker = '</body>'
    body_end_index = content.lower().find(body_end_marker)
    
    if body_end_index == -1:
        print(f"No </body> found in {file_path}")
        return

    # The ad block is everything from actual_start_index up to the last </div> before body_end_index
    # Actually, the user says it's at the very bottom.
    # Let's find the last </div> before body_end_index
    last_div_end = content.rfind('</div>', 0, body_end_index)
    
    # DEBUG
    if file_path == 'index.html':
        print(f"DEBUG: ad_start_index={ad_start_index}")
        print(f"DEBUG: actual_start_index={actual_start_index}")
        print(f"DEBUG: body_end_index={body_end_index}")
        print(f"DEBUG: last_div_end={last_div_end}")
        if last_div_end != -1:
            print(f"DEBUG: content at last_div_end={content[last_div_end:last_div_end+10]}")

    if last_div_end == -1 or last_div_end < ad_start_index:
        print(f"Could not find closing </div> for fixed-side-ad in {file_path}")
        return
    
    ad_block_end = last_div_end + len('</div>')
    ad_block = content[actual_start_index:ad_block_end].strip()
    
    # Remove the block (and any surrounding whitespace/newlines to avoid gaps)
    # We'll replace it with empty string
    new_content = content[:actual_start_index] + content[ad_block_end:]
    
    # Now find insertion point
    # After <body> tag and after <canvas id="season-canvas"></canvas> if exists
    body_pattern = re.compile(r'(<body[^>]*>)(\s*<canvas id="season-canvas"></canvas>)?', re.IGNORECASE)
    body_match = body_pattern.search(new_content)
    
    if not body_match:
        print(f"Could not find <body> tag in {file_path}")
        return
    
    insertion_point = body_match.end()
    
    # Insert ad_block
    final_content = new_content[:insertion_point] + "\n\n" + ad_block + "\n" + new_content[insertion_point:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"Refactored {file_path}")

def main():
    files = ['index.html'] # Just test index.html for now
    for file in files:
        refactor_html(file)

if __name__ == "__main__":
    main()
