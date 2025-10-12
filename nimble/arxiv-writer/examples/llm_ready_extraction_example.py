#!/usr/bin/env python3
"""
Example script demonstrating LLM-ready content extraction workflow.

This script shows how to use the ContentExtractor and AnswerKeyGenerator
to convert academic papers into training data for LLMs using the Karpathy strategy.
"""

import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from arxiv_writer.core.content_extractor import ContentExtractor
from arxiv_writer.core.answer_key_generator import AnswerKeyGenerator


def main():
    """Demonstrate the complete LLM-ready extraction workflow."""
    print("🚀 LLM-Ready Content Extraction Example")
    print("=" * 50)
    
    # Create temporary directory for this example
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Sample academic paper in LaTeX format
        sample_latex = """
        \\documentclass{article}
        \\begin{document}
        
        \\title{Novel Approach to Machine Learning Optimization}
        \\author{Research Team}
        \\maketitle
        
        \\section{Introduction}
        This paper presents a groundbreaking approach to machine learning optimization
        that addresses key limitations in existing methodologies.
        
        \\section{Methodology}
        Our analysis reveals that the proposed method significantly outperforms 
        existing approaches through innovative attention mechanisms. The results 
        indicate a remarkable 25\\% improvement in accuracy compared to baseline 
        methods. We found that the key factor enabling this performance gain is 
        the novel multi-head attention architecture that allows for better feature 
        extraction and representation learning.
        
        \\begin{figure}
        \\includegraphics{performance_chart.png}
        \\caption{Performance comparison across different datasets showing consistent improvements}
        \\end{figure}
        
        \\subsection{Case Study: Medical Image Classification}
        Consider the following practical example to illustrate our approach.
        The problem we address is accurate classification of medical images 
        with limited training data, a common challenge in healthcare applications.
        Our method uses transfer learning with pre-trained convolutional neural 
        networks, fine-tuned on domain-specific data. The results showed a 
        substantial 15\\% improvement over baseline methods, achieving 95\\% accuracy.
        The key lesson learned is that pre-training on large, diverse datasets 
        is crucial for success in specialized domains.
        
        \\section{Results}
        We found that our approach consistently outperforms existing methods 
        across multiple benchmark datasets. The evaluation demonstrates superior 
        performance in terms of both accuracy and computational efficiency.
        Therefore, we conclude that this method represents a significant 
        advancement in the field of machine learning optimization.
        
        \\begin{table}
        \\begin{tabular}{|c|c|c|}
        \\hline
        Method & Accuracy & F1-Score \\\\
        \\hline
        Baseline CNN & 80\\% & 0.75 \\\\
        ResNet-50 & 85\\% & 0.82 \\\\
        Our Method & 95\\% & 0.92 \\\\
        \\hline
        \\end{tabular}
        \\caption{Quantitative comparison of different approaches}
        \\end{table}
        
        \\section{Conclusion}
        This work demonstrates the effectiveness of our proposed approach and 
        opens new avenues for future research in machine learning optimization.
        
        \\end{document}
        """
        
        # Step 1: Create LaTeX file
        print("📄 Creating sample LaTeX paper...")
        latex_file = temp_path / "sample_paper.tex"
        latex_file.write_text(sample_latex, encoding='utf-8')
        
        # Create dummy image file for figure extraction
        image_file = temp_path / "performance_chart.png"
        image_file.write_bytes(b"dummy image data for demonstration")
        
        # Step 2: Initialize extractors
        print("🔧 Initializing content extractor and answer key generator...")
        extractor = ContentExtractor(output_dir=str(temp_path / "extraction"))
        answer_generator = AnswerKeyGenerator(output_dir=str(temp_path / "answer_keys"))
        
        # Step 3: Extract content from LaTeX
        print("📊 Extracting content from LaTeX paper...")
        extraction_result = extractor.extract_from_latex(latex_file)
        
        print(f"✅ Extraction complete!")
        print(f"   - Markdown content: {len(extraction_result.markdown_content)} characters")
        print(f"   - Figures extracted: {len(extraction_result.figures)}")
        print(f"   - SFT examples: {len(extraction_result.sft_examples)}")
        print(f"   - RL examples: {len(extraction_result.rl_examples)}")
        
        # Step 4: Generate answer keys
        print("\n🎯 Generating answer keys for training data...")
        answer_key_result = answer_generator.generate_answer_keys(extraction_result)
        
        print(f"✅ Answer key generation complete!")
        print(f"   - Total answer keys: {len(answer_key_result.answer_keys)}")
        print(f"   - Judge criteria: {len(answer_key_result.judge_criteria)}")
        
        # Step 5: Save results
        print("\n💾 Saving extraction results...")
        extraction_file = extractor.save_extraction_result(extraction_result, "sample_paper")
        answer_keys_file = answer_generator.save_answer_keys(answer_key_result, "sample_paper")
        
        print(f"✅ Results saved!")
        print(f"   - Extraction results: {extraction_file}")
        print(f"   - Answer keys: {answer_keys_file}")
        
        # Step 6: Display sample results
        print("\n📋 Sample Results:")
        print("-" * 30)
        
        # Show markdown preview
        print("🔤 Markdown Content Preview:")
        markdown_preview = extraction_result.markdown_content[:300] + "..." if len(extraction_result.markdown_content) > 300 else extraction_result.markdown_content
        print(markdown_preview)
        
        # Show SFT example
        if extraction_result.sft_examples:
            print(f"\n🎓 SFT Example Preview:")
            sft_example = extraction_result.sft_examples[0]
            print(f"   - Example ID: {sft_example.example_id}")
            print(f"   - Section Type: {sft_example.section_type}")
            print(f"   - Quality Score: {sft_example.quality_score:.2f}")
            print(f"   - Analysis Preview: {sft_example.analysis_passage[:150]}...")
        
        # Show RL example
        if extraction_result.rl_examples:
            print(f"\n🎮 RL Example Preview:")
            rl_example = extraction_result.rl_examples[0]
            print(f"   - Example ID: {rl_example.example_id}")
            print(f"   - Case Study: {rl_example.case_study_title}")
            print(f"   - Problem: {rl_example.problem_description[:100]}...")
        
        # Show answer key details
        if answer_key_result.answer_keys:
            print(f"\n🔑 Answer Key Preview:")
            answer_key = answer_key_result.answer_keys[0]
            print(f"   - Example ID: {answer_key.example_id}")
            print(f"   - Type: {answer_key.example_type}")
            print(f"   - Difficulty: {answer_key.difficulty_level.value}")
            print(f"   - Key Concepts: {', '.join(answer_key.key_concepts[:5])}")
            print(f"   - Verification Instructions: {len(answer_key.verification_instructions)}")
            print(f"   - Scoring Rubrics: {len(answer_key.scoring_rubrics)}")
        
        print("\n🎉 LLM-ready content extraction complete!")
        print("The extracted content and answer keys are now ready for LLM training.")
        print("\nNote: Files were saved in a temporary directory and will be cleaned up.")
        print("In a real scenario, specify a permanent output directory.")


if __name__ == "__main__":
    main()