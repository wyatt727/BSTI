import json
import re
import sys
import hashlib
from htmlwebshot import WebShot, Config
import os
from bs4 import BeautifulSoup
import html

class XMLScreenshotTool:
    def __init__(self, xml_file, config_file, output_dir):
        self.xml_file = xml_file
        self.config_file = config_file
        self.output_dir = output_dir
        try:
            print("[+] Loading JSON config...")
            self.config = self.load_json_config()
            print("[+] Loading XML content...")
            self.xml_content = self.load_xml_content()
            print("[+] Initialization successful.")
        except Exception as e:
            print(f"Initialization error: {e}")
            sys.exit(1)

    def load_json_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                print("[+] JSON config loaded successfully.")
                return config
        except Exception as e:
            print(f"Error loading JSON config: {e}")
            sys.exit(1)

    def load_xml_content(self):
        try:
            with open(self.xml_file, 'r') as f:
                content = f.read()
                print("[+] XML file loaded successfully.")
                return content
        except Exception as e:
            print(f"Error loading XML file: {e}")
            sys.exit(1)

    def extract_specific_lines(self, tag, verify_words):
        try:
            soup = BeautifulSoup(self.xml_content, 'xml')
            elements = soup.find_all(tag)
            if not elements:
                print(f"No match found for tag '{tag}'")
                return ""

            # Filter and format content that contains verify words
            content_parts = []
            for elem in elements:
                content = str(elem)
                if any(word in content for word in verify_words):
                    content_parts.append(content)
                    
            if not content_parts:
                print(f"No verify words found in tag '{tag}'")
            return "\n".join(content_parts)
        except Exception as e:
            print(f"Error extracting specific lines: {e}")
            return ""

    def highlight_keywords_in_content(self, content, verify_words):
        try:
            escaped_content = html.escape(content)

            highlighted_content = escaped_content
            for keyword in verify_words:
                escaped_keyword = html.escape(keyword)
                highlighted_content = re.sub(
                    re.escape(escaped_keyword),
                    f'<span style="background-color: red; color: white; font-weight: bold;">{escaped_keyword}</span>',
                    highlighted_content
                )
            return highlighted_content
        except Exception as e:
            print(f"Error highlighting keywords: {e}")
            return content


    def create_html_with_highlights(self, highlighted_content):
        try:
            # Define CSS for styling
            css = """
            body {
                background-color: #1e1e1e;
                color: #dcdcdc;
                font-family: 'Consolas', 'Courier New', monospace;
                white-space: pre-wrap;
                margin: 20px;
                font-size: 16px;
            }
            span {
                background-color: red;
                color: white;
                font-weight: bold;
            }
            """
            
            # Create the final HTML content
            html_content = f"""
            <html>
            <head><style>{css}</style></head>
            <body>
            <pre><code>{highlighted_content}</code></pre>
            </body>
            </html>
            """
            return html_content
        except Exception as e:
            print(f"Error creating HTML: {e}")
            return ""


    def save_html_to_file(self, html_content, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML content saved to {file_path}")
        except Exception as e:
            print(f"Error saving HTML to file: {e}")

    def take_screenshot(self, html_content, output_path):
        try:
            if sys.platform == "win32":
                shot = WebShot(
                    quality=100,
                    config=Config(
                        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe",
                        wkhtmltoimage=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltoimage.exe",
                    ),
                )
            elif sys.platform == "darwin":  # MacOS specific handling
                # Check common MacOS installation paths for wkhtmltopdf
                mac_paths = [
                    "/usr/local/bin/wkhtmltopdf",
                    "/usr/local/bin/wkhtmltoimage",
                    "/opt/homebrew/bin/wkhtmltopdf",
                    "/opt/homebrew/bin/wkhtmltoimage"
                ]
                
                # Use first path that exists
                wkhtmltopdf_path = next((path for path in mac_paths if os.path.exists(path)), None)
                wkhtmltoimage_path = next((path for path in mac_paths if os.path.exists(path) and "image" in path), None)
                
                if wkhtmltopdf_path and wkhtmltoimage_path:
                    print(f"[+] Found wkhtmltopdf at {wkhtmltopdf_path}")
                    print(f"[+] Found wkhtmltoimage at {wkhtmltoimage_path}")
                    shot = WebShot(
                        quality=100,
                        config=Config(
                            wkhtmltopdf=wkhtmltopdf_path,
                            wkhtmltoimage=wkhtmltoimage_path,
                        ),
                    )
                else:
                    print("[!] Warning: Could not find wkhtmltopdf/wkhtmltoimage in common MacOS locations.")
                    print("[!] Using default configuration which may not work correctly.")
                    shot = WebShot(quality=100)
            else:
                shot = WebShot(quality=100)

            shot.create_pic(html=html_content, output=output_path)
            print(f"[+] Screenshot saved as {output_path}")
        except Exception as e:
            print(f"Error taking screenshot: {e}")

    def process_screenshots(self):
        try:
            print("[+] Processing screenshots...")
            os.makedirs(self.output_dir, exist_ok=True) 

            for plugin, details in self.config.get('plugins', {}).items():
                xml_tags = details.get('xml_tags', [])
                verify_words = details.get('verify_words', [])
                screenshot_taken = False
                
                print(f"[+] Processing plugin '{plugin}' with tags: {xml_tags} and verify words: {verify_words}")
                
                for tag in xml_tags:
                    if screenshot_taken:
                        break

                    content = self.extract_specific_lines(tag, verify_words)
                    
                    if content:
                        highlighted_content = self.highlight_keywords_in_content(content, verify_words)
                        html_content = self.create_html_with_highlights(highlighted_content)
                        
                        plugin_hash = hashlib.md5(plugin.lower().encode()).hexdigest()
                        output_file = os.path.join(self.output_dir, f"{plugin_hash}.png")

                        try:
                            self.take_screenshot(html_content, output_file)
                            screenshot_taken = True
                        except Exception as e:
                            print(f"Unable to capture screenshot for {plugin}: {e}")
                            break
        except Exception as e:
            print(f"Error processing screenshots: {e}")