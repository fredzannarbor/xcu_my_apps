import json
import argparse
import os
import sys

# Add src to path to allow importing codexes modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from codexes.core import llm_caller

def generate_text(system_prompt, user_prompt, prompt_key, model_name, max_tokens=None):
    """
    This function takes a system and user prompt and returns the generated text
    using codexes.core.llm_caller.
    """
    # Add universal requirements to the system prompt
    citation_requirement = "\n\nIMPORTANT: Every substantive factual assertion or policy recommendation must be accompanied by a real, grounded citation."
    style_guideline = "\n\nWRITING STYLE: Use clear and concise language. Avoid long run-on sentences. Ensure bulleted list items and reference list entries are presented on separate lines."
    output_format_guideline = "\n\nOUTPUT FORMAT: Do not include any introductory or concluding pleasantries. The output should begin directly with the requested content and end immediately after the content is complete."
    
    if system_prompt:
        system_prompt += citation_requirement
        system_prompt += style_guideline
        system_prompt += output_format_guideline
    else:
        system_prompt = citation_requirement + style_guideline + output_format_guideline

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    prompt_config = {
        "messages": messages,
        "params": {}
    }
    if max_tokens:
        prompt_config["params"]["max_tokens"] = max_tokens

    print(f"--- Calling LLM ({model_name}) for {prompt_key} ---")

    response = llm_caller.call_model_with_prompt(
        model_name=model_name,
        prompt_config=prompt_config,
        prompt_name=prompt_key
    )

    parsed_content = response.get("parsed_content")
    if isinstance(parsed_content, dict) and "error" in parsed_content:
        return response.get("raw_content", f"Error generating content: {parsed_content['error']}")
    elif isinstance(parsed_content, dict):
        return json.dumps(parsed_content, indent=2)

    return parsed_content if parsed_content is not None else ""

def verify_chapter(chapter_content, model_name, prompt_key):
    """
    Calls the LLM to verify citations in the generated chapter and returns a verification notes section.
    """
    print(f"--- Verifying citations for {prompt_key} using {model_name} ---")

    system_prompt = "You are a meticulous fact-checker and research assistant. Your task is to verify the citations in the provided text. For each citation, you must confirm that it corresponds to a real publication. You will then produce a 'Verification Notes' section detailing your findings."
    
    user_prompt = f"""Please verify the citations in the following chapter text.

CHAPTER TEXT:
---
{chapter_content}
---

Your task is to:
1. For each citation found in the text, attempt to verify that it points to a real-world publication (e.g., a journal article, report, book).
2. Create a "Verification Notes" section.
3. In this section, for each citation, provide a note on whether you could verify it.
4. For verified citations, include details that would allow a human to find the source (e.g., a DOI link, a full bibliographic entry, or a stable URL).
5. For unverified citations, state that you could not find a corresponding publication.
6. Present this as a markdown-formatted section under the heading "### Verification Notes".""" # H3 for subsection

    verification_notes = generate_text(system_prompt, user_prompt, f"{prompt_key}_verification", model_name)
    return verification_notes

def assemble_report(prompts_data, output_dir, args):
    """
    Assembles the full report from generated markdown files.
    """
    print("--- Assembling Full Report ---")

    prompt_sections = [
        "reprompts", "chapters", "regional_chapters", "thematic_chapters", "annexes", "technical_guidelines"
    ]
    
    ordered_keys = []
    for section_name in prompt_sections:
        if section_name in prompts_data and isinstance(prompts_data[section_name], dict):
            ordered_keys.extend(prompts_data[section_name].keys())

    full_content = []
    for key in ordered_keys:
        md_path = os.path.join(output_dir, f"{key}_output.md")
        if os.path.exists(md_path):
            print(f"Appending {key}...")
            with open(md_path, 'r') as f:
                full_content.append(f.read())
        else:
            print(f"Warning: Missing chapter file: {md_path}")

    # Join with page breaks
    full_report_md_path = os.path.join(output_dir, "full_report.md")
    with open(full_report_md_path, 'w') as f:
        f.write("\n\n\\newpage\n\n".join(full_content))
    print(f"Full report assembled at: {full_report_md_path}")

    # --- Create Draft Header ---
    draft_header_line_1 = "DRAFT"
    prompt_info = f"PROMPT: {os.path.basename(args.system_prompt_override)}" if args.system_prompt_override else "PROMPT: default"
    model_name = args.model
    if args.lite:
        model_name = "gemini/gemini-1.5-flash-latest"
    model_info = f"MODEL: {model_name}"
    draft_header_line_2 = f"{prompt_info} - {model_info}"

    # --- Explanation Text ---
    explanation_section_latex = ""
    if args.lite:
        explanation_text = f"The system was instructed to write the report from the same perspective as the AR7 authors. This is a \"lite\" or illustrative version created using a less expensive, faster model with a maximum of {args.word_limit} words per chapter."
        explanation_section_latex = r"""\begin{center}
\parbox{0.8\textwidth}{\Large
\textbf{Explanation}

$explanation_text$
}
\end{center}
\vspace{1cm}
""".replace("$explanation_text$", explanation_text)

    # Create the complete and correct LaTeX template
    latex_template = r"""\documentclass[a4paper, 10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[english]{babel}
\usepackage{geometry}
\geometry{a4paper, top=2.5cm, bottom=2.5cm, textwidth=6.925in, columnsep=0.175in}
\usepackage{cuted} % For full-width tables in two-column layout
\usepackage{multicol}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{url} % For correctly typesetting URLs
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage{calc}
\usepackage{fontspec} % Use Fira Sans font
\setmainfont{Fira Sans}
\usepackage{listings} % Explicitly load listings for \lstinline and \passthrough

\usepackage{letltxmacro} % For redefining \includegraphics
\usepackage{xstring} % For robust string manipulation

\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    filecolor=magenta,      
    urlcolor=cyan,
    breaklinks=true, % Allow long URLs to be broken across lines
}

\renewcommand*\familydefault{\sfdefault} % Set Fira Sans as default

% Redefine tightlist to use default spacing, ensuring list items are clearly separated.
\providecommand{\tightlist}{}
\newcommand{\passthrough}[1]{#1} % Define \passthrough for pandoc listings issue

\newcommand{\pandocbounded}[1]{#1} % Define \pandocbounded to handle Pandoc's image wrapping

% Redefine \includegraphics to handle missing files and URLs gracefully
\LetLtxMacro{\oldincludegraphics}{\includegraphics}
\renewcommand{\includegraphics}[2][]{%
  \IfSubStr{#2}{://}{%
    \texttt{[Remote image at URL not included: \detokenize{#2}]}%
  }{%
    \IfFileExists{#2}
      {\oldincludegraphics[#1]{#2}}
      {\texttt{[Local image file not found: \detokenize{#2}]}}%
  }%
}
\title{IPCC AR7 Working Group II Report}
\author{Generated by Nimble Codexes Factory}
\date{\today}

\begin{document}

\maketitle

\begin{center}
  \parbox{0.8\textwidth}{
    \centering
    \Large\textbf{$draft_header_line_1$}\\[0.5em]
    \Large\textbf{$draft_header_line_2$}
  }
\end{center}
\vspace{1cm}

$explanation_section$

\begin{multicols}{2}
$body$
\end{multicols}

\end{document}
"""
    final_latex_template = latex_template.replace("$draft_header_line_1$", draft_header_line_1)
    final_latex_template = final_latex_template.replace("$draft_header_line_2$", draft_header_line_2)
    final_latex_template = final_latex_template.replace("$explanation_section$", explanation_section_latex)
    template_path = os.path.join(output_dir, "ipcc_template.tex")
    with open(template_path, 'w') as f:
        f.write(final_latex_template)
    print(f"LaTeX template created at: {template_path}")

    # Create the definitive, correct Lua filter
    lua_filter_content = r"""-- Pandoc Lua Filter to handle tables, chapter headings, and special characters.

-- Rule 1: Handle tables in a multicol environment.
function Table(table_element)
  -- Use the standard LaTeX table* float for full-width tables in a two-column layout.
  -- This also forces any longtable to become a tabular, ensuring compatibility.
  local table_body = pandoc.utils.stringify(table_element)
  -- Replace longtable with tabular, which is required inside the table* float.
  table_body = table_body:gsub('\\begin{longtable}', '\\begin{tabular}')
  table_body = table_body:gsub('\\end{longtable}', '\\end{tabular}')
  -- Escape ampersands that are not already escaped to prevent LaTeX errors.
  table_body = table_body:gsub('([^\\\\])&', '%1\\&')

  local new_table = pandoc.RawBlock('latex', table_body)
  local begin_table_star = pandoc.RawBlock('latex', '\\begin{table*}[t]')
  local end_table_star = pandoc.RawBlock('latex', '\\end{table*}')
  return {begin_table_star, new_table, end_table_star}
end

-- Rule 2: Reformat chapter headings.
function Header(el)
  local text = pandoc.utils.stringify(el.content)
  local chap_match = string.match(text, '^Chapter %d+: (.*)')
  
  if chap_match then
    el.level = 1 -- Ensure it is a top-level heading for numbering
    -- Create new inlines from the captured part of the title
    local new_inlines = pandoc.read(chap_match).blocks[1].content
    el.content = new_inlines
    return el
  end
  
  -- Make other special sections unnumbered
  if string.match(text, '^Summary For Policymakers') or 
     string.match(text, '^Technical Summary') or 
     string.match(text, '^Annex') then
    el.level = 1
    el.attributes['unnumbered'] = 'true'
    return el
  end

  -- Rule 2b: Strip hardcoded numbering like "2.1 " from other headings
  local heading_text = pandoc.utils.stringify(el.content)
  local stripped_text = heading_text:gsub('^[%d%.]+%s*', '')
  if stripped_text ~= heading_text and stripped_text ~= '' then
    local new_inlines = pandoc.read(stripped_text).blocks[1].content
    el.content = new_inlines
  end

  return el
end

-- Rule 3: Escape special LaTeX characters in regular text.
function Str(el)
  el.text = el.text:gsub('#', '\\#')
  el.text = el.text:gsub('_', '\\_')
  -- Convert Unicode subscript 2 to LaTeX command
  el.text = el.text:gsub('₂', '\\textsubscript{2}')
  return el
end

-- Rule 4: Ensure URLs are correctly handled.
-- This wraps any link URL in the \url{} command to allow for special characters.
function Link(el)
  -- If the link text is the same as the URL (an autolink),
  -- replace the whole element with a \url command.
  if pandoc.utils.stringify(el.content) == el.target then
    return pandoc.RawInline('latex', '\\url{' .. el.target .. '}')
  end
  return el
end
"""
    filter_path = os.path.join(output_dir, "table_filter.lua")
    with open(filter_path, 'w') as f:
        f.write(lua_filter_content)
    print(f"Pandoc Lua filter created at: {filter_path}")

    # Create the compilation script with the YAML metadata block disabled
    compile_script = r"""#!/bin/bash
# This script compiles the full report from Markdown to PDF.
# It requires Pandoc and a LaTeX distribution (like TeX Live) to be installed.

OUTPUT_DIR="."

# Step 1: Convert Markdown to LaTeX using Pandoc, the custom template, and the Lua filter
echo "Converting Markdown to LaTeX with Lua filter..."
pandoc -f markdown-yaml_metadata_block "${OUTPUT_DIR}/full_report.md" -o "${OUTPUT_DIR}/full_report.tex" -V table-engine=default --template="${OUTPUT_DIR}/ipcc_template.tex" --lua-filter="${OUTPUT_DIR}/table_filter.lua" --number-sections --listings

if [ $? -ne 0 ]; then
    echo "Pandoc conversion failed. Please check your Pandoc installation and file paths."
    exit 1
fi

# Step 2: Compile the LaTeX file to PDF
echo "Compiling LaTeX to PDF..."
cd "${OUTPUT_DIR}"
latexmk -lualatex full_report.tex

if [ $? -ne 0 ]; then
    echo "PDF compilation failed. Please check your LaTeX installation and the full_report.log file for errors."
    exit 1
fi

# Clean up auxiliary files
latexmk -c

echo "\nCompilation successful!"
echo "Final report is available at: ${OUTPUT_DIR}/full_report.pdf"
"""
    script_path = os.path.join(output_dir, "compile_report.sh")
    with open(script_path, 'w') as f:
        f.write(compile_script)
    os.chmod(script_path, 0o755) # Make the script executable
    print(f"Compilation script created at: {script_path}")

    # Print final instructions
    print("\n--- Action Required ---")
    print("To generate the final PDF report, please run the following command from your terminal:")
    print(f"\ncd {output_dir} && ./compile_report.sh\n")
    print("Note: This requires Pandoc and a LaTeX distribution (e.g., TeX Live, MiKTeX) to be installed on your system.")

def main():
    parser = argparse.ArgumentParser(description="Generate, verify, and assemble the AR7 Climate Report.")
    parser.add_argument("command", help="The command to execute: a prompt key (e.g., 'chapter_01_framing'), 'all', or 'assemble'.")
    parser.add_argument("--model", default="gemini/gemini-1.5-flash-latest", help="The model to use for generation.")
    parser.add_argument("--verification-model", default="gemini/gemini-2.5-pro", help="The model to use for the verification step.")
    parser.add_argument("--skip-verification", action="store_true", help="Skip the citation verification step.")
    parser.add_argument("--lite", action="store_true", help="Generate a lite report with word limits and a faster model.")
    parser.add_argument("--word-limit", type=int, default=500, help="The approximate word limit for each chapter in lite mode.")
    parser.add_argument("--system-prompt-override", type=str, help="Path to a JSON file containing a custom system prompt.")
    args = parser.parse_args()

    output_dir = "//nimble/codexes-factory/prompts/generated_chapters"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open('//nimble/codexes-factory/prompts/ar7_climate_report_prompts.json', 'r') as f:
        prompts_data = json.load(f)

    override_system_prompt = None
    if args.system_prompt_override:
        try:
            with open(args.system_prompt_override, 'r') as f:
                override_data = json.load(f)
            override_system_prompt = override_data.get('system_prompt')
            print(f"Using override file: {args.system_prompt_override}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading override file: {e}")
            return

    if args.command == 'assemble':
        assemble_report(prompts_data, output_dir, args)
        return

    prompt_sections = [
        "reprompts", "chapters", "regional_chapters", "thematic_chapters", "annexes", "technical_guidelines"
    ]

    prompts_to_run = []
    if args.command == 'all':
        for section_name in prompt_sections:
            if section_name in prompts_data and isinstance(prompts_data[section_name], dict):
                for key in prompts_data[section_name]:
                    prompts_to_run.append((section_name, key))
    else:
        found = False
        for section_name in prompt_sections:
            if section_name in prompts_data and isinstance(prompts_data[section_name], dict) and args.command in prompts_data[section_name]:
                prompts_to_run.append((section_name, args.command))
                found = True
                break
        if not found:
            print(f"Error: Prompt key '{args.command}' not found in any prompt section.")
            return

    for section, key in prompts_to_run:
        prompt_details = prompts_data[section][key]
        print(f"Generating content for: {key}")

        system_prompt = override_system_prompt if override_system_prompt is not None else prompt_details.get('system_prompt', '')
        user_prompt = prompt_details.get('user_prompt', '')

        if not user_prompt:
            print(f"Skipping {key} as it has no user_prompt.")
            continue

        model_to_use = args.model
        verification_model_to_use = args.verification_model
        max_tokens_to_use = None

        if args.lite:
            model_to_use = "gemini/gemini-1.5-flash-latest"
            verification_model_to_use = "gemini/gemini-1.5-flash-latest"
            max_tokens_to_use = int(args.word_limit * 1.3)
            user_prompt += f"\n\nIMPORTANT: The response must be approximately {args.word_limit} words."

        generated_content = generate_text(system_prompt, user_prompt, key, model_to_use, max_tokens=max_tokens_to_use)

        if "Error generating content" in generated_content or "Max retries exceeded" in generated_content:
            print(f"Skipping file write and verification for {key} due to generation error.")
            error_filename = os.path.join(output_dir, f"{key}_error.log")
            with open(error_filename, 'w') as f:
                f.write(generated_content)
            print(f"Error details for {key} written to {error_filename}")
            continue

        output_filename = os.path.join(output_dir, f"{key}_output.md")
        with open(output_filename, 'w') as f:
            f.write(generated_content)

        print(f"Content for {key} written to {output_filename}")

        if not args.skip_verification:
            verification_notes = verify_chapter(generated_content, verification_model_to_use, key)
            with open(output_filename, 'a') as f:
                f.write("\n\n" + verification_notes)
            print(f"Verification notes for {key} appended to {output_filename}")

if __name__ == '__main__':
    main()
