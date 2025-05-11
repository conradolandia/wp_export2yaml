# WordPress XML to YAML Converter

> **WARNING:** This is an early alpha version, created to satisfy a specific requirement. Feel free to fork it and adapt it to your needs. I offer no guarantees, but pull requests are welcome. While I may not be able to address issues immediately, I will review them when time permits.

This project provides a robust Python tool for converting WordPress WXR (XML export) files into clean, readable YAML files. It's especially useful for migrating WordPress content to static site generators or custom CMSs. Features include PHP serialized field decoding, HTML-to-Markdown conversion, and gallery attachment resolution.

## Features

- **Converts WordPress XML (WXR) exports to YAML.**
- **Decodes PHP serialized custom fields** using pure Python (`phpserialize`).  **No PHP required!**
- **Converts HTML content to Markdown** (optional, via `markdownify`).
- **Robust paragraph and inline formatting:** Handles both explicit and implicit paragraphs, preserving inline elements like links and bold text.
- **Filters by post type** (e.g., only export `proyectos`).
- **Excludes specific custom fields.** Supports wildcards (e.g. `_g_feedback_shortcode*`).
- **Resolves gallery IDs to file paths** for attachments (currently implemented for a custom post type `proyectos` with a custom field `galeria`. Adaptable for other attachment scenarios).
- **Outputs all multiline strings as YAML block scalars** for enhanced readability.
- **Handles large XML files efficiently** with low memory usage.

## Requirements

- [uv](https://github.com/astral-sh/uv)
- Python 3.13+
- The following Python packages:
  - lxml
  - PyYAML
  - markdownify
  - beautifulsoup4
  - phpserialize

> **Note:** PHP is **not required.** All unserialization is handled natively in Python.

The `main.py` entry point is compatible with [uv](https://github.com/astral-sh/uv) out of the box, allowing you to run it directly without installing dependencies first:

```bash
uv run main.py
```

## Usage

### 1. Export your WordPress site as XML (WXR)

- In your WordPress admin, go to **Tools > Export** and select **All Content**. Alternatively, use [WP-CLI](https://wp-cli.org/) if you have terminal access to your WP server, which can be significantly faster for large sites.

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

- `--convert-to-markdown`: Convert HTML content fields to Markdown.
- `--post-types`: Space-separated list of post types to include (e.g., `proyectos post page`).
- `--exclude-custom-fields`: Space-separated list of custom fields to exclude from output. Supports wildcards (e.g., `_g_feedback_shortcode*` will exclude all fields starting with that prefix).

## Output

- The resulting YAML file will:
  - Contain only the selected post types.
  - Represent all multiline strings (like `content`) as YAML block scalars (`|` style).
  - Replace gallery IDs with their corresponding file paths (if configured and available).
  - Decode PHP serialized custom fields where possible.
  - Preserve paragraphs and inline formatting in Markdown content.

## Example

```yaml
- title: Example Project
  slug: example-project
  post_type: proyectos
  post_date: "2023-01-01 12:00:00"
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

#### Optional: Add, remove, or rename fields

To rename fields (e.g., change `post_type` to `type`), edit `wp_export2yaml.py`:

```python
post['type'] = get_text('wp:post_type')
```

You can add or comment out other fields similarly.

## Advanced Formatting and Robustness

- The converter detects both explicit (`<p>`) and implicit (newlines, multiple `<br>`) paragraphs in WordPress HTML content.
- Inline elements (like `<a>`, `<strong>`, `<em>`) are preserved inline.
- The Markdown output is post-processed to ensure block elements (headings, lists, etc.) start new paragraphs and that paragraphs are separated by blank lines.
- This ensures the YAML output closely reflects the original WordPress content structure in a clean, Markdown-friendly format.

## Troubleshooting

- **BeautifulSoup warnings** are suppressed by default.
- If you encounter a deserialization error, verify the validity of your PHP serialized data. The script uses `phpserialize` for unserialization.
- For large XML files, the script leverages `lxml.iterparse` for efficient, low-memory parsing.
- If paragraphs aren't preserved as expected, examine the original WordPress HTML for implicit paragraphs (newlines or `<br>` tags). While the converter handles these, edge cases may exist. Please submit a pull request if you find one!
- For further customization of the Markdown or YAML output, modify the `wrap_inline_runs_in_paragraphs`, `html_paragraphize`, or `postprocess_markdown` functions in `wp_export2yaml.py`.

## License

MIT License

## Author

[Andrés Conrado Montoya Acosta](https://sesentaycuatro.com) ([@conradolandia](https://github.com/conradolandia))
