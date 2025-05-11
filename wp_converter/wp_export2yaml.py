import lxml.etree as etree
import yaml
import sys
import argparse
from datetime import datetime
import os
from markdownify import markdownify as md
from typing import List, Optional, Dict, Any
from bs4 import MarkupResemblesLocatorWarning, BeautifulSoup
import warnings
import phpserialize
import re
import fnmatch

# Suppress BeautifulSoup warning
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Define namespaces for lxml XPath
NAMESPACES = {
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "wp": "http://wordpress.org/export/1.2/",
    "dc": "http://purl.org/dc/elements/1.1/",
    "rss": "http://purl.org/rss/1.0/modules/syndication/",
}


# Custom representer for multiline strings as block scalars
def str_presenter(dumper, data):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


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
        bullets="-",  # Use - for lists
        convert=[
            "b",
            "i",
            "em",
            "strong",
            "p",
            "a",
            "img",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "ul",
            "ol",
            "li",
            "blockquote",
            "code",
            "pre",
            "br",
            "hr",
        ],
        autolinks=True,  # Convert URLs to links
        default_title=True,  # Use alt text as link title
        escape_asterisks=False,  # Don't escape * in text
        escape_underscores=False,  # Don't escape _ in text
        keep_inline_images_in=[
            "p",
            "li",
        ],  # Keep inline images in paragraphs and list items
        newline_style="\n",  # Use \n for newlines
        strip_links=False,  # Keep links
        strip_images=False,  # Keep images
        wrap=True,  # Wrap text
        wrap_width=80,  # Wrap at 80 characters
    )


def process_gallery_ids(posts_data: List[Dict[str, Any]], post: Dict[str, Any]) -> None:
    """
    Processes gallery IDs in a post's custom fields, replacing them with file paths.

    Args:
        posts_data: List of all processed posts
        post: The current post being processed
    """
    if "galeria" not in post["custom_fields"]:
        return

    gallery_data = post["custom_fields"]["galeria"]
    if not isinstance(gallery_data, (str, list)):
        return

    # Convert string to list if necessary
    if isinstance(gallery_data, str):
        gallery_ids = [id.strip() for id in gallery_data.split(",")]
    else:
        gallery_ids = gallery_data

    image_urls = []
    for attachment_id in gallery_ids:
        # Find the attachment post
        attachment = next(
            (
                p
                for p in posts_data
                if p.get("post_type") == "attachment"
                and str(p.get("id")) == str(attachment_id)
            ),
            None,
        )

        if attachment and "_wp_attached_file" in attachment["custom_fields"]:
            image_urls.append(attachment["custom_fields"]["_wp_attached_file"])
        else:
            image_urls.append(attachment_id)  # Keep original ID if not found

    post["custom_fields"]["galeria"] = image_urls


# Helper: Convert dicts with sequential integer keys to lists
def dict_to_list_if_sequential(d):
    if isinstance(d, dict):
        keys = list(d.keys())
        if keys == list(range(len(keys))):
            return [d[k] for k in sorted(d.keys())]
    return d


def try_php_unserialize(serialized_string: str):
    """
    Attempts to unserialize a PHP serialized string using phpserialize.
    Returns the deserialized Python object, or the original string on failure.
    Converts dicts with sequential integer keys to lists.
    """
    if not serialized_string:
        return serialized_string
    try:
        # phpserialize.loads expects bytes
        if isinstance(serialized_string, str):
            serialized_bytes = serialized_string.encode("utf-8", errors="replace")
        else:
            serialized_bytes = serialized_string
        result = phpserialize.loads(serialized_bytes, decode_strings=True)
        # Convert dicts with sequential integer keys to lists
        return dict_to_list_if_sequential(result)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to unserialize value: {e}\n")
        return serialized_string


def postprocess_markdown(md: str) -> str:
    # Insert double newline before headings, lists, and blockquotes if not already present
    md = re.sub(r"(?<!\n\n)(^|\n)([#\-])", r"\n\n\2", md)
    # Normalize line endings
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    # Remove more than two consecutive newlines
    while "\n\n\n" in md:
        md = md.replace("\n\n\n", "\n\n")
    return md.strip()


def wrap_inline_runs_in_paragraphs(html: str) -> str:
    """
    Group runs of inline elements and text nodes at the top level into a single <p>.
    Only true block elements remain as separate blocks.
    """
    soup = BeautifulSoup(html, "html.parser")
    block_tags = {
        "address",
        "article",
        "aside",
        "blockquote",
        "canvas",
        "dd",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "noscript",
        "ol",
        "output",
        "p",
        "pre",
        "section",
        "table",
        "tfoot",
        "ul",
        "video",
    }
    container = soup.body if soup.body else soup
    new_children = []
    buffer = []
    for child in list(container.children):
        # If it's a block element, flush buffer and add block
        if getattr(child, "name", None) in block_tags:
            if buffer:
                p = soup.new_tag("p")
                for item in buffer:
                    p.append(item)
                new_children.append(p)
                buffer = []
            new_children.append(child)
        # If it's a text node or inline element, buffer it
        elif getattr(child, "name", None) is None or child.name not in block_tags:
            buffer.append(child)
    # Flush any remaining buffer
    if buffer:
        p = soup.new_tag("p")
        for item in buffer:
            p.append(item)
        new_children.append(p)
    # Replace children
    container.clear()
    for item in new_children:
        container.append(item)
    return str(soup)


def html_paragraphize(html: str) -> str:
    # Convert two or more consecutive newlines between text to paragraph breaks
    html = re.sub(r"([^\n>])\n{2,}([^\n<])", r"\1</p><p>\2", html)
    # Convert a single newline between text to paragraph break
    html = re.sub(r"([^\n>])\n([^\n<])", r"\1</p><p>\2", html)
    # Replace two or more consecutive <br> tags with paragraph breaks
    html = re.sub(r"(<br\s*/?>\s*){2,}", "</p><p>", html, flags=re.IGNORECASE)
    # Replace <br> followed by a newline with paragraph break
    html = re.sub(r"<br\s*/?>\s*[\r\n]+", "</p><p>", html, flags=re.IGNORECASE)
    # Ensure the HTML starts and ends with a <p> for proper grouping
    html = html.strip()
    if not html.lower().startswith("<p>"):
        html = "<p>" + html
    if not html.lower().endswith("</p>"):
        html = html + "</p>"
    return html


def parse_wxr2yaml(
    xml_filepath: str,
    yaml_filepath: str,
    included_post_types: Optional[List[str]] = None,
    excluded_custom_fields: Optional[List[str]] = None,
    convert_to_markdown: bool = False,
) -> None:
    """
    Parse a WordPress WXR export file and convert it to YAML format.

    Args:
        xml_filepath: Path to the WordPress XML export file (.wxr)
        yaml_filepath: Path where the YAML output file will be saved
        included_post_types: List of post types to include (None for all)
        excluded_custom_fields: List of custom fields to exclude
        convert_to_markdown: Whether to convert HTML content to Markdown
    """
    posts_data = []
    attachments = {}  # Dictionary to store attachment data

    try:
        # Use iterparse to process the XML element by element
        context = etree.iterparse(
            xml_filepath, events=("end",), tag="item", recover=True
        )

        print(f"Iniciando parseo de {xml_filepath} con lxml iterparse...")

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
                        return text.decode("utf-8", errors="replace")
                    return text

                # Extract basic fields using xpath
                # Extract WordPress specific fields using xpath with wp namespace
                post["id"] = get_text("wp:post_id")
                post["title"] = get_text("title")
                post["slug"] = get_text("wp:post_name")  # Slug
                post["post_type"] = get_text("wp:post_type")
                post["post_date"] = get_text("wp:post_date")
                # post['link'] = get_text('link')
                # post['status'] = get_text('wp:status')
                # post['post_parent'] = get_text('wp:post_parent')
                # post['menu_order'] = get_text('wp:menu_order')
                # Add more fields here if needed

                # Process content
                post["content"] = get_text("content:encoded")
                # Ensure content is always a string
                if post["content"] is None:
                    post["content"] = ""
                # Convert content to Markdown if requested
                if convert_to_markdown and post["content"]:
                    # Preprocess HTML to convert implicit paragraphs to explicit ones
                    para_html = html_paragraphize(post["content"])
                    preprocessed_html = wrap_inline_runs_in_paragraphs(para_html)
                    post["content"] = md(
                        preprocessed_html,
                        heading_style="ATX",
                        bullets="-",
                        convert=[
                            "b",
                            "i",
                            "em",
                            "strong",
                            "p",
                            "a",
                            "img",
                            "h1",
                            "h2",
                            "h3",
                            "h4",
                            "h5",
                            "h6",
                            "ul",
                            "ol",
                            "li",
                            "blockquote",
                            "code",
                            "pre",
                            "br",
                            "hr",
                        ],
                        autolinks=True,
                        default_title=True,
                        escape_asterisks=False,
                        escape_underscores=False,
                        keep_inline_images_in=["p", "li"],
                        newline_style="\n",
                        strip_links=False,
                        strip_images=False,
                        wrap=False,  # Disable line wrapping for more control
                    )
                    post["content"] = postprocess_markdown(post["content"])

                # Extract taxonomies
                post["taxonomies"] = {}
                for category in item.xpath("category"):
                    domain = category.get("domain")
                    nicename = category.get("nicename")
                    term_name = category.text

                    if domain and nicename is not None:
                        if domain not in post["taxonomies"]:
                            post["taxonomies"][domain] = []

                        post["taxonomies"][domain].append(
                            {"name": term_name, "slug": nicename}
                        )

                # Extract metadata and custom fields using wp:postmeta
                post["custom_fields"] = {}
                for postmeta in item.xpath("wp:postmeta", namespaces=NAMESPACES):
                    meta_key_elem = postmeta.find("wp:meta_key", NAMESPACES)
                    meta_value_elem = postmeta.find("wp:meta_value", NAMESPACES)

                    if (
                        meta_key_elem is not None
                        and meta_key_elem.text
                        and meta_value_elem is not None
                    ):
                        meta_key = meta_key_elem.text

                        # Skip excluded custom fields (support wildcards)
                        if excluded_custom_fields and any(
                            fnmatch.fnmatch(meta_key, pattern)
                            for pattern in excluded_custom_fields
                        ):
                            continue

                        meta_value_raw = meta_value_elem.text  # Can be None if empty

                        # Ensure meta_value_raw is a string
                        if meta_value_raw is not None:
                            if isinstance(meta_value_raw, bytes):
                                meta_value_raw = meta_value_raw.decode(
                                    "utf-8", errors="replace"
                                )
                            elif not isinstance(meta_value_raw, str):
                                meta_value_raw = str(meta_value_raw)

                        # --- Attempt PHP Deserialization ---
                        meta_value_processed = meta_value_raw

                        # Heuristic: Does it look like PHP serialized data?
                        if (
                            meta_value_raw
                            and isinstance(meta_value_raw, str)
                            and len(meta_value_raw) > 2
                            and meta_value_raw[0] in ("a", "s", "O", "i", "d", "b", "N")
                            and meta_value_raw[1] == ":"
                        ):

                            # Try to deserialize using phpserialize
                            deserialized_result = try_php_unserialize(meta_value_raw)

                            # Check the result from the unserialization
                            if (
                                deserialized_result is not None
                                and deserialized_result != meta_value_raw
                            ):
                                # Deserialization was successful and returned a valid value
                                meta_value_processed = deserialized_result
                            else:
                                # Deserialization failed or returned the same string
                                meta_value_processed = (
                                    meta_value_raw  # Keep raw string on failure
                                )

                        # Always convert dicts with sequential integer keys to lists for all custom fields
                        meta_value_processed = dict_to_list_if_sequential(
                            meta_value_processed
                        )

                        # Store the processed value
                        if meta_key in post["custom_fields"]:
                            current_value = post["custom_fields"][meta_key]
                            if not isinstance(current_value, list):
                                post["custom_fields"][meta_key] = [
                                    current_value,
                                    meta_value_processed,
                                ]
                            else:
                                post["custom_fields"][meta_key].append(
                                    meta_value_processed
                                )
                        else:
                            post["custom_fields"][meta_key] = meta_value_processed

                # Always collect attachments for gallery resolution
                if post["post_type"] == "attachment":
                    attachments[post["id"]] = post

                # Only add to posts_data if included_post_types is None or matches
                if (included_post_types is None) or (
                    post["post_type"] in included_post_types
                ):
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

        # Second pass: process gallery IDs and _thumbnail_id
        print("Procesando IDs de galería y miniaturas...")
        for post in posts_data:
            # Process galeria
            if "galeria" in post["custom_fields"]:
                gallery_data = post["custom_fields"]["galeria"]
                # Always convert dicts with sequential integer keys to lists
                gallery_data = dict_to_list_if_sequential(gallery_data)
                if not isinstance(gallery_data, (str, list)):
                    continue
                # Convert string to list if necessary
                if isinstance(gallery_data, str):
                    gallery_ids = [id.strip() for id in gallery_data.split(",")]
                else:
                    gallery_ids = gallery_data
                image_urls = []
                for attachment_id in gallery_ids:
                    # Find the attachment in our dictionary
                    attachment = attachments.get(str(attachment_id))
                    if (
                        attachment
                        and "_wp_attached_file" in attachment["custom_fields"]
                    ):
                        image_urls.append(
                            attachment["custom_fields"]["_wp_attached_file"]
                        )
                    else:
                        image_urls.append(
                            attachment_id
                        )  # Keep original ID if not found
                post["custom_fields"]["galeria"] = image_urls
            # Process _thumbnail_id
            if "_thumbnail_id" in post["custom_fields"]:
                thumb_id = post["custom_fields"]["_thumbnail_id"]
                # If it's a list, take the first element
                if isinstance(thumb_id, list) and thumb_id:
                    thumb_id = thumb_id[0]
                attachment = attachments.get(str(thumb_id))
                if attachment and "_wp_attached_file" in attachment["custom_fields"]:
                    post["custom_fields"]["thumbnail"] = attachment["custom_fields"][
                        "_wp_attached_file"
                    ]
                else:
                    post["custom_fields"]["thumbnail"] = thumb_id
                # Remove the original _thumbnail_id field
                del post["custom_fields"]["_thumbnail_id"]

    except FileNotFoundError:
        print(f"Error: El archivo XML no fue encontrado en {xml_filepath}")
        sys.exit(1)
    except etree.XMLSyntaxError as e:
        print(f"Error al parsear el archivo XML (lxml): {e}")
        print(
            "Asegúrate de que el archivo es un XML de exportación de WordPress válido y bien formado."
        )
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error inesperado durante el parseo: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Write to YAML file
    try:
        print(f"Escribiendo datos en {yaml_filepath}...")
        with open(yaml_filepath, "w", encoding="utf-8") as outfile:
            yaml.dump(
                posts_data,
                outfile,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        print(f"Archivo YAML guardado exitosamente en {yaml_filepath}.")
    except IOError as e:
        print(f"Error al escribir el archivo YAML: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Ocurrió un error inesperado al escribir el archivo YAML: {e}")
        sys.exit(1)
