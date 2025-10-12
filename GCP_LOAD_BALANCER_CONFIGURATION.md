# Google Cloud Load Balancer Configuration for nimblebooks.com

**Date:** 2025-10-09
**Status:** ✅ Complete and Verified

## Overview

This document describes the Google Cloud Platform (GCP) load balancer configuration for `nimblebooks.com` and the changes made to align it with the application setup in `/home/wfzimmerman/xcu_my_apps`.

## Architecture

```
Internet
  ↓
Global Anycast IP: 34.36.142.182 (https2)
  ↓
HTTPS Load Balancer (nimblebooks-forwarding-rule)
  ↓
Target HTTPS Proxy (nimblebooks-target-proxy)
  ↓
SSL Certificate (my-cert)
  ↓
URL Map (nimblebooks)
  ↓
Backend Service (apple-banana)
  ├─ CDN: Enabled
  ├─ Port: 8502
  ├─ Named Port: streamlit-8502-port
  └─ Health Check: streamlit3
      ├─ Port: 8502
      ├─ Path: /
      └─ Interval: 10s
  ↓
Instance Group (instance-group-2, us-central1-c)
  ↓
VM: book-publisher-agi (10.128.0.29)
  ↓
Streamlit App: Codexes Factory
  ├─ Listening: 0.0.0.0:8502
  └─ Service: codexes-factory.service
```

## Changes Made (2025-10-09)

### Problem Identified

The GCP load balancer was misconfigured:
- **Load Balancer:** Pointing to port 8504 (TrillionsOfPeople app)
- **Expected:** Should point to port 8502 (Codexes Factory app)
- **Health Check:** Was checking port 8501 (wrong port)
- **Binding Issue:** Streamlit was listening on `127.0.0.1` instead of `0.0.0.0`

### Changes Applied via gcloud

1. **Instance Group Named Port**
   ```bash
   gcloud compute instance-groups unmanaged set-named-ports instance-group-2 \
     --zone=us-central1-c \
     --named-ports=streamlit-8502-port:8502
   ```
   - Changed from: `streamlit-8504-port:8504`
   - Changed to: `streamlit-8502-port:8502`

2. **Backend Service Port Name**
   ```bash
   gcloud compute backend-services update apple-banana \
     --global \
     --port-name=streamlit-8502-port
   ```
   - Updated to reference the new named port

3. **Health Check Port**
   ```bash
   gcloud compute health-checks update http streamlit3 \
     --port=8502
   ```
   - Changed from: port 8501
   - Changed to: port 8502

### Changes Applied on VM

4. **Streamlit Binding Address**
   - **File:** `/etc/systemd/system/codexes-factory.service`
   - **Change:** `--server.address=127.0.0.1` → `--server.address=0.0.0.0`
   - **Reason:** GCP health checks come from external IPs and cannot reach 127.0.0.1

   ```bash
   sudo sed -i 's/--server.address=127.0.0.1/--server.address=0.0.0.0/g' \
     /etc/systemd/system/codexes-factory.service
   sudo systemctl daemon-reload
   sudo systemctl restart codexes-factory.service
   ```

5. **Source Service File Updated**
   - **Local File:** `/Users/fred/xcu_my_apps/systemd_services/codexes-factory.service`
   - **Change:** Updated to use `0.0.0.0` for future deployments

## Verification Results

All systems operational as of 2025-10-09 00:50 UTC:

```
Instance Group Named Port: streamlit-8502-port → 8502  ✅
Backend Service Port Name: streamlit-8502-port        ✅
Health Check: port 8502, path /                       ✅
Backend Health: HEALTHY                                ✅
Listening Port: 0.0.0.0:8502                          ✅
Website Status: HTTP 200                              ✅
SSL/TLS: Valid (Google-managed cert)                  ✅
CDN: Enabled                                          ✅
```

## Important Notes

### For GCP Load Balancer Health Checks

**Critical:** Applications must listen on `0.0.0.0`, not `127.0.0.1`
- GCP health checks originate from external IP ranges
- Health checks cannot reach `127.0.0.1` (localhost-only binding)
- Use `--server.address=0.0.0.0` in Streamlit configuration

### Port Mappings

| Domain | Port | Application | Service File |
|--------|------|-------------|--------------|
| nimblebooks.com | 8502 | Codexes Factory | codexes-factory.service |
| trillionsofpeople.info | 8504 | TrillionsOfPeople | trillions.service |
| xtuff.ai | 8500 | Master App Runner | all-apps-runner.service |
| social.xtuff.ai | 8501 | Agentic Social | agentic-social.service |
| collectiverse.xtuff.ai | 8503 | Collectiverse | collectiverse.service |
| altdoge.xtuff.ai | 8505 | altDOGE | altdoge.service |
| fredzannarbor.com | 8508 | Resume Site | resume.service |
| dailyengine.xtuff.ai | 8509 | Daily Engine | daily-engine.service |

### Network Architecture

**Direct VM Access (Apache):**
- Apache runs on the VM and proxies to local ports
- Used for: Direct SSH access to VM
- Configuration: `/etc/apache2/sites-enabled/*.conf`

**Public Internet Access (GCP Load Balancer):**
- GCP Load Balancer connects directly to backend ports
- Bypasses Apache entirely
- Used for: All public traffic via nimblebooks.com
- Configuration: GCP backend services, health checks, URL maps

## Deployment Checklist

When deploying changes to production:

- [ ] Ensure systemd service files use `--server.address=0.0.0.0`
- [ ] Verify GCP health check port matches application port
- [ ] Verify GCP backend service named port matches instance group
- [ ] Test health check endpoint responds with HTTP 200
- [ ] Wait 20-30 seconds for health checks to pass after restart
- [ ] Verify `gcloud compute backend-services get-health <service>` shows HEALTHY

## Useful Commands

```bash
# Check health status
gcloud compute backend-services get-health apple-banana --global

# View backend configuration
gcloud compute backend-services describe apple-banana --global

# View health check configuration
gcloud compute health-checks describe streamlit3

# View instance group ports
gcloud compute instance-groups describe instance-group-2 --zone=us-central1-c

# SSH to VM
gcloud compute ssh book-publisher-agi --zone=us-central1-c

# Check what's listening on VM
gcloud compute ssh book-publisher-agi --zone=us-central1-c \
  --command="netstat -tuln | grep 850"

# Test local endpoint
gcloud compute ssh book-publisher-agi --zone=us-central1-c \
  --command="curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8502/"
```

## Related Documentation

- [DEPLOYMENT_FINAL_STATUS.md](./DEPLOYMENT_FINAL_STATUS.md) - Overall deployment status
- [PORT_ASSIGNMENTS.md](./PORT_ASSIGNMENTS.md) - Port allocation across all apps
- [REMOTE_STRUCTURE.md](./REMOTE_STRUCTURE.md) - Remote server directory structure
- `systemd_services/` - Service definition files

## Contact

For issues or questions about this configuration, contact the infrastructure team or refer to the GCP console:
- Project: `rare-shadow-387905`
- Region: `us-central1-c`
- Console: https://console.cloud.google.com/compute
