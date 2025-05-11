# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "lxml>=4.9.0",
#     "markdownify>=0.11.6",
#     "phpserialize",
#     "pyyaml>=6.0",
# ]
# ///
import argparse
from wp_export2yaml import parse_wxr2yaml

def main():
    parser = argparse.ArgumentParser(description='Convert WordPress WXR export to YAML format')
    parser.add_argument('xml_file', help='Path to WordPress XML export file (.wxr)')
    parser.add_argument('yaml_file', help='Path where the YAML output file will be saved')
    parser.add_argument('--post-types', nargs='+', help='List of post types to include (space-separated)')
    parser.add_argument('--exclude-custom-fields', nargs='+', help='List of custom fields to exclude (space-separated)')
    parser.add_argument('--convert-to-markdown', action='store_true', help='Convert HTML content to Markdown')
    
    args = parser.parse_args()
    
    parse_wxr2yaml(
        args.xml_file,
        args.yaml_file,
        included_post_types=args.post_types,
        excluded_custom_fields=args.exclude_custom_fields,
        convert_to_markdown=args.convert_to_markdown
    )


if __name__ == "__main__":
    main()
