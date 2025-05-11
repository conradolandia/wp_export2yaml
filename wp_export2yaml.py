import lxml.etree as etree
import yaml
import sys
import argparse
from datetime import datetime
import subprocess
import json
import os
from markdownify import markdownify as md
from typing import List, Optional, Dict, Any
from bs4 import MarkupResemblesLocatorWarning
import warnings

# Suppress BeautifulSoup warning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Define namespaces for lxml XPath
NAMESPACES = {
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp': 'http://wordpress.org/export/1.2/',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'rss': 'http://purl.org/rss/1.0/modules/syndication/'
}

# Custom representer for multiline strings as block scalars
def str_presenter(dumper, data):
    if '\n' in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

def convert_html_to_markdown(html_content: str) -> str:
    """
    Converts HTML content to Markdown format using markdownify.
    
    Args:
        html_content: The HTML content to convert
        
    Returns:
        The converted Markdown content
    """
    if not html_content:
        return ""
        
    return md(
        html_content,
        heading_style="ATX",  # Use # style headings
        bullets="-",         # Use - for lists
        convert=['b', 'i', 'em', 'strong', 'p', 'a', 'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'br', 'hr'],
        autolinks=True,      # Convert URLs to links
        default_title=True,  # Use alt text as link title
        escape_asterisks=False,  # Don't escape * in text
        escape_underscores=False,  # Don't escape _ in text
        keep_inline_images_in=['p', 'li'],  # Keep inline images in paragraphs and list items
        newline_style='\n',  # Use \n for newlines
        strip_links=False,   # Keep links
        strip_images=False,  # Keep images
        wrap=True,          # Wrap text
        wrap_width=80       # Wrap at 80 characters
    )

def process_gallery_ids(posts_data: List[Dict[str, Any]], post: Dict[str, Any]) -> None:
    """
    Processes gallery IDs in a post's custom fields, replacing them with file paths.
    
    Args:
        posts_data: List of all processed posts
        post: The current post being processed
    """
    if 'galeria' not in post['custom_fields']:
        return
        
    gallery_data = post['custom_fields']['galeria']
    if not isinstance(gallery_data, (str, list)):
        return
        
    # Convert string to list if necessary
    if isinstance(gallery_data, str):
        gallery_ids = [id.strip() for id in gallery_data.split(',')]
    else:
        gallery_ids = gallery_data
        
    image_urls = []
    for attachment_id in gallery_ids:
        # Find the attachment post
        attachment = next(
            (p for p in posts_data 
             if p.get('post_type') == 'attachment' 
             and str(p.get('id')) == str(attachment_id)),
            None
        )
        
        if attachment and '_wp_attached_file' in attachment['custom_fields']:
            image_urls.append(attachment['custom_fields']['_wp_attached_file'])
        else:
            image_urls.append(attachment_id)  # Keep original ID if not found
            
    post['custom_fields']['galeria'] = image_urls

def call_php_unserialize(serialized_string: str, php_script_path: str) -> Optional[Any]:
    """
    Calls the external PHP script to unserialize a string.
    Returns the deserialized Python object or None if deserialization fails (gracefully).
    Returns an error dictionary if the PHP script execution fails unexpectedly.
    """
    if not serialized_string:
        return None

    try:
        # Ensure we have a string, not bytes
        if isinstance(serialized_string, bytes):
            serialized_string = serialized_string.decode('utf-8', errors='replace')
        elif not isinstance(serialized_string, str):
            serialized_string = str(serialized_string)
            
        # Execute the PHP script, passing the string via STDIN
        process = subprocess.run(
            ['php', php_script_path],
            input=serialized_string,  # Pass string directly, subprocess will handle encoding
            capture_output=True,
            text=True,  # Decode stdout/stderr as text
            check=False,
            encoding='utf-8'  # Explicitly set encoding
        )

        # Check if PHP script executed successfully
        if process.returncode != 0:
             sys.stderr.write(f"Error executing PHP script '{php_script_path}'. Return code: {process.returncode}\n")
             sys.stderr.write(f"STDERR: {process.stderr}\n")
             sys.stderr.write(f"STDOUT: {process.stdout}\n")
             return {'_deserialization_error': 'PHP script execution failed', 'return_code': process.returncode, 'stderr': process.stderr, 'stdout_raw': process.stdout}

        # Parse JSON output
        try:
            result = json.loads(process.stdout)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error decoding JSON from PHP script output: {e}\n")
            sys.stderr.write(f"Raw PHP STDOUT: {process.stdout}\n")
            return {'_deserialization_error': 'Invalid JSON output from PHP script', 'json_error': str(e), 'stdout_raw': process.stdout}

        # Check for deserialization error
        if isinstance(result, dict) and 'error' in result:
            return None

        return result

    except FileNotFoundError:
        sys.stderr.write(f"Error: PHP executable not found. Make sure 'php' is in your system's PATH.\n")
        return {'_deserialization_error': 'PHP executable not found'}
    except Exception as e:
        sys.stderr.write(f"An unexpected error occurred calling the PHP script: {e}\n")
        return {'_deserialization_error': f'Unexpected Python error: {e}', 'error_type': type(e).__name__}

def parse_wxr2yaml(
    xml_filepath: str, 
    yaml_filepath: str, 
    php_script_path: str,
    included_post_types: Optional[List[str]] = None,
    excluded_custom_fields: Optional[List[str]] = None,
    convert_to_markdown: bool = False
) -> None:
    """
    Parse a WordPress WXR export file and convert it to YAML format.
    
    Args:
        xml_filepath: Path to the WordPress XML export file (.wxr)
        yaml_filepath: Path where the YAML output file will be saved
        php_script_path: Path to the PHP deserializer script
        included_post_types: List of post types to include (None for all)
        excluded_custom_fields: List of custom fields to exclude
        convert_to_markdown: Whether to convert HTML content to Markdown
    """
    posts_data = []
    attachments = {}  # Dictionary to store attachment data

    # Validate PHP script path
    if not os.path.isfile(php_script_path):
        print(f"Error: El script PHP no fue encontrado en {php_script_path}")
        sys.exit(1)

    try:
        # Use iterparse to process the XML element by element
        context = etree.iterparse(xml_filepath, events=('end',), tag='item', recover=True)

        print(f"Iniciando parseo de {xml_filepath} con lxml iterparse...")
        print(f"Utilizando script PHP en {php_script_path} para deserialización.")

        # First pass: collect all posts and attachments
        for event, item in context:
            try:
                post = {}

                # Helper to safely get text using xpath and namespaces
                def get_text(xpath_expr):
                    elements = item.xpath(xpath_expr, namespaces=NAMESPACES)
                    if not elements or elements[0].text is None:
                        return None
                    # Ensure we return a string, not bytes
                    text = elements[0].text
                    if isinstance(text, bytes):
                        return text.decode('utf-8', errors='replace')
                    return text

                # Extract basic fields using xpath
                # Extract WordPress specific fields using xpath with wp namespace
                post['id'] = get_text('wp:post_id')
                post['title'] = get_text('title')
                post['slug'] = get_text('wp:post_name') # Slug
                post['post_type'] = get_text('wp:post_type')
                post['post_date'] = get_text('wp:post_date')
                post['content'] = get_text('content:encoded')
                #post['link'] = get_text('link')
                #post['status'] = get_text('wp:status')
                #post['post_parent'] = get_text('wp:post_parent')
                #post['menu_order'] = get_text('wp:menu_order')
                
                # Add more fields here if needed
                
                # Convert content to Markdown if requested
                if convert_to_markdown and post['content']:
                    post['content'] = convert_html_to_markdown(post['content'])

                # Extract taxonomies
                post['taxonomies'] = {}
                for category in item.xpath('category'):
                    domain = category.get('domain')
                    nicename = category.get('nicename')
                    term_name = category.text

                    if domain and nicename is not None:
                         if domain not in post['taxonomies']:
                             post['taxonomies'][domain] = []

                         post['taxonomies'][domain].append({
                             'name': term_name,
                             'slug': nicename
                         })

                # Extract metadata and custom fields using wp:postmeta
                post['custom_fields'] = {}
                for postmeta in item.xpath('wp:postmeta', namespaces=NAMESPACES):
                    meta_key_elem = postmeta.find('wp:meta_key', NAMESPACES)
                    meta_value_elem = postmeta.find('wp:meta_value', NAMESPACES)

                    if meta_key_elem is not None and meta_key_elem.text and meta_value_elem is not None:
                        meta_key = meta_key_elem.text
                        
                        # Skip excluded custom fields
                        if excluded_custom_fields and meta_key in excluded_custom_fields:
                            continue
                            
                        meta_value_raw = meta_value_elem.text # Can be None if empty

                        # Ensure meta_value_raw is a string
                        if meta_value_raw is not None:
                            if isinstance(meta_value_raw, bytes):
                                meta_value_raw = meta_value_raw.decode('utf-8', errors='replace')
                            elif not isinstance(meta_value_raw, str):
                                meta_value_raw = str(meta_value_raw)

                        # --- Attempt PHP Deserialization ---
                        meta_value_processed = meta_value_raw # Default to raw value

                        # Heuristic: Does it look like PHP serialized data?
                        if meta_value_raw and isinstance(meta_value_raw, str) and \
                           len(meta_value_raw) > 2 and \
                           meta_value_raw[0] in ('a', 's', 'O', 'i', 'd', 'b', 'N') and meta_value_raw[1] == ':':

                             # Try to deserialize using the PHP script
                             deserialized_result = call_php_unserialize(meta_value_raw, php_script_path)

                             # Check the result from the PHP call
                             if deserialized_result is not None and not (isinstance(deserialized_result, dict) and '_deserialization_error' in deserialized_result):
                                 # Deserialization was successful and returned a valid value
                                 meta_value_processed = deserialized_result
                             elif isinstance(deserialized_result, dict) and '_deserialization_error' in deserialized_result:
                                 # An error occurred during the PHP call or JSON decoding
                                 sys.stderr.write(f"Warning: Error processing meta_key '{meta_key}' (ID {post.get('id')}). PHP helper error: {deserialized_result.get('_deserialization_error', 'Unknown')}. Keeping raw string.\n")
                                 meta_value_processed = meta_value_raw # Keep raw string on error
                             else:
                                 # Deserialization failed according to the PHP script
                                 meta_value_processed = meta_value_raw # Keep raw string on failure

                        # Store the processed value
                        if meta_key in post['custom_fields']:
                            current_value = post['custom_fields'][meta_key]
                            if not isinstance(current_value, list):
                                post['custom_fields'][meta_key] = [current_value, meta_value_processed]
                            else:
                                post['custom_fields'][meta_key].append(meta_value_processed)
                        else:
                            post['custom_fields'][meta_key] = meta_value_processed

                # Always collect attachments for gallery resolution
                if post['post_type'] == 'attachment':
                    attachments[post['id']] = post

                # Only add to posts_data if included_post_types is None or matches
                if (included_post_types is None) or (post['post_type'] in included_post_types):
                    posts_data.append(post)

            finally:
                # Clean up the element and its ancestors
                item.clear()
                # Remove references to previous siblings
                prev = item.getprevious()
                if prev is not None:
                    item.getparent().remove(prev)
                # Remove the current element
                if item.getparent() is not None:
                    item.getparent().remove(item)

        print(f"Parseo completado. {len(posts_data)} ítems procesados.")

        # Second pass: process gallery IDs
        print("Procesando IDs de galería...")
        for post in posts_data:
            if 'galeria' in post['custom_fields']:
                gallery_data = post['custom_fields']['galeria']
                if not isinstance(gallery_data, (str, list)):
                    continue
                    
                # Convert string to list if necessary
                if isinstance(gallery_data, str):
                    gallery_ids = [id.strip() for id in gallery_data.split(',')]
                else:
                    gallery_ids = gallery_data
                    
                image_urls = []
                for attachment_id in gallery_ids:
                    # Find the attachment in our dictionary
                    attachment = attachments.get(str(attachment_id))
                    
                    if attachment and '_wp_attached_file' in attachment['custom_fields']:
                        image_urls.append(attachment['custom_fields']['_wp_attached_file'])
                    else:
                        image_urls.append(attachment_id)  # Keep original ID if not found
                        
                post['custom_fields']['galeria'] = image_urls

    except FileNotFoundError:
        print(f"Error: El archivo XML no fue encontrado en {xml_filepath}")
        sys.exit(1)
    except etree.XMLSyntaxError as e:
        print(f"Error al parsear el archivo XML (lxml): {e}")
        print("Asegúrate de que el archivo es un XML de exportación de WordPress válido y bien formado.")
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el parseo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Write to YAML file
    try:
        print(f"Escribiendo datos en {yaml_filepath}...")
        with open(yaml_filepath, 'w', encoding='utf-8') as outfile:
            yaml.dump(posts_data, outfile, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"Archivo YAML guardado exitosamente en {yaml_filepath}.")
    except IOError as e:
        print(f"Error al escribir el archivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error inesperado al escribir el archivo YAML: {e}")
        sys.exit(1)
