# WordPress XML to YAML Converter

> **WARNING:** Very early alpha, created to satisfy a custom requirement. You are welcome to fork it and modify it to your needs if you find it useful, but I provide no guarantees of any kind. PRs are welcome if you ae into that sort of stuff. Issues will probably be ignored until I have time.

This project provides a robust Python tool to convert WordPress WXR (XML export) files into clean, readable YAML files. It is especially useful for migrating WordPress content to static site generators or custom CMSs, and supports advanced features like PHP serialized field decoding, HTML-to-Markdown conversion, and gallery attachment resolution.

## Features
- **Converts WordPress XML (WXR) exports to YAML**
- **Decodes PHP serialized custom fields** using pure Python (`phpserialize`)
- **Converts HTML content to Markdown** (optional, via `markdownify`)
- **Robust paragraph and inline formatting**: Handles both explicit and implicit paragraphs, and keeps inline elements inlined (like links and bold text)
- **Filters by post type** (e.g., only export `proyectos`)
- **Excludes specific custom fields**
- **Resolves gallery IDs to file paths** for attachments (currently only for a custom post type `proyectos` with a custom field `galeria`, which is my current custom requirement. You can adapt it to use attachments, for example)
- **Outputs all multiline strings as YAML block scalars** for readability
- **Handles large XML files efficiently** with low memory usage

## Requirements
- [uv](https://github.com/astral-sh/uv)
- Python 3.8+
- The following Python packages:
  - lxml
  - PyYAML
  - markdownify
  - beautifulsoup4
  - phpserialize

> **Note:** PHP is **not required**. All unserialization is handled natively in Python.

The `main.py` entry point is compatible with [uv](https://github.com/astral-sh/uv) out of the box, so you can run it directly with uv without installing dependencies first:
```bash
uv run main.py 
```

## Usage

### 1. Export your WordPress site as XML (WXR)
- In your WordPress admin, go to **Tools > Export** and export **All Content**. You can also use [WP-CLI](https://wp-cli.org/) if you have terminal access to your WP server; this is faster for large sites.

### 2. Run the converter

Basic usage:
```bash
python main.py wp_export.xml wp_export.yaml
```

With options:
```bash
python main.py wp_export.xml wp_export.yaml \
  --convert-to-markdown \
  --post-types proyectos \
  --exclude-custom-fields _edit_last _fechas _galeria _g_feedback_shortcode*
```

Or with `uv`:
```bash
uv run main.py wp_export.xml wp_export.yaml --convert-to-markdown --post-types proyectos
```

#### Command-line options
- `--convert-to-markdown` : Convert HTML content fields to Markdown
- `--post-types` : Space-separated list of post types to include (e.g. `proyectos post page`)
- `--exclude-custom-fields` : Space-separated list of custom fields to exclude from output. **Supports wildcards** (e.g. `_g_feedback_shortcode*` will exclude all fields starting with that prefix)

## Output
- The resulting YAML file will:
  - Contain only the selected post types
  - Have all multiline strings (like `content`) as YAML block scalars (`|` style)
  - Replace gallery IDs with their corresponding file paths (if available)
  - Decode PHP serialized custom fields where possible
  - Preserve paragraphs and inline formatting in Markdown content

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
    
    Here is a [link](https://example.com) and some **bold text** in the same paragraph.
    
    Another paragraph follows.
  custom_fields:
    galeria:
      - 2023/01/image1.jpg
      - 2023/01/image2.jpg
```

#### Optional: add, remove or rename fields

If you want to rename fields (for example, change `post_type` to `type`), edit `wp_export2yaml.py`, and just change the field name:
```python
post['type'] = get_text('wp:post_type')
```

You can also add or comment out other fields in a similar way.

## Advanced Formatting and Robustness
- The converter now detects both explicit (`<p>`) and implicit (newlines, multiple `<br>`) paragraphs in WordPress HTML content.
- Inline elements (like `<a>`, `<strong>`, `<em>`) are kept inline, not split into their own paragraphs.
- The Markdown output is post-processed to ensure that block elements (headings, lists, etc.) start new paragraphs, and that paragraphs are separated by blank lines.
- This ensures that the YAML output is as close as possible to the original WordPress content structure, but in a clean, Markdown-friendly format.

## Troubleshooting
- **BeautifulSoup warnings** are suppressed by default.
- If you encounter a deserialization error, ensure your PHP serialized data is valid. The script uses `phpserialize` for all unserialization.
- For large XML files, the script uses `lxml.iterparse` for efficient, low-memory parsing.
- If you notice paragraphs are not preserved as expected, check your original WordPress HTML for implicit paragraphs (newlines or `<br>` tags). The converter now handles these, but edge cases may still exist. If you find one, please open an issue or PR!
- If you want to further customize the Markdown or YAML output, you can edit the `wrap_inline_runs_in_paragraphs`, `html_paragraphize`, or `postprocess_markdown` functions in `wp_export2yaml.py`.

## License
MIT License

## Author
[Andrés Conrado Montoya Acosta](https://sesentaycuatro.com) (@conradolandia)
