# WordPress XML to YAML Converter

This project provides a robust Python tool to convert WordPress WXR (XML export) files into clean, readable YAML files. It is especially useful for migrating WordPress content to static site generators or custom CMSs, and supports advanced features like PHP serialized field decoding, HTML-to-Markdown conversion, and gallery attachment resolution.

## Features
- **Converts WordPress XML (WXR) exports to YAML**
- **Decodes PHP serialized custom fields** using an external PHP script
- **Converts HTML content to Markdown** (optional, via `markdownify`)
- **Filters by post type** (e.g., only export `proyectos`)
- **Excludes specific custom fields**
- **Resolves gallery IDs to file paths** for attachments
- **Outputs all multiline strings as YAML block scalars** for readability
- **Handles large XML files efficiently** with low memory usage

## Requirements
- Python 3.8+
- PHP (for unserializing PHP fields. I tried to do with with Python alone, but after so much trial and error this was the most realiable option)
- The following Python packages:
  - lxml
  - PyYAML
  - markdownify
  - beautifulsoup4

The `main.py` entry point is compatible with [uv](https://github.com/astral-sh/uv) out of the box, so you can run it directly with uv without installing dependencies first:
```bash
uv run main.py 
```

Or, you can install dependencies with [uv](https://github.com/astral-sh/uv) (or pip):
```bash
uv pip install -r requirements.txt
```

## Usage

### 1. Export your WordPress site as XML (WXR)
- In your WordPress admin, go to **Tools > Export** and export **All Content**. You can also use [WP-CLI](https://wp-cli.org/) if you have terminal access to your WP server; this is faster for large sites.

### 2. Prepare the PHP unserialize script
- Ensure you have the `deserialize.php` script in your project root. This script is used to decode PHP serialized fields.

### 3. Run the converter

Basic usage:
```bash
python main.py wp_export.xml wp_export.yaml deserialize.php
```

With options:
```bash
python main.py wp_export.xml wp_export.yaml deserialize.php \
  --convert-to-markdown \
  --post-types proyectos \
  --exclude-custom-fields _edit_last _fechas _galeria
```

Or with `uv`:
```bash
uv run main.py wp_export.xml wp_export.yaml deserialize.php --convert-to-markdown --post-types proyectos
```

#### Command-line options
- `--convert-to-markdown` : Convert HTML content fields to Markdown
- `--post-types` : Space-separated list of post types to include (e.g. `proyectos post page`)
- `--exclude-custom-fields` : Space-separated list of custom fields to exclude from output

## Output
- The resulting YAML file will:
  - Contain only the selected post types
  - Have all multiline strings (like `content`) as YAML block scalars (`|` style)
  - Replace gallery IDs with their corresponding file paths (if available)
  - Decode PHP serialized custom fields where possible

## Example
```yaml
- title: Example Project
  slug: example-project
  post_type: proyectos
  post_date: '2023-01-01 12:00:00'
  content: |
    This is a **Markdown** block.
    
    - List item 1
    - List item 2
  custom_fields:
    galeria:
      - 2023/01/image1.jpg
      - 2023/01/image2.jpg
```

#### Optional: add, remove or rename fields

If you want to rename fields (for example, change `post_type` to `type`), edit `wp_export2yaml.py` as follows:
```python
# Around line 210...
post['type'] = get_text('wp:post_type')
```

You can also add or comment out other fields in a similar way.

## Troubleshooting
- BeautifulSoup warnings are suppressed by default.
- If you encounter a PHP or unserialization error, ensure that `php` is installed and that the `deserialize.php` script is present and executable.
- For large XML files, the script uses `lxml.iterparse` for efficient, low-memory parsing.

## License
MIT License

## Author
Andrés Conrado Montoya Acosta
