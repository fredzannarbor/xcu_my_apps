"""
Imprint-Specific Financial Dashboard

Provides comprehensive financial reporting and analysis capabilities
for individual imprints using the integration between imprints and finance modules.
"""

import logging
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Import following current patterns
try:
    from codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration
    from codexes.core.logging_config import get_logging_manager

    # Set up logging
    logging_manager = get_logging_manager()
    logging_manager.setup_logging()
    logger = logging.getLogger(__name__)
except ModuleNotFoundError:
    try:
        from src.codexes.modules.finance.leo_bloom.integrations.imprint_finance_integration import ImprintFinanceIntegration
        from src.codexes.core.logging_config import get_logging_manager

        # Set up logging
        logging_manager = get_logging_manager()
        logging_manager.setup_logging()
        logger = logging.getLogger(__name__)
    except ModuleNotFoundError:
        # Fallback
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        # Mock for fallback
        class ImprintFinanceIntegration:
            pass


class ImprintFinancialDashboard:
    """
    Streamlit dashboard for imprint-specific financial reporting and analysis.
    """

    def __init__(self, root_path: Optional[str] = None):
        """Initialize the dashboard."""
        self.root_path = root_path
        self.integration: Optional[ImprintFinanceIntegration] = None
        self._initialize_integration()

    def _initialize_integration(self) -> None:
        """Initialize the imprint-finance integration."""
        try:
            self.integration = ImprintFinanceIntegration(self.root_path)
            self.integration.load_imprint_configurations()
            self.integration.initialize_financial_reporting()
            logger.info("Initialized ImprintFinancialDashboard")
        except Exception as e:
            logger.error(f"Failed to initialize integration: {e}")
            st.error(f"Failed to initialize imprint financial integration: {e}")

    def show_dashboard(self) -> None:
        """Display the main imprint financial dashboard."""
        if not self.integration:
            st.error("❌ Dashboard initialization failed")
            return

        # Header
        st.title("📊 Imprint Financial Dashboard")
        st.markdown("**Comprehensive financial reporting by imprint**")

        # Validation check
        validation = self.integration.validate_integration()
        if validation['integration_status'] != 'healthy':
            with st.expander("⚠️ Integration Status", expanded=True):
                st.warning(f"Status: {validation['integration_status']}")
                if validation['issues']:
                    for issue in validation['issues']:
                        st.write(f"• {issue}")

        # Sidebar - Imprint Selection
        self._show_imprint_selector()

        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Individual Imprint",
            "🔍 Comparative Analysis",
            "📋 All Imprints Overview",
            "⚙️ Settings & Export"
        ])

        with tab1:
            self._show_individual_imprint_analysis()

        with tab2:
            self._show_comparative_analysis()

        with tab3:
            self._show_all_imprints_overview()

        with tab4:
            self._show_settings_and_export()

    def _show_imprint_selector(self) -> None:
        """Show imprint selection in sidebar."""
        st.sidebar.header("🎯 Imprint Selection")

        available_imprints = self.integration.get_available_imprints()

        if not available_imprints:
            st.sidebar.warning("No imprints with configurations found")
            return

        # Single imprint selector
        selected_imprint = st.sidebar.selectbox(
            "Select Imprint for Analysis:",
            options=available_imprints,
            key="selected_imprint"
        )

        # Multi-select for comparative analysis
        selected_imprints_multi = st.sidebar.multiselect(
            "Select Multiple Imprints for Comparison:",
            options=available_imprints,
            default=available_imprints[:3] if len(available_imprints) >= 3 else available_imprints,
            key="selected_imprints_multi"
        )

        # Cache refresh
        if st.sidebar.button("🔄 Refresh Data"):
            self.integration.clear_cache()
            st.rerun()

        # Display integration status
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Integration Status:**")
        validation = self.integration.validate_integration()
        st.sidebar.success(f"Configs: {validation['imprint_configs_loaded']}")
        st.sidebar.success(f"Financial Data: {'✅' if validation['financial_data_available'] else '❌'}")

    def _show_individual_imprint_analysis(self) -> None:
        """Show detailed analysis for a single imprint."""
        selected_imprint = st.session_state.get("selected_imprint")

        if not selected_imprint:
            st.info("👈 Please select an imprint from the sidebar")
            return

        st.header(f"📊 Financial Analysis: {selected_imprint}")

        # Get financial data and summary
        financial_data = self.integration.get_imprint_financial_data(selected_imprint)
        summary = self.integration.generate_imprint_financial_summary(selected_imprint)

        if financial_data is None or financial_data.empty:
            st.warning(f"No financial data available for {selected_imprint}")
            return

        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_revenue = summary.get('financial_metrics', {}).get('total_revenue', 0)
            st.metric("Total Revenue", f"${total_revenue:,.2f}")

        with col2:
            total_units = summary.get('sales_metrics', {}).get('total_units_sold', 0)
            st.metric("Units Sold", f"{total_units:,}")

        with col3:
            avg_revenue = summary.get('financial_metrics', {}).get('avg_revenue_per_title', 0)
            st.metric("Avg Revenue/Title", f"${avg_revenue:.2f}")

        with col4:
            title_count = summary.get('records_count', 0)
            st.metric("Active Titles", f"{title_count:,}")

        # Charts section
        st.subheader("📈 Performance Charts")

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Revenue by title chart
            if 'Net Compensation' in financial_data.columns and 'Title' in financial_data.columns:
                top_titles = financial_data.nlargest(10, 'Net Compensation')
                fig_revenue = px.bar(
                    top_titles,
                    x='Net Compensation',
                    y='Title',
                    orientation='h',
                    title="Top 10 Titles by Revenue",
                    labels={'Net Compensation': 'Revenue ($)', 'Title': 'Book Title'}
                )
                fig_revenue.update_layout(height=400)
                st.plotly_chart(fig_revenue, use_container_width=True)

        with chart_col2:
            # Units sold by title chart
            if 'Net Qty' in financial_data.columns and 'Title' in financial_data.columns:
                top_units = financial_data.nlargest(10, 'Net Qty')
                fig_units = px.bar(
                    top_units,
                    x='Net Qty',
                    y='Title',
                    orientation='h',
                    title="Top 10 Titles by Units Sold",
                    labels={'Net Qty': 'Units Sold', 'Title': 'Book Title'}
                )
                fig_units.update_layout(height=400)
                st.plotly_chart(fig_units, use_container_width=True)

        # Configuration information
        with st.expander("⚙️ Imprint Configuration", expanded=False):
            config_info = summary.get('configuration_info', {})
            if config_info:
                config_col1, config_col2 = st.columns(2)

                with config_col1:
                    st.write("**Lightning Source Account:**", config_info.get('lightning_source_account', 'Not configured'))
                    st.write("**Default Wholesale Discount:**", config_info.get('default_wholesale_discount', 'Not configured'))

                with config_col2:
                    st.write("**Territorial Markets:**", ', '.join(config_info.get('territorial_markets', [])))
                    st.write("**Primary Genres:**", ', '.join(config_info.get('primary_genres', [])))

        # Detailed data table
        with st.expander("📋 Detailed Financial Data", expanded=False):
            # Add filters
            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                min_revenue = st.number_input("Minimum Revenue", value=0.0, step=10.0)

            with filter_col2:
                min_units = st.number_input("Minimum Units", value=0, step=1)

            # Filter the data
            filtered_data = financial_data[
                (financial_data.get('Net Compensation', 0) >= min_revenue) &
                (financial_data.get('Net Qty', 0) >= min_units)
            ]

            st.dataframe(filtered_data, use_container_width=True)

            # Download link
            csv = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{selected_imprint.lower().replace(' ', '_')}_financial_data.csv",
                mime="text/csv"
            )

    def _show_comparative_analysis(self) -> None:
        """Show comparative analysis across multiple imprints."""
        st.header("🔍 Comparative Analysis")

        selected_imprints = st.session_state.get("selected_imprints_multi", [])

        if len(selected_imprints) < 2:
            st.info("👈 Please select at least 2 imprints from the sidebar for comparison")
            return

        # Get comparative analysis
        comparison = self.integration.get_comparative_analysis(selected_imprints)

        # Metrics comparison
        st.subheader("📊 Key Metrics Comparison")

        metrics_to_show = ['total_revenue', 'total_units', 'title_count']

        for metric in metrics_to_show:
            metric_data = comparison['metrics'].get(metric, {})
            if metric_data:
                st.write(f"**{metric.replace('_', ' ').title()}:**")

                # Create horizontal bar chart
                df_metric = pd.DataFrame(list(metric_data.items()), columns=['Imprint', 'Value'])
                df_metric = df_metric.sort_values('Value', ascending=True)

                fig = px.bar(
                    df_metric,
                    x='Value',
                    y='Imprint',
                    orientation='h',
                    title=f"{metric.replace('_', ' ').title()} by Imprint"
                )
                st.plotly_chart(fig, use_container_width=True)

        # Rankings
        st.subheader("🏆 Performance Rankings")

        ranking_col1, ranking_col2 = st.columns(2)

        with ranking_col1:
            revenue_ranking = comparison.get('rankings', {}).get('total_revenue', [])
            if revenue_ranking:
                st.write("**Revenue Ranking:**")
                for i, item in enumerate(revenue_ranking, 1):
                    st.write(f"{i}. {item['imprint']}: ${item['value']:,.2f}")

        with ranking_col2:
            units_ranking = comparison.get('rankings', {}).get('total_units', [])
            if units_ranking:
                st.write("**Units Sold Ranking:**")
                for i, item in enumerate(units_ranking, 1):
                    st.write(f"{i}. {item['imprint']}: {item['value']:,}")

        # Territorial presence
        st.subheader("🌍 Territorial Presence")
        territorial_data = comparison.get('territorial_presence', {})
        if territorial_data:
            # Create a presence matrix
            all_territories = set()
            for territories in territorial_data.values():
                all_territories.update(territories)

            presence_matrix = []
            for imprint, territories in territorial_data.items():
                row = {'Imprint': imprint}
                for territory in all_territories:
                    row[territory] = '✅' if territory in territories else '❌'
                presence_matrix.append(row)

            if presence_matrix:
                df_presence = pd.DataFrame(presence_matrix)
                st.dataframe(df_presence, use_container_width=True)

    def _show_all_imprints_overview(self) -> None:
        """Show overview of all imprints."""
        st.header("📋 All Imprints Overview")

        # Get summaries for all imprints
        all_summaries = self.integration.get_all_imprints_summary()

        if not all_summaries:
            st.warning("No imprint data available")
            return

        # Create overview table
        overview_data = []
        for imprint_name, summary in all_summaries.items():
            if 'error' not in summary:
                overview_data.append({
                    'Imprint': imprint_name,
                    'Total Revenue': summary.get('financial_metrics', {}).get('total_revenue', 0),
                    'Units Sold': summary.get('sales_metrics', {}).get('total_units_sold', 0),
                    'Active Titles': summary.get('records_count', 0),
                    'Avg Revenue/Title': summary.get('financial_metrics', {}).get('avg_revenue_per_title', 0)
                })

        if overview_data:
            df_overview = pd.DataFrame(overview_data)

            # Sort by total revenue
            df_overview = df_overview.sort_values('Total Revenue', ascending=False)

            # Format columns
            df_overview['Total Revenue'] = df_overview['Total Revenue'].apply(lambda x: f"${x:,.2f}")
            df_overview['Units Sold'] = df_overview['Units Sold'].apply(lambda x: f"{x:,}")
            df_overview['Avg Revenue/Title'] = df_overview['Avg Revenue/Title'].apply(lambda x: f"${x:.2f}")

            st.dataframe(df_overview, use_container_width=True)

            # Summary statistics
            st.subheader("📈 Portfolio Summary")

            summary_col1, summary_col2, summary_col3 = st.columns(3)

            with summary_col1:
                total_imprints = len(overview_data)
                st.metric("Total Imprints", total_imprints)

            with summary_col2:
                total_portfolio_revenue = sum(item['Total Revenue'] for item in overview_data)
                st.metric("Portfolio Revenue", f"${total_portfolio_revenue:,.2f}")

            with summary_col3:
                total_portfolio_units = sum(item['Units Sold'] for item in overview_data)
                st.metric("Portfolio Units", f"{total_portfolio_units:,}")

        else:
            st.warning("No financial data available for any imprints")

    def _show_settings_and_export(self) -> None:
        """Show settings and export options."""
        st.header("⚙️ Settings & Export")

        # Export section
        st.subheader("📤 Export Options")

        selected_imprint = st.session_state.get("selected_imprint")

        if selected_imprint:
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Export Individual Report"):
                    with st.spinner("Generating report..."):
                        output_path = self.integration.export_imprint_report(selected_imprint)
                        if output_path:
                            st.success(f"Report exported to: {output_path}")
                        else:
                            st.error("Failed to export report")

            with col2:
                if st.button("📋 Export All Imprints Summary"):
                    with st.spinner("Generating summary..."):
                        all_summaries = self.integration.get_all_imprints_summary()
                        # Convert to DataFrame and export
                        summary_data = []
                        for name, summary in all_summaries.items():
                            if 'error' not in summary:
                                summary_data.append({
                                    'Imprint': name,
                                    'Records': summary.get('records_count', 0),
                                    'Revenue': summary.get('financial_metrics', {}).get('total_revenue', 0),
                                    'Units': summary.get('sales_metrics', {}).get('total_units_sold', 0)
                                })

                        if summary_data:
                            df_summary = pd.DataFrame(summary_data)
                            csv = df_summary.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Summary CSV",
                                data=csv,
                                file_name="all_imprints_summary.csv",
                                mime="text/csv"
                            )

        # Integration status
        st.subheader("🔍 Integration Status")
        validation = self.integration.validate_integration()

        status_color = {
            'healthy': 'success',
            'warning': 'warning',
            'error': 'error'
        }.get(validation['integration_status'], 'info')

        getattr(st, status_color)(f"Status: {validation['integration_status']}")

        # Detailed status
        with st.expander("📋 Detailed Status", expanded=False):
            st.json(validation)

        # Cache management
        st.subheader("🗄️ Cache Management")
        if st.button("🔄 Clear All Caches"):
            self.integration.clear_cache()
            st.success("Caches cleared successfully")


def show_imprint_financial_dashboard():
    """Entry point for the imprint financial dashboard."""
    dashboard = ImprintFinancialDashboard()
    dashboard.show_dashboard()


if __name__ == "__main__":
    show_imprint_financial_dashboard()