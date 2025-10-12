"""
Workflow Export Component

Provides comprehensive export and sharing capabilities for workflow results.
Supports multiple formats and sharing options with metadata preservation.
"""

import streamlit as st
import pandas as pd
import json
import csv
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import sys
import io
import zipfile
import base64

# Add project paths for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from codexes.modules.ideation.core.codex_object import CodexObject

logger = logging.getLogger(__name__)


class WorkflowExporter:
    """
    Comprehensive export system for workflow results.
    Supports multiple formats and sharing options with metadata preservation.
    """
    
    def __init__(self):
        """Initialize the workflow exporter."""
        self.session_key = "workflow_export_state"
        self.export_formats = {
            "JSON": {"extension": ".json", "mime": "application/json"},
            "CSV": {"extension": ".csv", "mime": "text/csv"},
            "Excel": {"extension": ".xlsx", "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
            "Text Report": {"extension": ".txt", "mime": "text/plain"},
            "HTML Report": {"extension": ".html", "mime": "text/html"},
            "Markdown": {"extension": ".md", "mime": "text/markdown"}
        }
        
        logger.info("WorkflowExporter initialized")
    
    def render_export_interface(self, workflow_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render the export interface for workflow results.
        
        Args:
            workflow_results: Results from workflow execution
            
        Returns:
            Dictionary containing export actions and results
        """
        if not workflow_results or not workflow_results.get("success"):
            st.info("📤 No workflow results available for export.")
            return {}
        
        st.markdown("### 📤 Export & Share Results")
        
        # Create export tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Quick Export", "📋 Detailed Export", "🔗 Share Results", "📁 Batch Export"])
        
        with tab1:
            return self._render_quick_export(workflow_results)
        
        with tab2:
            return self._render_detailed_export(workflow_results)
        
        with tab3:
            return self._render_share_results(workflow_results)
        
        with tab4:
            return self._render_batch_export(workflow_results)
    
    def _render_quick_export(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render quick export options."""
        st.markdown("#### 📊 Quick Export")
        st.markdown("Export results in common formats with one click.")
        
        workflow_type = results.get("workflow_type", "unknown")
        
        # Quick export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export as CSV", use_container_width=True):
                csv_data = self._export_to_csv(results)
                if csv_data:
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv_data,
                        file_name=f"{workflow_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("📋 Export as JSON", use_container_width=True):
                json_data = self._export_to_json(results)
                if json_data:
                    st.download_button(
                        label="💾 Download JSON",
                        data=json_data,
                        file_name=f"{workflow_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        with col3:
            if st.button("📄 Export as Report", use_container_width=True):
                report_data = self._export_to_text_report(results)
                if report_data:
                    st.download_button(
                        label="💾 Download Report",
                        data=report_data,
                        file_name=f"{workflow_type}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
        
        # Preview section
        if st.checkbox("🔍 Preview Export Data"):
            self._render_export_preview(results)
        
        return {}
    
    def _render_detailed_export(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render detailed export options with customization."""
        st.markdown("#### 📋 Detailed Export")
        st.markdown("Customize your export with advanced options.")
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format",
            options=list(self.export_formats.keys()),
            help="Choose the format for your export"
        )
        
        # Export options
        st.markdown("**Export Options:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_metadata = st.checkbox("Include Metadata", value=True)
            include_timestamps = st.checkbox("Include Timestamps", value=True)
            include_config = st.checkbox("Include Configuration", value=False)
        
        with col2:
            include_raw_data = st.checkbox("Include Raw Data", value=False)
            include_analytics = st.checkbox("Include Analytics", value=True)
            compress_output = st.checkbox("Compress Output", value=False)
        
        # Content selection
        workflow_type = results.get("workflow_type", "unknown")
        
        if workflow_type == "tournament":
            content_options = self._get_tournament_export_options(results)
        elif workflow_type == "reader_panel":
            content_options = self._get_reader_panel_export_options(results)
        elif workflow_type == "series_generation":
            content_options = self._get_series_export_options(results)
        else:
            content_options = ["All Results"]
        
        selected_content = st.multiselect(
            "Content to Export",
            options=content_options,
            default=content_options,
            help="Select which parts of the results to include"
        )
        
        # Custom filename
        default_filename = f"{workflow_type}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        custom_filename = st.text_input(
            "Filename (without extension)",
            value=default_filename,
            help="Enter a custom filename for your export"
        )
        
        # Export button
        if st.button("🚀 Generate Export", type="primary"):
            export_options = {
                "format": export_format,
                "include_metadata": include_metadata,
                "include_timestamps": include_timestamps,
                "include_config": include_config,
                "include_raw_data": include_raw_data,
                "include_analytics": include_analytics,
                "compress_output": compress_output,
                "selected_content": selected_content,
                "filename": custom_filename
            }
            
            export_data = self._generate_custom_export(results, export_options)
            
            if export_data:
                file_extension = self.export_formats[export_format]["extension"]
                mime_type = self.export_formats[export_format]["mime"]
                
                if compress_output and export_format != "Excel":
                    # Create ZIP file
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        zip_file.writestr(f"{custom_filename}{file_extension}", export_data)
                    
                    st.download_button(
                        label="💾 Download Export (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"{custom_filename}.zip",
                        mime="application/zip"
                    )
                else:
                    st.download_button(
                        label="💾 Download Export",
                        data=export_data,
                        file_name=f"{custom_filename}{file_extension}",
                        mime=mime_type
                    )
        
        return {}
    
    def _render_share_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render sharing options for results."""
        st.markdown("#### 🔗 Share Results")
        st.markdown("Share your workflow results with others.")
        
        # Generate shareable summary
        summary = self._generate_shareable_summary(results)
        
        # Sharing options
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Quick Share:**")
            
            # Copy to clipboard (text summary)
            if st.button("📋 Copy Summary to Clipboard"):
                st.code(summary, language="text")
                st.info("📋 Summary displayed above - copy manually")
            
            # Generate shareable link (placeholder)
            if st.button("🔗 Generate Shareable Link"):
                st.info("🔗 Shareable links feature coming soon!")
        
        with col2:
            st.markdown("**Export for Sharing:**")
            
            # Export as shareable formats
            if st.button("📧 Export for Email"):
                email_content = self._generate_email_export(results)
                st.text_area("Email Content:", value=email_content, height=200)
            
            if st.button("📱 Export for Social Media"):
                social_content = self._generate_social_export(results)
                st.text_area("Social Media Post:", value=social_content, height=100)
        
        # Collaboration features
        st.markdown("#### 👥 Collaboration")
        
        # Team sharing (placeholder)
        team_email = st.text_input("Team Member Email", placeholder="colleague@example.com")
        if st.button("📤 Share with Team Member") and team_email:
            st.info(f"📤 Team sharing feature coming soon! Would share with: {team_email}")
        
        # Export for external tools
        st.markdown("#### 🔧 External Tool Integration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export for Spreadsheet"):
                csv_data = self._export_to_csv(results)
                if csv_data:
                    st.download_button(
                        label="💾 Download for Excel/Sheets",
                        data=csv_data,
                        file_name=f"workflow_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("📈 Export for Analytics"):
                analytics_data = self._export_for_analytics(results)
                if analytics_data:
                    st.download_button(
                        label="💾 Download Analytics Data",
                        data=analytics_data,
                        file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        with col3:
            if st.button("📝 Export for Documentation"):
                doc_data = self._export_to_markdown(results)
                if doc_data:
                    st.download_button(
                        label="💾 Download Markdown",
                        data=doc_data,
                        file_name=f"workflow_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
        
        return {}
    
    def _render_batch_export(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Render batch export options."""
        st.markdown("#### 📁 Batch Export")
        st.markdown("Export multiple formats at once or combine with other results.")
        
        # Batch export formats
        selected_formats = st.multiselect(
            "Select Export Formats",
            options=list(self.export_formats.keys()),
            default=["JSON", "CSV", "Text Report"],
            help="Choose multiple formats to export simultaneously"
        )
        
        # Batch options
        col1, col2 = st.columns(2)
        
        with col1:
            create_zip = st.checkbox("Create ZIP Archive", value=True)
            include_timestamp = st.checkbox("Include Timestamp in Filenames", value=True)
        
        with col2:
            include_summary = st.checkbox("Include Summary File", value=True)
            include_metadata_file = st.checkbox("Include Metadata File", value=False)
        
        # Generate batch export
        if st.button("🚀 Generate Batch Export", type="primary") and selected_formats:
            batch_files = {}
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            workflow_type = results.get("workflow_type", "unknown")
            
            # Generate each format
            for format_name in selected_formats:
                filename_base = f"{workflow_type}_results"
                if include_timestamp:
                    filename_base += f"_{timestamp}"
                
                if format_name == "JSON":
                    data = self._export_to_json(results)
                    batch_files[f"{filename_base}.json"] = data
                elif format_name == "CSV":
                    data = self._export_to_csv(results)
                    batch_files[f"{filename_base}.csv"] = data
                elif format_name == "Text Report":
                    data = self._export_to_text_report(results)
                    batch_files[f"{filename_base}.txt"] = data
                elif format_name == "HTML Report":
                    data = self._export_to_html_report(results)
                    batch_files[f"{filename_base}.html"] = data
                elif format_name == "Markdown":
                    data = self._export_to_markdown(results)
                    batch_files[f"{filename_base}.md"] = data
            
            # Add summary file if requested
            if include_summary:
                summary = self._generate_shareable_summary(results)
                summary_filename = f"{workflow_type}_summary"
                if include_timestamp:
                    summary_filename += f"_{timestamp}"
                batch_files[f"{summary_filename}.txt"] = summary
            
            # Add metadata file if requested
            if include_metadata_file:
                metadata = self._extract_metadata(results)
                metadata_filename = f"{workflow_type}_metadata"
                if include_timestamp:
                    metadata_filename += f"_{timestamp}"
                batch_files[f"{metadata_filename}.json"] = json.dumps(metadata, indent=2)
            
            # Create download
            if create_zip:
                # Create ZIP file
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for filename, data in batch_files.items():
                        zip_file.writestr(filename, data)
                
                zip_filename = f"{workflow_type}_batch_export"
                if include_timestamp:
                    zip_filename += f"_{timestamp}"
                
                st.download_button(
                    label="💾 Download Batch Export (ZIP)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{zip_filename}.zip",
                    mime="application/zip"
                )
            else:
                # Offer individual downloads
                st.markdown("**Individual Downloads:**")
                for filename, data in batch_files.items():
                    file_extension = Path(filename).suffix
                    mime_type = "text/plain"
                    
                    if file_extension == ".json":
                        mime_type = "application/json"
                    elif file_extension == ".csv":
                        mime_type = "text/csv"
                    elif file_extension == ".html":
                        mime_type = "text/html"
                    elif file_extension == ".md":
                        mime_type = "text/markdown"
                    
                    st.download_button(
                        label=f"💾 {filename}",
                        data=data,
                        file_name=filename,
                        mime=mime_type,
                        key=f"download_{filename}"
                    )
        
        return {}
    
    def _render_export_preview(self, results: Dict[str, Any]):
        """Render preview of export data."""
        st.markdown("#### 🔍 Export Preview")
        
        # Show preview of different formats
        preview_format = st.selectbox(
            "Preview Format",
            options=["JSON", "CSV", "Text Report"],
            key="preview_format"
        )
        
        if preview_format == "JSON":
            json_preview = self._export_to_json(results)
            if json_preview:
                # Show first 1000 characters
                preview_text = json_preview[:1000]
                if len(json_preview) > 1000:
                    preview_text += "\n... (truncated)"
                st.code(preview_text, language="json")
        
        elif preview_format == "CSV":
            csv_preview = self._export_to_csv(results)
            if csv_preview:
                # Convert to DataFrame for better display
                try:
                    df = pd.read_csv(io.StringIO(csv_preview))
                    st.dataframe(df.head(10), use_container_width=True)
                    if len(df) > 10:
                        st.info(f"Showing first 10 rows of {len(df)} total rows")
                except Exception:
                    st.code(csv_preview[:1000], language="text")
        
        elif preview_format == "Text Report":
            report_preview = self._export_to_text_report(results)
            if report_preview:
                preview_text = report_preview[:2000]
                if len(report_preview) > 2000:
                    preview_text += "\n... (truncated)"
                st.text(preview_text)
    
    def _export_to_json(self, results: Dict[str, Any]) -> str:
        """Export results to JSON format."""
        try:
            # Create a clean export structure
            export_data = {
                "export_info": {
                    "format": "JSON",
                    "timestamp": datetime.now().isoformat(),
                    "workflow_type": results.get("workflow_type", "unknown")
                },
                "results": results
            }
            
            return json.dumps(export_data, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error exporting to JSON: {e}")
            return None
    
    def _export_to_csv(self, results: Dict[str, Any]) -> str:
        """Export results to CSV format."""
        try:
            workflow_type = results.get("workflow_type", "unknown")
            
            if workflow_type == "tournament":
                return self._export_tournament_to_csv(results)
            elif workflow_type == "reader_panel":
                return self._export_reader_panel_to_csv(results)
            elif workflow_type == "series_generation":
                return self._export_series_to_csv(results)
            else:
                return self._export_generic_to_csv(results)
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def _export_to_text_report(self, results: Dict[str, Any]) -> str:
        """Export results to text report format."""
        try:
            workflow_type = results.get("workflow_type", "unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report = f"""WORKFLOW RESULTS REPORT
{'=' * 50}

Generated: {timestamp}
Workflow Type: {workflow_type.replace('_', ' ').title()}

"""
            
            if workflow_type == "tournament":
                report += self._generate_tournament_report(results)
            elif workflow_type == "reader_panel":
                report += self._generate_reader_panel_report(results)
            elif workflow_type == "series_generation":
                report += self._generate_series_report(results)
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating text report: {e}")
            return None
    
    def _export_to_html_report(self, results: Dict[str, Any]) -> str:
        """Export results to HTML report format."""
        try:
            workflow_type = results.get("workflow_type", "unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Workflow Results Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #007cba; }}
    </style>
</head>
<body>
    <h1>Workflow Results Report</h1>
    <p><strong>Generated:</strong> {timestamp}</p>
    <p><strong>Workflow Type:</strong> {workflow_type.replace('_', ' ').title()}</p>
"""
            
            # Add workflow-specific content
            if workflow_type == "tournament":
                html += self._generate_tournament_html(results)
            elif workflow_type == "reader_panel":
                html += self._generate_reader_panel_html(results)
            elif workflow_type == "series_generation":
                html += self._generate_series_html(results)
            
            html += """
</body>
</html>"""
            
            return html
        
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}")
            return None
    
    def _export_to_markdown(self, results: Dict[str, Any]) -> str:
        """Export results to Markdown format."""
        try:
            workflow_type = results.get("workflow_type", "unknown")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            markdown = f"""# Workflow Results Report

**Generated:** {timestamp}  
**Workflow Type:** {workflow_type.replace('_', ' ').title()}

---

"""
            
            if workflow_type == "tournament":
                markdown += self._generate_tournament_markdown(results)
            elif workflow_type == "reader_panel":
                markdown += self._generate_reader_panel_markdown(results)
            elif workflow_type == "series_generation":
                markdown += self._generate_series_markdown(results)
            
            return markdown
        
        except Exception as e:
            logger.error(f"Error generating Markdown: {e}")
            return None
    
    def _export_tournament_to_csv(self, results: Dict[str, Any]) -> str:
        """Export tournament results to CSV."""
        tournament_results = results.get("tournament_results", {})
        rankings = tournament_results.get("final_rankings", [])
        
        if not rankings:
            return "No tournament rankings available"
        
        # Create CSV data
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Header
        writer.writerow(["Rank", "Title", "Type", "Final_Score", "Wins", "Losses"])
        
        # Data rows
        for i, ranking in enumerate(rankings):
            writer.writerow([
                i + 1,
                ranking.get('title', 'Unknown'),
                ranking.get('type', 'Unknown'),
                ranking.get('final_score', 0),
                ranking.get('wins', 0),
                ranking.get('losses', 0)
            ])
        
        return csv_buffer.getvalue()
    
    def _export_reader_panel_to_csv(self, results: Dict[str, Any]) -> str:
        """Export reader panel results to CSV."""
        panel_results = results.get("panel_results", [])
        
        if not panel_results:
            return "No reader panel results available"
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Header
        writer.writerow(["Object_Title", "Overall_Score", "Market_Appeal", "Emotional_Engagement", "Genre_Fit"])
        
        # Data rows
        for result in panel_results:
            obj_title = result.get('object_title', 'Unknown')
            results_data = result.get('results', {})
            
            writer.writerow([
                obj_title,
                results_data.get('overall_score', 0),
                results_data.get('market_appeal', 0),
                results_data.get('emotional_engagement', 0),
                results_data.get('genre_fit', 0)
            ])
        
        return csv_buffer.getvalue()
    
    def _export_series_to_csv(self, results: Dict[str, Any]) -> str:
        """Export series generation results to CSV."""
        series_data = results.get("series_data", {})
        series_entries = series_data.get("series_entries", [])
        
        if not series_entries:
            return "No series entries available"
        
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Header
        writer.writerow(["Book_Number", "Title", "Genre", "Word_Count", "Consistency_Score"])
        
        # Data rows
        for i, entry in enumerate(series_entries):
            writer.writerow([
                i + 1,
                entry.get('title', f'Book {i+1}'),
                entry.get('genre', 'Unknown'),
                entry.get('word_count', 0),
                entry.get('consistency_score', 0)
            ])
        
        return csv_buffer.getvalue()
    
    def _export_generic_to_csv(self, results: Dict[str, Any]) -> str:
        """Export generic results to CSV."""
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        
        # Simple key-value export
        writer.writerow(["Key", "Value"])
        
        for key, value in results.items():
            if isinstance(value, (str, int, float, bool)):
                writer.writerow([key, value])
        
        return csv_buffer.getvalue()
    
    def _generate_tournament_report(self, results: Dict[str, Any]) -> str:
        """Generate tournament text report."""
        tournament_results = results.get("tournament_results", {})
        rankings = tournament_results.get("final_rankings", [])
        
        if not rankings:
            return "No tournament results available.\n"
        
        report = "TOURNAMENT RESULTS\n"
        report += "-" * 20 + "\n\n"
        
        # Winner
        winner = rankings[0]
        report += f"🏆 WINNER: {winner.get('title', 'Unknown')} ({winner.get('type', 'Unknown')})\n"
        report += f"   Final Score: {winner.get('final_score', 0):.3f}\n\n"
        
        # Full rankings
        report += "COMPLETE RANKINGS:\n"
        for i, ranking in enumerate(rankings):
            report += f"{i+1:2d}. {ranking.get('title', 'Unknown'):30s} "
            report += f"({ranking.get('type', 'Unknown'):10s}) "
            report += f"Score: {ranking.get('final_score', 0):6.3f} "
            report += f"W/L: {ranking.get('wins', 0)}/{ranking.get('losses', 0)}\n"
        
        return report + "\n"
    
    def _generate_reader_panel_report(self, results: Dict[str, Any]) -> str:
        """Generate reader panel text report."""
        panel_results = results.get("panel_results", [])
        
        if not panel_results:
            return "No reader panel results available.\n"
        
        report = "READER PANEL RESULTS\n"
        report += "-" * 20 + "\n\n"
        
        # Sort by overall score
        sorted_results = sorted(
            panel_results,
            key=lambda x: x.get('results', {}).get('overall_score', 0),
            reverse=True
        )
        
        for i, result in enumerate(sorted_results):
            obj_title = result.get('object_title', 'Unknown')
            results_data = result.get('results', {})
            
            report += f"{i+1}. {obj_title}\n"
            report += f"   Overall Score: {results_data.get('overall_score', 0):.2f}/5.0\n"
            report += f"   Market Appeal: {results_data.get('market_appeal', 0):.2f}/5.0\n"
            report += f"   Emotional Engagement: {results_data.get('emotional_engagement', 0):.2f}/5.0\n"
            report += f"   Genre Fit: {results_data.get('genre_fit', 0):.2f}/5.0\n\n"
        
        return report
    
    def _generate_series_report(self, results: Dict[str, Any]) -> str:
        """Generate series generation text report."""
        series_data = results.get("series_data", {})
        series_entries = series_data.get("series_entries", [])
        
        if not series_entries:
            return "No series entries available.\n"
        
        report = "SERIES GENERATION RESULTS\n"
        report += "-" * 25 + "\n\n"
        
        report += f"Generated {len(series_entries)} books:\n\n"
        
        for i, entry in enumerate(series_entries):
            report += f"Book {i+1}: {entry.get('title', f'Book {i+1}')}\n"
            report += f"   Genre: {entry.get('genre', 'Unknown')}\n"
            report += f"   Word Count: {entry.get('word_count', 0):,}\n"
            report += f"   Consistency Score: {entry.get('consistency_score', 0):.2f}\n\n"
        
        return report
    
    def _generate_tournament_html(self, results: Dict[str, Any]) -> str:
        """Generate tournament HTML content."""
        tournament_results = results.get("tournament_results", {})
        rankings = tournament_results.get("final_rankings", [])
        
        if not rankings:
            return "<p>No tournament results available.</p>"
        
        html = "<h2>Tournament Results</h2>\n"
        
        # Winner
        winner = rankings[0]
        html += f'<div class="metric"><strong>Winner:</strong> {winner.get("title", "Unknown")} ({winner.get("type", "Unknown")})<br>'
        html += f'<strong>Final Score:</strong> {winner.get("final_score", 0):.3f}</div>\n'
        
        # Rankings table
        html += "<h3>Complete Rankings</h3>\n<table>\n"
        html += "<tr><th>Rank</th><th>Title</th><th>Type</th><th>Score</th><th>W/L</th></tr>\n"
        
        for i, ranking in enumerate(rankings):
            html += f"<tr><td>{i+1}</td><td>{ranking.get('title', 'Unknown')}</td>"
            html += f"<td>{ranking.get('type', 'Unknown')}</td>"
            html += f"<td>{ranking.get('final_score', 0):.3f}</td>"
            html += f"<td>{ranking.get('wins', 0)}/{ranking.get('losses', 0)}</td></tr>\n"
        
        html += "</table>\n"
        
        return html
    
    def _generate_reader_panel_html(self, results: Dict[str, Any]) -> str:
        """Generate reader panel HTML content."""
        # Similar to tournament but for reader panel
        return "<h2>Reader Panel Results</h2>\n<p>Reader panel HTML export coming soon.</p>\n"
    
    def _generate_series_html(self, results: Dict[str, Any]) -> str:
        """Generate series generation HTML content."""
        # Similar to tournament but for series
        return "<h2>Series Generation Results</h2>\n<p>Series HTML export coming soon.</p>\n"
    
    def _generate_tournament_markdown(self, results: Dict[str, Any]) -> str:
        """Generate tournament Markdown content."""
        tournament_results = results.get("tournament_results", {})
        rankings = tournament_results.get("final_rankings", [])
        
        if not rankings:
            return "No tournament results available.\n"
        
        markdown = "## Tournament Results\n\n"
        
        # Winner
        winner = rankings[0]
        markdown += f"### 🏆 Winner\n\n"
        markdown += f"**{winner.get('title', 'Unknown')}** ({winner.get('type', 'Unknown')})  \n"
        markdown += f"Final Score: {winner.get('final_score', 0):.3f}\n\n"
        
        # Rankings table
        markdown += "### Complete Rankings\n\n"
        markdown += "| Rank | Title | Type | Score | W/L |\n"
        markdown += "|------|-------|------|-------|-----|\n"
        
        for i, ranking in enumerate(rankings):
            markdown += f"| {i+1} | {ranking.get('title', 'Unknown')} | {ranking.get('type', 'Unknown')} | "
            markdown += f"{ranking.get('final_score', 0):.3f} | {ranking.get('wins', 0)}/{ranking.get('losses', 0)} |\n"
        
        return markdown + "\n"
    
    def _generate_reader_panel_markdown(self, results: Dict[str, Any]) -> str:
        """Generate reader panel Markdown content."""
        return "## Reader Panel Results\n\nReader panel Markdown export coming soon.\n\n"
    
    def _generate_series_markdown(self, results: Dict[str, Any]) -> str:
        """Generate series generation Markdown content."""
        return "## Series Generation Results\n\nSeries Markdown export coming soon.\n\n"
    
    def _generate_shareable_summary(self, results: Dict[str, Any]) -> str:
        """Generate a concise shareable summary."""
        workflow_type = results.get("workflow_type", "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        summary = f"Workflow Results Summary ({timestamp})\n"
        summary += f"Type: {workflow_type.replace('_', ' ').title()}\n\n"
        
        if workflow_type == "tournament" and results.get("tournament_results", {}).get("final_rankings"):
            winner = results["tournament_results"]["final_rankings"][0]
            summary += f"🏆 Winner: {winner.get('title', 'Unknown')} (Score: {winner.get('final_score', 0):.3f})\n"
            summary += f"Participants: {len(results['tournament_results']['final_rankings'])}\n"
        
        elif workflow_type == "reader_panel" and results.get("panel_results"):
            summary += f"Objects Evaluated: {len(results['panel_results'])}\n"
            # Add top-rated content if available
        
        elif workflow_type == "series_generation" and results.get("series_data", {}).get("series_entries"):
            entries = results["series_data"]["series_entries"]
            summary += f"Books Generated: {len(entries)}\n"
            total_words = sum(entry.get('word_count', 0) for entry in entries)
            summary += f"Total Words: {total_words:,}\n"
        
        return summary
    
    def _generate_email_export(self, results: Dict[str, Any]) -> str:
        """Generate email-friendly export."""
        summary = self._generate_shareable_summary(results)
        
        email_content = f"Subject: Workflow Results - {results.get('workflow_type', 'Unknown').replace('_', ' ').title()}\n\n"
        email_content += "Hi,\n\n"
        email_content += "Here are the results from the recent workflow execution:\n\n"
        email_content += summary
        email_content += "\n\nFull results are attached.\n\n"
        email_content += "Best regards"
        
        return email_content
    
    def _generate_social_export(self, results: Dict[str, Any]) -> str:
        """Generate social media-friendly export."""
        workflow_type = results.get("workflow_type", "unknown")
        
        if workflow_type == "tournament" and results.get("tournament_results", {}).get("final_rankings"):
            winner = results["tournament_results"]["final_rankings"][0]
            return f"🏆 Tournament Results: '{winner.get('title', 'Unknown')}' wins with a score of {winner.get('final_score', 0):.3f}! #CreativeWriting #Tournament"
        
        elif workflow_type == "series_generation" and results.get("series_data", {}).get("series_entries"):
            entries = results["series_data"]["series_entries"]
            return f"📚 Generated a {len(entries)}-book series! Total of {sum(entry.get('word_count', 0) for entry in entries):,} words. #SeriesGeneration #CreativeWriting"
        
        else:
            return f"✅ Completed {workflow_type.replace('_', ' ')} workflow! #CreativeWriting #AI"
    
    def _export_for_analytics(self, results: Dict[str, Any]) -> str:
        """Export data optimized for analytics tools."""
        analytics_data = {
            "metadata": self._extract_metadata(results),
            "metrics": self._extract_metrics(results),
            "raw_data": results
        }
        
        return json.dumps(analytics_data, indent=2, default=str)
    
    def _extract_metadata(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from results."""
        return {
            "workflow_type": results.get("workflow_type", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "success": results.get("success", False),
            "export_version": "1.0"
        }
    
    def _extract_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from results."""
        workflow_type = results.get("workflow_type", "unknown")
        metrics = {}
        
        if workflow_type == "tournament":
            tournament_results = results.get("tournament_results", {})
            rankings = tournament_results.get("final_rankings", [])
            if rankings:
                scores = [r.get('final_score', 0) for r in rankings]
                metrics = {
                    "participant_count": len(rankings),
                    "average_score": sum(scores) / len(scores) if scores else 0,
                    "score_range": max(scores) - min(scores) if scores else 0,
                    "winner_score": rankings[0].get('final_score', 0) if rankings else 0
                }
        
        return metrics
    
    def _get_tournament_export_options(self, results: Dict[str, Any]) -> List[str]:
        """Get export options for tournament results."""
        return [
            "Final Rankings",
            "Match Results",
            "Participant Details",
            "Tournament Configuration",
            "Performance Statistics"
        ]
    
    def _get_reader_panel_export_options(self, results: Dict[str, Any]) -> List[str]:
        """Get export options for reader panel results."""
        return [
            "Overall Scores",
            "Individual Evaluations",
            "Panel Demographics",
            "Evaluation Criteria",
            "Content Analysis"
        ]
    
    def _get_series_export_options(self, results: Dict[str, Any]) -> List[str]:
        """Get export options for series generation results."""
        return [
            "Series Entries",
            "Consistency Scores",
            "Base Concept",
            "Generation Parameters",
            "Content Statistics"
        ]
    
    def _generate_custom_export(self, results: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Generate custom export based on options."""
        export_format = options.get("format", "JSON")
        
        # Filter results based on selected content
        filtered_results = self._filter_results_by_content(results, options.get("selected_content", []))
        
        # Add metadata if requested
        if options.get("include_metadata", True):
            filtered_results["export_metadata"] = {
                "timestamp": datetime.now().isoformat(),
                "format": export_format,
                "options": options
            }
        
        # Generate export based on format
        if export_format == "JSON":
            return json.dumps(filtered_results, indent=2, default=str)
        elif export_format == "CSV":
            return self._export_to_csv(filtered_results)
        elif export_format == "Text Report":
            return self._export_to_text_report(filtered_results)
        elif export_format == "HTML Report":
            return self._export_to_html_report(filtered_results)
        elif export_format == "Markdown":
            return self._export_to_markdown(filtered_results)
        else:
            return json.dumps(filtered_results, indent=2, default=str)
    
    def _filter_results_by_content(self, results: Dict[str, Any], selected_content: List[str]) -> Dict[str, Any]:
        """Filter results based on selected content options."""
        if not selected_content:
            return results
        
        # This would implement content filtering based on the selected options
        # For now, return all results
        return results