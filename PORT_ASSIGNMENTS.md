# xCU Port Assignments

## Firewall Configuration
**Allowed Ports:** 8501-8510 (Google Cloud Firewall)

## Current Port Mapping

| Port | Application | Domain | Service Status | Entry Point |
|------|-------------|--------|----------------|-------------|
| 8500 | All Applications Runner | xtuff.ai | ✅ Running | main.py |
| 8501 | Social Xtuff (Agentic Social) | social.xtuff.ai | ⚠️ Port conflict | app.py |
| 8502 | Codexes Factory | codexes.nimblebooks.com | ✅ Running (old process) | src/codexes/codexes-factory-home-ui.py |
| 8503 | Collectiverse | collectiverse.xtuff.ai | 🔴 Not deployed | app.py |
| 8504 | TrillionsOfPeople | trillionsofpeople.info | ✅ Running | trillionsofpeople.py |
| 8505 | altDOGE | altdoge.xtuff.ai | 🔴 Not deployed | cfr_document_analyzer/streamlit_app.py |
| 8506 | Max Bialystok | maxb.nimblebooks.com | 🔴 Not deployed | max_bialystok_home.py |
| 8507 | Available | - | - | - |
| 8508 | Resume & Contact | fredzannarbor.com | 🔴 Not deployed | app.py |
| 8509 | Daily Engine | dailyengine.xtuff.ai | ✅ Running | daily_engine.py |
| 8510 | Available | - | - | - |

## Apache Reverse Proxy Configuration

Each domain is configured with:
- ProxyPass / http://127.0.0.1:[PORT]/
- ProxyPassReverse / http://127.0.0.1:[PORT]/
- WebSocket support via RewriteRule for Streamlit apps

## Current Issues

### Port 8501 Conflict
- **Problem:** Old process using port 8501, blocking agentic-social service
- **Solution:** Kill old process and restart service

### Port 8502 Conflict
- **Problem:** Old codexes-factory process running (PID 533567, started Sep 12)
- **Solution:** Create systemd service for codexes-factory and stop old process

## Systemd Services Deployed

- ✅ all-apps-runner.service (port 8500)
- ✅ daily-engine.service (port 8509)
- ⚠️ agentic-social.service (port 8501 - failing due to port conflict)
- ✅ trillions.service (port 8504)

## Services Needed

1. codexes-factory.service (port 8502)
2. collectiverse.service (port 8503)
3. altdoge.service (port 8505)
4. max-bialystok.service (port 8506)
5. resume.service (port 8508)

## Migration Status

- ✅ Code deployed via git
- ✅ Systemd services created for 4 apps
- ⚠️ Port conflicts preventing full deployment
- 🔴 5 additional services needed
