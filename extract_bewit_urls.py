"""
Extract BEWIT product URLs from interactive PDF files.
Uses pypdf annotation extraction to get all hyperlinks.
"""

import json
import sys
from pathlib import Path
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject


def extract_links_from_pdf(pdf_path: str, pdf_label: str) -> list[dict]:
    """Extract all hyperlinks from a PDF, returning list of {page, url, text} dicts."""
    results = []
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)
    print(f"\n[{pdf_label}] {num_pages} pages found in: {pdf_path}")

    for page_num, page in enumerate(reader.pages, start=1):
        annotations = page.annotations
        if annotations is None:
            continue

        for annot in annotations:
            annot_obj = annot.get_object()
            if not isinstance(annot_obj, DictionaryObject):
                continue

            subtype = annot_obj.get("/Subtype")
            if subtype != "/Link":
                continue

            # Try to get URL from /A (Action) dictionary
            url = None
            action = annot_obj.get("/A")
            if action:
                action_obj = action.get_object() if hasattr(action, "get_object") else action
                if isinstance(action_obj, DictionaryObject):
                    action_type = action_obj.get("/S")
                    if action_type == "/URI":
                        uri = action_obj.get("/URI")
                        if uri:
                            url = str(uri)

            if not url:
                continue

            # Filter for bewit.love/produkt URLs
            if "bewit.love/produkt" not in url:
                continue

            # Try to get link text from /Contents or via rect area (optional)
            link_text = ""
            contents = annot_obj.get("/Contents")
            if contents:
                link_text = str(contents)

            results.append({
                "source": pdf_label,
                "page": page_num,
                "url": url,
                "text": link_text
            })

    return results


def main():
    pdf1_path = r"C:\Users\x2\Desktop\xx\0_Jednodruhové EO_interaktivní.pdf"
    pdf2_path = r"C:\Users\x2\Desktop\xx\0_Směsi EO_interaktivni.pdf"
    output_path = r"C:\Claude\projekty\www\esenci.cz\bewit-urls.json"

    all_results = []

    # Extract from PDF 1
    try:
        results1 = extract_links_from_pdf(pdf1_path, "single_oils")
        print(f"  Found {len(results1)} bewit.love/produkt links")
        unique1 = len(set(r["url"] for r in results1))
        print(f"  Unique URLs: {unique1}")
        all_results.extend(results1)
    except Exception as e:
        print(f"ERROR processing PDF 1: {e}", file=sys.stderr)

    # Extract from PDF 2
    try:
        results2 = extract_links_from_pdf(pdf2_path, "blends")
        print(f"  Found {len(results2)} bewit.love/produkt links")
        unique2 = len(set(r["url"] for r in results2))
        print(f"  Unique URLs: {unique2}")
        all_results.extend(results2)
    except Exception as e:
        print(f"ERROR processing PDF 2: {e}", file=sys.stderr)

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save full results (with source field)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # Also save per-PDF files for easier consumption
    results1_only = [r for r in all_results if r["source"] == "single_oils"]
    results2_only = [r for r in all_results if r["source"] == "blends"]

    output1 = output_file.parent / "bewit-urls-single-oils.json"
    output2 = output_file.parent / "bewit-urls-blends.json"

    with open(output1, "w", encoding="utf-8") as f:
        json.dump(results1_only, f, ensure_ascii=False, indent=2)

    with open(output2, "w", encoding="utf-8") as f:
        json.dump(results2_only, f, ensure_ascii=False, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"PDF 1 (single oils): {len(results1_only)} total links, {len(set(r['url'] for r in results1_only))} unique URLs")
    print(f"PDF 2 (blends):      {len(results2_only)} total links, {len(set(r['url'] for r in results2_only))} unique URLs")
    print(f"Combined total:      {len(all_results)} links saved to {output_path}")

    # Show sample URLs
    if results1_only:
        print(f"\nSample from PDF 1:")
        for r in results1_only[:3]:
            print(f"  Page {r['page']}: {r['url']}")
    if results2_only:
        print(f"\nSample from PDF 2:")
        for r in results2_only[:3]:
            print(f"  Page {r['page']}: {r['url']}")


if __name__ == "__main__":
    main()
