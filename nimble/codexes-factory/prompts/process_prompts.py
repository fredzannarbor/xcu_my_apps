import json

def generate_markdown():
    with open('//nimble/codexes-factory/prompts/ar7_climate_report_prompts.json', 'r') as f:
        data = json.load(f)

    markdown_output = []

    # Metadata
    markdown_output.append("# IPCC AR7 Working Group II Report: Climate Change 202X: Impacts, Adaptation and Vulnerability")
    markdown_output.append(f"**Version:** {data['metadata']['version']}")
    markdown_output.append(f"**Created:** {data['metadata']['created']}")
    markdown_output.append(f"**Updated:** {data['metadata']['updated']}")
    markdown_output.append(f"**Author:** {data['metadata']['author']}")
    markdown_output.append("\n---\n")

    # Reprompts
    if 'reprompts' in data:
        markdown_output.append("## Summary for Policymakers and Technical Summary")
        for key, prompt in data['reprompts'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")

    # Chapters
    if 'chapters' in data:
        markdown_output.append("## Chapters")
        for key, prompt in data['chapters'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")

    # Regional Chapters
    if 'regional_chapters' in data:
        markdown_output.append("## Regional Chapters")
        for key, prompt in data['regional_chapters'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")

    # Thematic Chapters
    if 'thematic_chapters' in data:
        markdown_output.append("## Thematic Chapters")
        for key, prompt in data['thematic_chapters'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")

    # Annexes
    if 'annexes' in data:
        markdown_output.append("## Annexes")
        for key, prompt in data['annexes'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")

    # Technical Guidelines
    if 'technical_guidelines' in data:
        markdown_output.append("## Technical Guidelines")
        for key, prompt in data['technical_guidelines'].items():
            title = key.replace('_', ' ').title()
            markdown_output.append(f"### {title}")
            markdown_output.append("#### System Prompt")
            markdown_output.append(f"```\n{prompt['system_prompt']}\n```")
            markdown_output.append("#### User Prompt")
            markdown_output.append(f"```\n{prompt['user_prompt']}\n```")
            markdown_output.append("\n")


    with open('//nimble/codexes-factory/prompts/ar7_climate_report_prompts.md', 'w') as f:
        f.write('\n'.join(markdown_output))

if __name__ == '__main__':
    generate_markdown()
