Task: create and use database of unique ISBNs owned by each publisher.
- Each publisher owns one or more blocks of iSBNs.
- Accept as "sources of truth" spreadsheet files downloaded from Bowker that list all the ISBNs that a publisher owns as well as all the ones that have been publicly assigned.
- The publisher's available ISBNs are all those that have never been publicly assigned.
- When a publisher uses LSI distribution, an ISBN is required. The system should pull the next available ISBN from the database, mark it as privately assigned, and use it in the book pipeline.
- The privately assigned ISBN becomes publicly assigned whenever it is uploaded to LSI and can never again be used by the publisher for any other purpose.
- Privately assigned ISBNs can be released by the publisher at any time before publication.

Task: create and use minimal LSISeriesMetadata class that manages series names and contents for LSI metadata.
- LSI Series metadata is three fields, name, series unique id, and number in series.
- Other distributors such as KDP have more elaborate metadata with multiple descriptive fields and icons.
- For our immediate purposes, we only need the LSI Series Metadata to:
  - keep track of all unique series names
  - keep track of all titles belonging to that series and their sequence number in the series
- We need methods that:
    - validate series names for consistency
    - allow for CRUD of titles from series. No renumbering.
- The user should be able to specify series name when starting the Book Pipeline and have the system automatically assign a series number.
- The minimum initial requirement is that each publisher may have any number of series.
- Different publishers may have series with the same name, but they are different series with different ids.
- Multiple publishers may contribute to the same series.
- A series is either a single-publisher series or a multi.  Default is single. 

Task: improve field completion for listed fields.
- Series and Series #:
   - Imprint has list of registered series and their members.
   - In UI, user can select from registered series, or add a new one.
   - In either case, title is assigned a series ID #.
   - Delete the llm_completion option for identifying series, we are not using that at present.

- Annotation/Summary:

    - Constructed in simple HTML for LSI catalog display. Max 4000 characters. No outbound links.
    - First paragraph: dramatic hook in bold italic.
    - Then back_cover_text.
    - Then concatenate new paragraphedlist of strings from a shared dictionary in configs/publisher, e.g. "nimble_history": "Nimble Books was founded in 2006."

- BISAC Category, BISAC Category 2, BISAC Category 3: 
    - each field contains one category/code pair that is the result of llm_competion call to suggest_bisac_codes.
    - the user may specify a BISAC category override that automatically assigns a given code based on user information. This is job-specific. For example, all jobs to create pilsa books might be assigned Journalling:Self-Help for category 3.

- Thema Subject 1, ... 2 and  ...3 and Regional Subjects: 
    - assign based on results of suggest_thema_codes

- Contributor info fields:
    - assign based on results of extract_lsi_contributor_info

- Illustrations and Illustration Note:
    - assign based on results of gemini_get_basic_info for Illustrations

- Table of Contents:
    - assign based on results of create_simple_toc

- Ignore (leave cells blank but retain column headings):
    - Reserved*
    - SIBI*
    - Stamped*
    - LSI Flexfield*
    - Review Quotes
    
