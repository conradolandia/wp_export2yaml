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

You can use the CLI entry point after installing dependencies, or run the module directly:

```bash
# Run as a CLI tool (after installing dependencies)
wp-converter wp_export.xml wp_export.yaml [options]

# Or run as a module
python -m wp_converter wp_export.xml wp_export.yaml [options]

# Or with uv
uv run -m wp_converter wp_export.xml wp_export.yaml [options]
```
If you installed the package in editable mode (`pip install -e .`), the `wp-converter` command will be available globally in your environment.

## Usage

### 1. Export your WordPress site as XML (WXR)

- In your WordPress admin, go to **Tools > Export** and select **All Content**. Alternatively, use [WP-CLI](https://wp-cli.org/) if you have terminal access to your WP server, which can be significantly faster for large sites.

### 2. Run the converter

Basic usage:

```bash
wp-converter wp_export.xml wp_export.yaml
```

With options:

```bash
wp-converter wp_export.xml wp_export.yaml \
  --convert-to-markdown \
  --post-types proyectos \
  --exclude-custom-fields _edit_last _fechas _galeria _g_feedback_shortcode*
```

Or as a module:

```bash
python -m wp_converter wp_export.xml wp_export.yaml --convert-to-markdown --post-types proyectos
```

Or with uv:

```bash
uv run -m wp_converter wp_export.xml wp_export.yaml --convert-to-markdown --post-types proyectos
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

Command line: `wp-converter wp_source.xml wp_destination.yaml --convert-to-markdown --post-types proyectos --exclude-custom-fields _edit_last _fechas _galeria _wp_page_template _wpcom_is_markdown wp_featherlight_disable _g_feedback_shortcode* _wp_old_slug`

Source XML (fragment):

```xml
<item>
	<title><![CDATA[Project Title]]></title>
	<link>https://example.com/projects/project-title/</link>
	<pubDate>Thu, 29 Dec 2022 03:21:06 +0000</pubDate>
	<dc:creator><![CDATA[author]]></dc:creator>
	<guid isPermaLink="false">https://example.com/?post_type=proyectos&#038;p=797</guid>
	<description></description>
	<content:encoded><![CDATA[This is an example project dedicated to illustrating the conversion process. It aims to showcase how WordPress content, with its specific structure and formatting, can be transformed into clean and readable YAML. This content might describe the project's goals, technologies used, or key team members. Visit the project website at <a href="https://example.com/" target="_blank" rel="noopener">https://example.com/</a>.]]></content:encoded>
	<excerpt:encoded><![CDATA[]]></excerpt:encoded>
	<wp:post_id>797</wp:post_id>
	<wp:post_date><![CDATA[2022-12-28 22:21:06]]></wp:post_date>
	<wp:post_date_gmt><![CDATA[2022-12-29 03:21:06]]></wp:post_date_gmt>
	<wp:post_modified><![CDATA[2022-12-29 22:52:03]]></wp:post_modified>
	<wp:post_modified_gmt><![CDATA[2022-12-30 03:52:03]]></wp:post_modified_gmt>
	<wp:comment_status><![CDATA[closed]]></wp:comment_status>
	<wp:ping_status><![CDATA[closed]]></wp:ping_status>
	<wp:post_name><![CDATA[project-title]]></wp:post_name>
	<wp:status><![CDATA[publish]]></wp:status>
	<wp:post_parent>0</wp:post_parent>
	<wp:menu_order>0</wp:menu_order>
	<wp:post_type><![CDATA[proyectos]]></wp:post_type>
	<wp:post_password><![CDATA[]]></wp:post_password>
	<wp:is_sticky>0</wp:is_sticky>
	<category domain="tipos" nicename="front-end"><![CDATA[Front end]]></category>
	<category domain="clientes" nicename="client-org"><![CDATA[Client Organization]]></category>
	<category domain="tipos" nicename="wordpress"><![CDATA[WordPress]]></category>
	<wp:postmeta>
		<wp:meta_key><![CDATA[_edit_last]]></wp:meta_key>
		<wp:meta_value><![CDATA[1]]></wp:meta_value>
	</wp:postmeta>
	<wp:postmeta>
		<wp:meta_key><![CDATA[_thumbnail_id]]></wp:meta_key>
		<wp:meta_value><![CDATA[798]]></wp:meta_value>
	</wp:postmeta>
	<wp:postmeta>
		<wp:meta_key><![CDATA[fechas]]></wp:meta_key>
		<wp:meta_value><![CDATA[2019]]></wp:meta_value>
	</wp:postmeta>
	<wp:postmeta>
		<wp:meta_key><![CDATA[_fechas]]></wp:meta_key>
		<wp:meta_value><![CDATA[field_639d30b2540e1]]></wp:meta_value>
	</wp:postmeta>
	<wp:postmeta>
		<wp:meta_key><![CDATA[galeria]]></wp:meta_key>
		<wp:meta_value><![CDATA[a:4:{i:0;s:3:"799";i:1;s:3:"800";i:2;s:3:"801";i:3;s:3:"802";}]]></wp:meta_value>
	</wp:postmeta>
	<wp:postmeta>
		<wp:meta_key><![CDATA[_galeria]]></wp:meta_key>
		<wp:meta_value><![CDATA[field_639c3bff28f62]]></wp:meta_value>
	</wp:postmeta>
</item>
```

Result YAML (fragment):

```yaml
- id: '797'
  title: Project Title
  slug: project-title
  post_type: proyectos
  post_date: '2022-12-28 22:21:06'
  content: This is an example project dedicated to illustrating the conversion process.
    It aims to showcase how WordPress content, with its specific structure and formatting,
    can be transformed into clean and readable YAML. This content might describe
    the project's goals, technologies used, or key team members. Visit the project
    website at [https://example.com/](https://example.com/ "https://example.com/").
  taxonomies:
    tipos:
    - name: Front end
      slug: front-end
    - name: WordPress
      slug: wordpress
    clientes:
    - name: Client Organization
      slug: client-org
  custom_fields:
    fechas: '2019'
    galeria:
    - 2022/12/image1.png
    - 2022/12/image2.png
    - 2022/12/image3.png
    - 2022/12/image4.png
    thumbnail: 2022/12/featured-image.jpg
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

## Running Tests

To run the test suite, use:

```bash
PYTHONPATH=. pytest tests
```

## Contributing

- Source code is now in the `wp_converter/` package directory.
- CLI logic is in `wp_converter/__main__.py`.
- Tests are in the `tests/` directory.

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
