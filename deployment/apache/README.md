# Apache Configuration for xtuff.ai Applications

This directory contains Apache virtual host configurations for all xtuff.ai applications.

## Files

- `all-apps-vhosts.conf` - HTTP virtual hosts (port 80)
- `all-apps-ssl-vhosts.conf` - HTTPS virtual hosts (port 443)

## SSL Certificate

All domains use a single Let's Encrypt certificate:
- Certificate name: `xtuff.ai`
- Location: `/etc/letsencrypt/live/xtuff.ai/`
- Expiry: 2026-01-15

### Covered Domains:
- xtuff.ai (main site - port 8500)
- www.xtuff.ai (alias to main)
- social.xtuff.ai (port 8501)
- codexes.xtuff.ai (port 8502)
- trillions.xtuff.ai (port 8504)
- daily.xtuff.ai (port 8509)
- resume.xtuff.ai (port 8512)
- collectiverse.xtuff.ai (legacy - port 8503)
- altdoge.xtuff.ai (legacy - port 8505)
- dailyengine.xtuff.ai (redirect to daily.xtuff.ai)

## Deployment

To deploy these configurations to production:

```bash
./deployment/apache/deploy_apache_config.sh
```

Or manually:
```bash
# Copy configs to production
scp deployment/apache/all-apps-vhosts.conf wfzimmerman@34.172.181.254:/tmp/
scp deployment/apache/all-apps-ssl-vhosts.conf wfzimmerman@34.172.181.254:/tmp/

# SSH to production
ssh wfzimmerman@34.172.181.254

# Install configs
sudo cp /tmp/all-apps-vhosts.conf /etc/apache2/sites-available/
sudo cp /tmp/all-apps-ssl-vhosts.conf /etc/apache2/sites-available/

# Enable sites if not already enabled
sudo a2ensite all-apps-vhosts.conf
sudo a2ensite all-apps-ssl-vhosts.conf

# Test and reload
sudo apache2ctl configtest
sudo systemctl reload apache2
```

## SSL Certificate Renewal

The certificate auto-renews via certbot. To manually renew or expand:

```bash
sudo certbot certonly --cert-name xtuff.ai --expand \
  -d xtuff.ai -d www.xtuff.ai -d social.xtuff.ai -d codexes.xtuff.ai \
  -d trillions.xtuff.ai -d daily.xtuff.ai -d resume.xtuff.ai \
  -d dailyengine.xtuff.ai -d collectiverse.xtuff.ai -d altdoge.xtuff.ai \
  --webroot -w /var/www/html
```

## Features

- HTTPS on all domains with modern TLS 1.2+ configuration
- HTTP to HTTPS redirects for main domains
- WebSocket support for Streamlit applications
- Let's Encrypt ACME challenge support
- Reverse proxy to local Streamlit apps on various ports
