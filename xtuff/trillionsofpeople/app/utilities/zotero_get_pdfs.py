import argparse
import json
import os

from pyzotero import zotero

zot = zotero.Zotero(
    os.environ["ZOTERO_LIBRARY_ID"],
    os.environ["ZOTERO_LIBRARY_TYPE"],
    os.environ["ZOTERO_API_KEY"],
)


# print(zot.collections())
def get_pdfs(output_dir, collection_id, tag):
    target_dir = os.path.join(output_dir, 'zotero', collection_id, tag)
    # Create the output directory
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print("Getting pdfs for tag: " + tag + " in collection: " + collection_id)
    key = collection_id
    items = [d for d in zot.everything(zot.collection_items(key, tag=tag))]
    print(len(items), "items found with tag", tag)
    with open(target_dir + "/items.json", "w") as f:
        json.dump(items, f)

    for item in items:

        # An item's attachments
        children = [c for c in zot.children(item['key'])]

        # Just get the PDFs
        pdfs = [c for c in children
                if c['data'].get('contentType') == 'application/pdf']

        # Handle when there are no attachments
        if not children:
            print('\nMISSING DOCUMENTS {}\n'.format(item['key']))
        # Handle when there are no PDF attachments
        elif not pdfs:
            print('\nNO PDFs {}\n'.format(item['key']))
        # Handle when there is more than one PDF attachment
        elif len(pdfs) != 1:
            print('\nTOO MANY PDFs {}\n'.format(item['key']))
        # Save the PDF to the category directory
        else:
            try:
                doc = pdfs[0]
                print(doc['data']['filename'])

            except Exception as e:
                print('\nERROR {}\n'.format(item['key']))
                print(e)
                continue
    return


if __name__ == "__main__":
    argparser = argparse.ArgumentParser(
        description="Get bibliography from Zotero collection"
    )

    argparser.add_argument("--collection_id", help="collection id", default="N3EXZ3VT")
    argparser.add_argument(
        "--style", help="style", default="chicago-annotated-bibliography"
    )
    argparser.add_argument("--tag", help="one tag", default="test5gw")
    argparser.add_argument("--output_dir", help="output directory", default="output")
    args = argparser.parse_args()
    collection_id = args.collection_id
    style = args.style
    tag = args.tag
    output_dir = args.output_dir

    # Get the PDFs

    doc = get_pdfs(output_dir, collection_id, tag)
    print(doc)
