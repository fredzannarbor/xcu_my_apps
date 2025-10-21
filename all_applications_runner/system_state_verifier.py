#!/usr/bin/env python3
"""
System State Verification Module

Verifies that all apps comply with system architecture requirements:
1. Shared authentication across all apps
2. Unified sidebar with consistent platform info
3. UV workspace dependency inheritance
4. Shared dotenv environment variables
5. Correct GCP domain→port mappings
"""

import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import toml
import requests

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of a verification check."""
    check_name: str
    passed: bool
    severity: str  # "critical", "warning", "info"
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    fix_suggestion: Optional[str] = None


@dataclass
class AppStateReport:
    """Complete state report for an app."""
    org_id: str
    app_id: str
    app_name: str
    port: int
    domain_name: Optional[str]
    results: List[VerificationResult] = field(default_factory=list)

    @property
    def has_critical_issues(self) -> bool:
        return any(r.severity == "critical" and not r.passed for r in self.results)

    @property
    def has_warnings(self) -> bool:
        return any(r.severity == "warning" and not r.passed for r in self.results)

    @property
    def compliance_score(self) -> float:
        """Calculate compliance score (0-100)."""
        if not self.results:
            return 0.0
        passed = sum(1 for r in self.results if r.passed)
        return (passed / len(self.results)) * 100


class SystemStateVerifier:
    """Verifies system state compliance across all apps."""

    def __init__(self, config_path: str = "apps_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

        # Auto-detect environment: use current working directory's parent as workspace root
        # This works on both Mac (/Users/fred/xcu_my_apps) and Linux (/home/wfzimmerman/xcu_my_apps)
        if Path.cwd().name == "all_applications_runner":
            self.workspace_root = Path.cwd().parent
        else:
            self.workspace_root = Path("/Users/fred/xcu_my_apps")
        self.shared_path = self.workspace_root / "shared"

    def _load_config(self) -> Dict[str, Any]:
        """Load apps configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def verify_all_apps(self) -> List[AppStateReport]:
        """Verify all apps and return reports."""
        reports = []

        for org_id, org_config in self.config.get("organizations", {}).items():
            for app_id, app_config in org_config.get("apps", {}).items():
                report = self.verify_app(org_id, app_id, app_config)
                reports.append(report)

        return reports

    def verify_app(self, org_id: str, app_id: str, app_config: Dict[str, Any]) -> AppStateReport:
        """Verify a single app against all requirements."""
        report = AppStateReport(
            org_id=org_id,
            app_id=app_id,
            app_name=app_config.get("name", app_id),
            port=app_config.get("port"),
            domain_name=app_config.get("domain_name")
        )

        # Convert Mac paths to current environment paths
        raw_path = app_config.get("path", "")
        if raw_path.startswith("/Users/fred/xcu_my_apps/"):
            # Replace Mac path prefix with workspace root
            relative_path = raw_path.replace("/Users/fred/xcu_my_apps/", "")
            app_path = self.workspace_root / relative_path
        else:
            app_path = Path(raw_path)

        entry_file = app_config.get("entry", "")

        # Run all verification checks
        report.results.append(self._check_shared_auth(app_path, entry_file, app_id))
        report.results.append(self._check_unified_sidebar(app_path, app_id))
        report.results.append(self._check_uv_workspace(app_path, app_id))
        report.results.append(self._check_dotenv_sharing(app_path, app_id))
        report.results.append(self._check_domain_mapping(app_config, org_id, app_id))
        report.results.append(self._check_port_binding(app_config, app_id))
        report.results.append(self._check_health_endpoint(app_config, app_id))

        return report

    def _check_shared_auth(self, app_path: Path, entry_file: str, app_id: str) -> VerificationResult:
        """Verify app uses shared authentication system."""
        check_name = "Shared Authentication"

        if not app_path.exists():
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="critical",
                message=f"App path does not exist: {app_path}",
                fix_suggestion="Verify app path in apps_config.json"
            )

        # Check the entry file specifically
        entry_path = app_path / entry_file
        uses_shared_auth = False

        if entry_path.exists():
            try:
                content = entry_path.read_text()
                if "from shared.auth import" in content or "from shared.auth.shared_auth import" in content:
                    uses_shared_auth = True
            except Exception as e:
                pass

        # If not found in entry file, scan other Python files as fallback
        if not uses_shared_auth:
            py_files = list(app_path.rglob("*.py"))
            for py_file in py_files[:50]:  # Check up to 50 files
                try:
                    content = py_file.read_text()
                    if "from shared.auth import" in content or "from shared.auth.shared_auth import" in content:
                        uses_shared_auth = True
                        entry_file = py_file.name
                        break
                except Exception:
                    continue

        if uses_shared_auth:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="critical",
                message=f"✓ Uses shared auth (found in {entry_file})",
                details={"entry_file": entry_file}
            )
        else:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="critical",
                message="✗ Does not import shared.auth",
                fix_suggestion=f"Add 'from shared.auth import get_shared_auth, is_authenticated' to app entry file ({entry_file})",
                details={"entry_file": entry_file}
            )

    def _check_unified_sidebar(self, app_path: Path, app_id: str) -> VerificationResult:
        """Verify app uses unified sidebar component."""
        check_name = "Unified Sidebar"

        if not app_path.exists():
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="Cannot verify - app path not found"
            )

        # Check if app imports shared.ui
        py_files = list(app_path.rglob("*.py"))
        uses_unified_sidebar = False
        entry_file = None

        for py_file in py_files[:50]:
            try:
                content = py_file.read_text()
                if "from shared.ui import" in content or "render_unified_sidebar" in content:
                    uses_unified_sidebar = True
                    entry_file = py_file.name
                    break
            except Exception:
                continue

        if uses_unified_sidebar:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="warning",
                message=f"✓ Uses unified sidebar (found in {entry_file})"
            )
        else:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="✗ Does not use unified sidebar",
                fix_suggestion="Add 'from shared.ui import render_unified_sidebar' to app"
            )

    def _check_uv_workspace(self, app_path: Path, app_id: str) -> VerificationResult:
        """Verify app is in UV workspace and inherits dependencies."""
        check_name = "UV Workspace"

        # Check if app has pyproject.toml
        pyproject_path = app_path / "pyproject.toml"

        # Check workspace root for workspace definition
        workspace_pyproject = self.workspace_root / "pyproject.toml"

        if not workspace_pyproject.exists():
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="✗ No workspace pyproject.toml found at root",
                fix_suggestion="Create workspace pyproject.toml with [tool.uv.workspace]"
            )

        try:
            workspace_config = toml.load(workspace_pyproject)
            workspace_members = workspace_config.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])

            # Check if app path is in workspace members
            app_relative = str(app_path.relative_to(self.workspace_root))
            in_workspace = any(app_relative.startswith(member.rstrip("/*")) for member in workspace_members)

            if in_workspace:
                # Check if app has its own pyproject or relies on workspace
                if pyproject_path.exists():
                    app_config = toml.load(pyproject_path)
                    has_dependencies = "dependencies" in app_config.get("project", {})

                    return VerificationResult(
                        check_name=check_name,
                        passed=True,
                        severity="info",
                        message=f"✓ In UV workspace with {'own' if has_dependencies else 'inherited'} dependencies",
                        details={"has_own_deps": has_dependencies}
                    )
                else:
                    return VerificationResult(
                        check_name=check_name,
                        passed=True,
                        severity="info",
                        message="✓ In UV workspace, inherits all dependencies"
                    )
            else:
                return VerificationResult(
                    check_name=check_name,
                    passed=False,
                    severity="warning",
                    message="✗ Not in UV workspace members",
                    fix_suggestion=f"Add '{app_relative}' to workspace.members in root pyproject.toml"
                )
        except Exception as e:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message=f"✗ Error checking workspace: {str(e)}"
            )

    def _check_dotenv_sharing(self, app_path: Path, app_id: str) -> VerificationResult:
        """Verify app uses shared .env or has documented overrides."""
        check_name = "Environment Variables"

        # Check for master .env
        master_env = self.workspace_root / ".env"
        app_env = app_path / ".env"

        has_master = master_env.exists()
        has_app_env = app_env.exists()

        if has_master and not has_app_env:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="info",
                message="✓ Uses master .env (no app override)"
            )
        elif has_master and has_app_env:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="info",
                message="✓ Uses master .env + app-specific overrides",
                details={"has_override": True}
            )
        elif has_app_env:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="warning",
                message="⚠ Uses app-specific .env only (no master)",
                details={"has_override": True}
            )
        else:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="✗ No .env file found",
                fix_suggestion="Create master .env or app-specific .env"
            )

    def _check_domain_mapping(self, app_config: Dict[str, Any], org_id: str, app_id: str) -> VerificationResult:
        """Verify domain name matches expected GCP mapping."""
        check_name = "GCP Domain Mapping"

        port = app_config.get("port")
        domain_name = app_config.get("domain_name")

        # Expected mappings based on your configuration
        expected_mappings = {
            8500: "xtuff.ai",
            8501: "social.xtuff.ai",
            8502: "codexes.nimblebooks.com",
            8504: "trillionsofpeople.info",
            8509: "dailyengine.xtuff.ai",
            8512: "resume.xtuff.ai",
        }

        expected_domain = expected_mappings.get(port)

        if not domain_name:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="✗ No domain_name configured",
                fix_suggestion=f"Add 'domain_name' to app config (expected: {expected_domain})" if expected_domain else "Add 'domain_name' to app config"
            )

        if expected_domain and domain_name != expected_domain:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="critical",
                message=f"✗ Domain mismatch: {domain_name} (expected: {expected_domain})",
                fix_suggestion=f"Update domain_name to '{expected_domain}' in apps_config.json",
                details={"configured": domain_name, "expected": expected_domain}
            )

        return VerificationResult(
            check_name=check_name,
            passed=True,
            severity="info",
            message=f"✓ Domain correctly mapped: {domain_name} → port {port}",
            details={"domain": domain_name, "port": port}
        )

    def _check_port_binding(self, app_config: Dict[str, Any], app_id: str) -> VerificationResult:
        """Verify app is configured to bind to 0.0.0.0 for GCP access."""
        check_name = "Port Binding (0.0.0.0)"

        startup_command = app_config.get("startup_command", "")

        # Check if command specifies server address
        if "--server.address=0.0.0.0" in startup_command:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="critical",
                message="✓ Configured to bind to 0.0.0.0"
            )
        elif "--server.address" in startup_command:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="critical",
                message="✗ Binds to non-0.0.0.0 address",
                fix_suggestion="Change --server.address to 0.0.0.0 in startup_command"
            )
        else:
            # Streamlit defaults to localhost, which won't work with GCP load balancer
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="critical",
                message="✗ No explicit binding (defaults to localhost)",
                fix_suggestion="Add '--server.address=0.0.0.0' to startup_command"
            )

    def _check_health_endpoint(self, app_config: Dict[str, Any], app_id: str) -> VerificationResult:
        """Verify health endpoint is configured for GCP health checks."""
        check_name = "Health Endpoint"

        health_endpoint = app_config.get("health_endpoint", "/")

        if health_endpoint:
            return VerificationResult(
                check_name=check_name,
                passed=True,
                severity="info",
                message=f"✓ Health endpoint configured: {health_endpoint}",
                details={"endpoint": health_endpoint}
            )
        else:
            return VerificationResult(
                check_name=check_name,
                passed=False,
                severity="warning",
                message="✗ No health endpoint configured",
                fix_suggestion="Add 'health_endpoint' to app config (typically '/' or '/health')"
            )

    def get_system_summary(self, reports: List[AppStateReport]) -> Dict[str, Any]:
        """Generate system-wide summary statistics."""
        total_apps = len(reports)
        apps_with_critical = sum(1 for r in reports if r.has_critical_issues)
        apps_with_warnings = sum(1 for r in reports if r.has_warnings)
        fully_compliant = sum(1 for r in reports if not r.has_critical_issues and not r.has_warnings)

        avg_compliance = sum(r.compliance_score for r in reports) / total_apps if total_apps > 0 else 0

        # Check-specific statistics
        check_stats = {}
        all_checks = set()
        for report in reports:
            for result in report.results:
                all_checks.add(result.check_name)

        for check_name in all_checks:
            passed = sum(1 for r in reports for result in r.results if result.check_name == check_name and result.passed)
            total = sum(1 for r in reports for result in r.results if result.check_name == check_name)
            check_stats[check_name] = {
                "passed": passed,
                "failed": total - passed,
                "total": total,
                "pass_rate": (passed / total * 100) if total > 0 else 0
            }

        return {
            "total_apps": total_apps,
            "fully_compliant": fully_compliant,
            "apps_with_critical_issues": apps_with_critical,
            "apps_with_warnings": apps_with_warnings,
            "average_compliance_score": round(avg_compliance, 1),
            "check_statistics": check_stats
        }

    def auto_fix_app(self, org_id: str, app_id: str, app_config: Dict[str, Any]) -> List[str]:
        """Attempt to automatically fix common issues."""
        fixes_applied = []
        app_path = Path(app_config.get("path", ""))

        # Fix 1: Add --server.address=0.0.0.0 if missing
        startup_command = app_config.get("startup_command", "")
        if "--server.address" not in startup_command and "streamlit run" in startup_command:
            # Update in config
            new_command = startup_command.replace(
                "streamlit run",
                "streamlit run --server.address=0.0.0.0"
            )
            app_config["startup_command"] = new_command
            fixes_applied.append(f"Added --server.address=0.0.0.0 to startup command")

        # Fix 2: Ensure health_endpoint exists
        if "health_endpoint" not in app_config:
            app_config["health_endpoint"] = "/"
            fixes_applied.append("Added default health_endpoint: /")

        return fixes_applied


def main():
    """CLI for system state verification."""
    logging.basicConfig(level=logging.INFO)

    verifier = SystemStateVerifier()
    print("\n" + "="*80)
    print("SYSTEM STATE VERIFICATION REPORT")
    print("="*80 + "\n")

    reports = verifier.verify_all_apps()

    for report in reports:
        status_icon = "✓" if not report.has_critical_issues else "✗"
        print(f"\n{status_icon} {report.app_name} ({report.org_id}.{report.app_id})")
        print(f"   Port: {report.port} | Domain: {report.domain_name or 'N/A'}")
        print(f"   Compliance Score: {report.compliance_score:.1f}%")

        for result in report.results:
            if not result.passed:
                icon = "🔴" if result.severity == "critical" else "🟡"
                print(f"   {icon} {result.message}")
                if result.fix_suggestion:
                    print(f"      → Fix: {result.fix_suggestion}")

    # Summary
    summary = verifier.get_system_summary(reports)
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total Apps: {summary['total_apps']}")
    print(f"Fully Compliant: {summary['fully_compliant']}")
    print(f"With Critical Issues: {summary['apps_with_critical_issues']}")
    print(f"With Warnings: {summary['apps_with_warnings']}")
    print(f"Average Compliance: {summary['average_compliance_score']:.1f}%\n")

    print("Check Pass Rates:")
    for check_name, stats in summary['check_statistics'].items():
        print(f"  {check_name}: {stats['passed']}/{stats['total']} ({stats['pass_rate']:.1f}%)")


if __name__ == "__main__":
    main()
