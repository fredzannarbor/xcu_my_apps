#!/usr/bin/env python3

"""
LLM Response Monitor

This script helps monitor LLM responses during pipeline execution by:
1. Analyzing log files for empty response patterns
2. Providing statistics on LLM success rates
3. Identifying which prompts are most problematic
"""

import re
import json
import logging
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

def analyze_log_file(log_file_path: str):
    """Analyze a log file for LLM response patterns."""
    
    if not Path(log_file_path).exists():
        print(f"❌ Log file not found: {log_file_path}")
        return
    
    print(f"📊 Analyzing log file: {log_file_path}")
    print("="*60)
    
    # Patterns to look for
    empty_result_pattern = r"WARNING.*LLM returned empty result for prompt (\w+)"
    success_pattern = r"INFO.*Successfully received response from.*"
    error_pattern = r"ERROR.*LLM.*"
    
    empty_results = []
    success_count = 0
    error_count = 0
    prompt_stats = defaultdict(lambda: {"empty": 0, "success": 0, "error": 0})
    
    try:
        with open(log_file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                # Check for empty results
                empty_match = re.search(empty_result_pattern, line)
                if empty_match:
                    prompt_name = empty_match.group(1)
                    empty_results.append((line_num, prompt_name, line.strip()))
                    prompt_stats[prompt_name]["empty"] += 1
                
                # Check for successes
                if re.search(success_pattern, line):
                    success_count += 1
                
                # Check for errors
                if re.search(error_pattern, line):
                    error_count += 1
    
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return
    
    # Print statistics
    print(f"📈 OVERALL STATISTICS:")
    print(f"   Total LLM Successes: {success_count}")
    print(f"   Total LLM Errors: {error_count}")
    print(f"   Total Empty Results: {len(empty_results)}")
    
    if success_count + len(empty_results) > 0:
        success_rate = (success_count / (success_count + len(empty_results))) * 100
        print(f"   Success Rate: {success_rate:.1f}%")
    
    print(f"\n🎯 EMPTY RESULTS BY PROMPT:")
    if empty_results:
        prompt_counts = Counter(result[1] for result in empty_results)
        for prompt, count in prompt_counts.most_common():
            print(f"   {prompt}: {count} empty results")
    else:
        print("   ✅ No empty results found!")
    
    print(f"\n📋 RECENT EMPTY RESULTS:")
    if empty_results:
        for line_num, prompt, line in empty_results[-5:]:  # Show last 5
            timestamp = line.split(' - ')[0] if ' - ' in line else "Unknown time"
            print(f"   Line {line_num}: {prompt} ({timestamp})")
    else:
        print("   ✅ No empty results to show!")
    
    return {
        "success_count": success_count,
        "error_count": error_count,
        "empty_count": len(empty_results),
        "prompt_stats": dict(prompt_stats),
        "empty_results": empty_results
    }

def monitor_current_logs():
    """Monitor current log files."""
    
    # Common log file locations
    log_locations = [
        "logs/lsi_generation/lsi_generation.log",
        "logs/lsi_generation.log", 
        "lsi_generation.log",
        "pipeline.log"
    ]
    
    print("🔍 MONITORING LLM RESPONSES")
    print("="*60)
    
    found_logs = False
    
    for log_path in log_locations:
        if Path(log_path).exists():
            found_logs = True
            print(f"\n📄 Found log file: {log_path}")
            stats = analyze_log_file(log_path)
            
            if stats and stats["empty_count"] > 0:
                print(f"\n💡 RECOMMENDATIONS for {log_path}:")
                
                # Analyze which prompts are most problematic
                prompt_stats = stats["prompt_stats"]
                problematic_prompts = [
                    prompt for prompt, counts in prompt_stats.items() 
                    if counts["empty"] > 2
                ]
                
                if problematic_prompts:
                    print(f"   🎯 Most problematic prompts: {', '.join(problematic_prompts)}")
                    print(f"   💡 Consider adjusting these prompts or their temperature settings")
                
                if stats["empty_count"] > stats["success_count"]:
                    print(f"   ⚠️  High empty result rate - consider reviewing book metadata quality")
                
                print(f"   📝 The fixes in fix_empty_llm_responses.py should help reduce these")
    
    if not found_logs:
        print("❌ No log files found in common locations")
        print("💡 Try running your pipeline first to generate logs")
        print("📍 Common log locations checked:")
        for loc in log_locations:
            print(f"   - {loc}")

def create_monitoring_config():
    """Create a configuration for monitoring LLM responses."""
    
    config = {
        "monitoring": {
            "log_empty_responses": True,
            "log_successful_responses": True,
            "log_response_times": True,
            "alert_on_high_empty_rate": True,
            "empty_rate_threshold": 0.3,  # Alert if >30% empty
            "save_response_stats": True
        },
        "logging": {
            "level": "INFO",
            "include_prompt_names": True,
            "include_response_length": True,
            "include_model_name": True
        }
    }
    
    config_file = Path("configs/llm_monitoring_config.json")
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Created monitoring configuration at {config_file}")

def main():
    """Main monitoring function."""
    
    print("🔍 LLM Response Monitor")
    print("="*60)
    
    # Monitor current logs
    monitor_current_logs()
    
    # Create monitoring config
    print(f"\n⚙️  CONFIGURATION:")
    create_monitoring_config()
    
    print(f"\n📋 UNDERSTANDING THE WARNINGS:")
    print(f"   ✅ Empty result warnings are NORMAL and HELPFUL")
    print(f"   ✅ They indicate the system is working and monitoring LLM responses")
    print(f"   ✅ Some books genuinely don't have illustrations, series info, etc.")
    print(f"   ✅ The system uses fallback values when LLM returns empty results")
    print(f"   ⚠️  Only worry if you see >50% empty results for critical fields")
    
    print(f"\n🎯 WHAT TO DO:")
    print(f"   1. Run fix_empty_llm_responses.py (already done)")
    print(f"   2. Monitor your next pipeline run")
    print(f"   3. Check if empty results decrease")
    print(f"   4. Review specific books that cause many empty results")
    print(f"   5. Consider if the empty results are actually correct (e.g., no illustrations)")

if __name__ == "__main__":
    main()