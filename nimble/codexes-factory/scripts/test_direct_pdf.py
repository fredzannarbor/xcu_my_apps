#!/usr/bin/env python3
"""
Test direct PDF URL construction based on the pattern mentioned.
"""

import os
import base64
import requests

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    """Test direct PDF URL construction."""

    api_key = os.getenv("ZYTE_API_KEY")
    if not api_key:
        print("Error: ZYTE_API_KEY environment variable not set")
        return

    # Test the PDF URL pattern you mentioned
    doc_id = "0000119706"
    pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"

    print(f"Testing direct PDF URL: {pdf_url}")

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{api_key}:'.encode()).decode()}",
        "Content-Type": "application/json"
    }
    data = {
        "url": pdf_url,
        "httpResponseBody": True,
        "httpResponseHeaders": True
    }

    response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=60)

    if response.status_code == 200:
        result = response.json()

        # Check HTTP status
        status_code = result.get('httpResponseStatusCode')
        print(f"HTTP Status: {status_code}")

        # Check headers
        headers_info = result.get('httpResponseHeaders', {})
        content_type = None
        content_length = None

        for header in headers_info:
            if header.get('name', '').lower() == 'content-type':
                content_type = header.get('value')
            elif header.get('name', '').lower() == 'content-length':
                content_length = header.get('value')

        print(f"Content-Type: {content_type}")
        print(f"Content-Length: {content_length}")

        if result.get('httpResponseBody'):
            # Decode and check if it's a valid PDF
            try:
                pdf_content = base64.b64decode(result['httpResponseBody'])
                print(f"PDF size: {len(pdf_content)} bytes")

                # Check PDF magic bytes
                if pdf_content.startswith(b'%PDF'):
                    print("✅ Valid PDF file!")

                    # Try to count pages
                    try:
                        import fitz
                        with fitz.open(stream=pdf_content) as doc:
                            page_count = doc.page_count
                            print(f"📄 Page count: {page_count}")
                    except ImportError:
                        print("PyMuPDF not available - cannot count pages")
                    except Exception as e:
                        print(f"Error counting pages: {e}")

                else:
                    print("❌ Not a valid PDF file")
                    print(f"First 100 bytes: {pdf_content[:100]}")

            except Exception as e:
                print(f"Error decoding PDF: {e}")
        else:
            print("No content received")

    else:
        print(f"Failed to fetch: {response.status_code}")
        if response.content:
            print(f"Error: {response.text}")

    # Test a few more document IDs from your example
    other_doc_ids = ["0000258356", "0000272975", "0000258552"]

    for doc_id in other_doc_ids:
        pdf_url = f"https://www.cia.gov/readingroom/docs/DOC_{doc_id}.pdf"
        print(f"\nTesting: {pdf_url}")

        data = {
            "url": pdf_url,
            "httpResponseHeaders": True
        }

        response = requests.post('https://api.zyte.com/v1/extract', headers=headers, json=data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            status_code = result.get('httpResponseStatusCode')
            print(f"  HTTP Status: {status_code}")

            if status_code == 200:
                print("  ✅ PDF exists!")
            elif status_code == 404:
                print("  ❌ PDF not found")
            else:
                print(f"  ⚠️  Unexpected status: {status_code}")
        else:
            print(f"  Failed to test: {response.status_code}")

if __name__ == "__main__":
    main()