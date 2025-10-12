COVER:

Must create UPC-A US style book barcode and place it in the same location as presently with adequate safety spaces.

INTERIOR

- Dotgrid image must appear lower on page leaving at least 0.5in more between the bottom of the header and the beginning of the footer
- the ISBN in the copyright page must be the properly hyphenated full 13-digit with check digit
- for xynapse_traces titles, there is a 38 character hard limit for subtitles.  If the subtitle is longer than that, it must be REPLACED with a new subtitle created with an LLM call using nimble-llm-caller.

METADATA
- Verify that current calculated spine width is correct using the logic in metadata2lsicoverspecs.py to look up in resources/SpineWidthLookup.xlsx.  Page type for these books is "Standard perfect 70".  Provide this spine width to metadata and to cover creator.