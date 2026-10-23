"""Run the scanner on one URL and print the findings. No API or database needed.

Usage:  python try_scan.py https://www.gov.uk
"""
import json
import sys

from dotenv import load_dotenv

load_dotenv("../.env")

from scanner.scan import run_scan  # noqa: E402

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.gov.uk"
result = run_scan(url)

print("Pages crawled:")
for page in result["pages_crawled"]:
    print("  ", page)
print(f"\n{len(result['findings'])} findings:")
print(json.dumps(result["findings"], indent=2))
print(f"\nPrivacy policy text: {len(result['privacy_text'])} characters")
