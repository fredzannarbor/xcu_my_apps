#!/usr/bin/env python3
"""
Apache Reverse Proxy Configuration Generator for Unified App Runner

Generates Apache configuration for reverse proxy setup in production.
"""

import json
from pathlib import Path
from typing import Dict, Any

class ApacheConfigGenerator:
    """Generates Apache configuration for the app runner system."""

    def __init__(self, config_path: str = "../apps_config.json"):
        self.config_path = Path(__file__).parent / config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load the application configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration: {e}")

    def generate_virtualhost_config(self, domain: str = "your-domain.com",
                                  ssl_enabled: bool = False) -> str:
        """Generate Apache VirtualHost configuration."""

        config_lines = []

        # SSL or non-SSL configuration
        if ssl_enabled:
            config_lines.extend([
                f"<VirtualHost *:443>",
                f"    ServerName {domain}",
                f"    DocumentRoot /var/www/html",
                f"",
                f"    SSLEngine on",
                f"    SSLCertificateFile /etc/ssl/certs/{domain}.crt",
                f"    SSLCertificateKeyFile /etc/ssl/private/{domain}.key",
                f"    # SSLCertificateChainFile /etc/ssl/certs/intermediate.crt",
                f"",
            ])
        else:
            config_lines.extend([
                f"<VirtualHost *:80>",
                f"    ServerName {domain}",
                f"    DocumentRoot /var/www/html",
                f"",
            ])

        # Add proxy configuration
        config_lines.extend([
            f"    # Enable proxy modules",
            f"    ProxyPreserveHost On",
            f"    ProxyRequests Off",
            f"",
            f"    # Main app runner dashboard",
            f"    ProxyPass / http://localhost:8500/",
            f"    ProxyPassReverse / http://localhost:8500/",
            f"",
            f"    # Organization-specific routing",
        ])

        # Generate routes for each organization and app
        organizations = self.config.get("organizations", {})

        for org_id, org_config in organizations.items():
            org_name = org_config.get("name", org_id)
            config_lines.append(f"    # {org_name}")

            apps = org_config.get("apps", {})
            for app_id, app_config in apps.items():
                app_name = app_config.get("name", app_id)
                port = app_config.get("port")

                # Create route: /org/app/ -> localhost:port/
                route_path = f"/{org_id}/{app_id}/"
                upstream_url = f"http://localhost:{port}/"

                config_lines.extend([
                    f"    # {app_name}",
                    f"    ProxyPass {route_path} {upstream_url}",
                    f"    ProxyPassReverse {route_path} {upstream_url}",
                    f"",
                ])

        # Add security and logging
        config_lines.extend([
            f"    # Security headers",
            f"    Header always set X-Frame-Options DENY",
            f"    Header always set X-Content-Type-Options nosniff",
            f"    Header always set X-XSS-Protection \"1; mode=block\"",
            f"    Header always set Strict-Transport-Security \"max-age=63072000; includeSubDomains; preload\"",
            f"",
            f"    # Logging",
            f"    ErrorLog ${{APACHE_LOG_DIR}}/{domain}_error.log",
            f"    CustomLog ${{APACHE_LOG_DIR}}/{domain}_access.log combined",
            f"",
            f"    # Optional: Redirect HTTP to HTTPS",
        ])

        if ssl_enabled:
            config_lines.append(f"    # (SSL configuration already enabled above)")
        else:
            config_lines.extend([
                f"    # Uncomment to redirect HTTP to HTTPS:",
                f"    # Redirect permanent / https://{domain}/",
            ])

        config_lines.extend([
            f"",
            f"</VirtualHost>",
        ])

        # Add HTTP to HTTPS redirect if SSL is enabled
        if ssl_enabled:
            config_lines.extend([
                f"",
                f"# HTTP to HTTPS redirect",
                f"<VirtualHost *:80>",
                f"    ServerName {domain}",
                f"    Redirect permanent / https://{domain}/",
                f"</VirtualHost>",
            ])

        return "\n".join(config_lines)

    def generate_modules_config(self) -> str:
        """Generate required Apache modules configuration."""
        modules = [
            "mod_proxy",
            "mod_proxy_http",
            "mod_headers",
            "mod_rewrite",
            "mod_ssl"  # if SSL is used
        ]

        config_lines = [
            "# Required Apache modules for Fred's App Runner",
            "# Add these to your Apache configuration",
            "",
            "LoadModule proxy_module modules/mod_proxy.so",
            "LoadModule proxy_http_module modules/mod_proxy_http.so",
            "LoadModule headers_module modules/mod_headers.so",
            "LoadModule rewrite_module modules/mod_rewrite.so",
            "LoadModule ssl_module modules/mod_ssl.so",
            "",
            "# Alternative: Enable with a2enmod on Debian/Ubuntu:",
            "# a2enmod proxy",
            "# a2enmod proxy_http",
            "# a2enmod headers",
            "# a2enmod rewrite",
            "# a2enmod ssl",
        ]

        return "\n".join(config_lines)

    def generate_systemd_services(self) -> Dict[str, str]:
        """Generate systemd service files for Linux deployment."""
        services = {}

        # Master app runner service
        master_service = f"""[Unit]
Description=Fred's Unified App Runner - Master Dashboard
After=network.target
Wants=app-runner-manager.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/home/wfz/app-runner
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/wfz/app-runner
ExecStart=/usr/bin/python3 -c "import streamlit.web.cli as stcli; import sys; sys.argv = ['streamlit', 'run', 'main.py', '--server.port=8500', '--server.address=127.0.0.1']; stcli.main()"
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""

        services["app-runner-master.service"] = master_service

        # Process manager service
        manager_service = f"""[Unit]
Description=Fred's App Runner - Process Manager
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/home/wfz/app-runner
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/wfz/app-runner
ExecStart=/usr/bin/python3 process_manager.py --action start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""

        services["app-runner-manager.service"] = manager_service

        # Individual app services
        organizations = self.config.get("organizations", {})

        for org_id, org_config in organizations.items():
            apps = org_config.get("apps", {})

            for app_id, app_config in apps.items():
                service_name = f"app-{org_id}-{app_id}.service"
                app_name = app_config.get("name", app_id)
                port = app_config.get("port")
                path = app_config.get("path", "").replace("/Users/fred/my-organizations", "/home/wfz")
                startup_command = app_config.get("startup_command", "")

                # Adapt startup command for Linux
                if "uv run python" in startup_command:
                    exec_start = startup_command.replace("uv run python", "/usr/bin/python3")
                elif "streamlit run" in startup_command:
                    exec_start = f"/usr/bin/python3 -m streamlit run {startup_command.split('streamlit run')[1]}"
                else:
                    exec_start = startup_command

                app_service = f"""[Unit]
Description={app_name} - {org_config.get('name', org_id)}
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory={path}
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH={path}
ExecStart={exec_start}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target"""

                services[service_name] = app_service

        return services

    def generate_deployment_script(self) -> str:
        """Generate a deployment script for Linux production."""
        script_lines = [
            "#!/bin/bash",
            "# Deployment script for Fred's Unified App Runner",
            "# Run as root or with sudo",
            "",
            "set -e",
            "",
            "echo \"Deploying Fred's Unified App Runner...\"",
            "",
            "# Variables",
            "APP_USER=\"www-data\"",
            "APP_DIR=\"/home/wfz/app-runner\"",
            "APACHE_SITES_DIR=\"/etc/apache2/sites-available\"",
            "SYSTEMD_DIR=\"/etc/systemd/system\"",
            "",
            "# Create app directory if it doesn't exist",
            "if [ ! -d \"$APP_DIR\" ]; then",
            "    echo \"Creating app directory: $APP_DIR\"",
            "    mkdir -p \"$APP_DIR\"",
            "    chown $APP_USER:$APP_USER \"$APP_DIR\"",
            "fi",
            "",
            "# Install Python dependencies",
            "echo \"Installing system dependencies...\"",
            "apt-get update",
            "apt-get install -y python3 python3-pip python3-venv apache2",
            "",
            "# Enable required Apache modules",
            "echo \"Enabling Apache modules...\"",
            "a2enmod proxy",
            "a2enmod proxy_http",
            "a2enmod headers",
            "a2enmod rewrite",
            "a2enmod ssl",
            "",
            "# Copy application files",
            "echo \"Copying application files...\"",
            "# Note: Assumes files are already in $APP_DIR via git pull",
            "",
            "# Install Python dependencies",
            "cd \"$APP_DIR\"",
            "if [ -f \"requirements.txt\" ]; then",
            "    pip3 install -r requirements.txt",
            "fi",
            "",
            "# Install systemd services",
            "echo \"Installing systemd services...\"",
            "python3 deployment/apache_config.py generate-systemd",
            "",
            "# Copy Apache configuration",
            "echo \"Installing Apache configuration...\"",
            "python3 deployment/apache_config.py generate-apache > \"$APACHE_SITES_DIR/app-runner.conf\"",
            "",
            "# Enable the site",
            "a2ensite app-runner",
            "a2dissite 000-default  # Optional: disable default site",
            "",
            "# Reload Apache",
            "systemctl reload apache2",
            "",
            "# Start and enable services",
            "echo \"Starting services...\"",
            "systemctl daemon-reload",
            "systemctl enable app-runner-master.service",
            "systemctl enable app-runner-manager.service",
            "systemctl start app-runner-master.service",
            "systemctl start app-runner-manager.service",
            "",
            "echo \"Deployment complete!\"",
            "echo \"\"",
            "echo \"Services status:\"",
            "systemctl status app-runner-master.service --no-pager",
            "systemctl status app-runner-manager.service --no-pager",
            "",
            "echo \"\"",
            "echo \"Access the application at: http://your-domain.com\"",
            "echo \"Configure DNS to point to this server\"",
        ]

        return "\n".join(script_lines)

    def save_configs(self, output_dir: Path = None):
        """Save all generated configurations to files."""
        if output_dir is None:
            output_dir = Path(__file__).parent / "generated"

        output_dir.mkdir(exist_ok=True)

        # Generate and save Apache config
        apache_config = self.generate_virtualhost_config()
        (output_dir / "apache-virtualhost.conf").write_text(apache_config)

        # Generate and save modules config
        modules_config = self.generate_modules_config()
        (output_dir / "apache-modules.conf").write_text(modules_config)

        # Generate and save systemd services
        systemd_services = self.generate_systemd_services()
        systemd_dir = output_dir / "systemd"
        systemd_dir.mkdir(exist_ok=True)

        for service_name, service_content in systemd_services.items():
            (systemd_dir / service_name).write_text(service_content)

        # Generate and save deployment script
        deploy_script = self.generate_deployment_script()
        deploy_script_path = output_dir / "deploy-linux.sh"
        deploy_script_path.write_text(deploy_script)
        deploy_script_path.chmod(0o755)

        print(f"Configuration files generated in: {output_dir}")
        print("\nGenerated files:")
        print(f"  - apache-virtualhost.conf")
        print(f"  - apache-modules.conf")
        print(f"  - systemd/ (service files)")
        print(f"  - deploy-linux.sh")

def main():
    """Main CLI for Apache configuration generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Apache Configuration Generator")
    parser.add_argument("action", choices=["generate-all", "generate-apache", "generate-systemd"],
                       help="Action to perform")
    parser.add_argument("--domain", default="your-domain.com", help="Domain name")
    parser.add_argument("--ssl", action="store_true", help="Enable SSL configuration")
    parser.add_argument("--output", help="Output directory")

    args = parser.parse_args()

    generator = ApacheConfigGenerator()

    if args.action == "generate-all":
        output_dir = Path(args.output) if args.output else None
        generator.save_configs(output_dir)

    elif args.action == "generate-apache":
        config = generator.generate_virtualhost_config(args.domain, args.ssl)
        print(config)

    elif args.action == "generate-systemd":
        services = generator.generate_systemd_services()
        for service_name, service_content in services.items():
            print(f"# {service_name}")
            print(service_content)
            print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()