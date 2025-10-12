# Remote Server Structure Analysis

## Target Structure (on wfzimmerman@book-publisher-agi)

```
/home/wfzimmerman/
├── resume-site/                          # Standalone app
│   └── logs/
└── xcu_my_apps/                          # Main container for all xCU apps
    ├── all_applications_runner/          # App launcher (port 8500)
    ├── personal/                          # Daily Engine (port 8509)
    ├── shared/                            # Shared auth & UI components
    ├── systemd_services/                  # Service files
    ├── xtuff/                            # xtuff.ai apps
    │   ├── agentic_social_server/        # Port 8501
    │   ├── altDOGE/                      # Port 8505
    │   ├── collectiverse/                # Port 8503
    │   ├── trillionsofpeople/            # Port 8504
    │   └── xai_health_coach/             # (Optional)
    └── nimble/                           # Nimble Books apps
        └── codexes-factory/              # Port 8502 & 8506 (max-bialystok)
```

## Current Issues

1. **Scattered apps** - Apps deployed to wrong locations:
   - ❌ `/home/wfzimmerman/personal/` (should be in xcu_my_apps)
   - ❌ `/home/wfzimmerman/agentic_social_server/` (should be in xcu_my_apps/xtuff)
   - ❌ `/home/wfzimmerman/trillionsofpeople/` (should be in xcu_my_apps/xtuff)
   - ❌ `/home/wfzimmerman/all_applications_runner/` (should be in xcu_my_apps)

2. **Correct locations**:
   - ✅ `/home/wfzimmerman/xcu_my_apps/nimble/codexes-factory/`
   - ✅ `/home/wfzimmerman/xcu_my_apps/xtuff/agentic_social_server/` (exists)
   - ✅ `/home/wfzimmerman/xcu_my_apps/xtuff/altDOGE/` (exists)
   - ✅ `/home/wfzimmerman/xcu_my_apps/xtuff/collectiverse/` (exists)
   - ✅ `/home/wfzimmerman/xcu_my_apps/xtuff/trillionsofpeople/` (exists)
   - ✅ `/home/wfzimmerman/xcu_my_apps/personal/` (exists)
   - ✅ `/home/wfzimmerman/xcu_my_apps/all_applications_runner/` (exists)

## Solution

### Update systemd service paths to use xcu_my_apps structure:

| Service | Old Path | New Path |
|---------|----------|----------|
| all-apps-runner | `/home/wfzimmerman/all_applications_runner` | `/home/wfzimmerman/xcu_my_apps/all_applications_runner` |
| daily-engine | `/home/wfzimmerman/personal` | `/home/wfzimmerman/xcu_my_apps/personal` |
| agentic-social | `/home/wfzimmerman/agentic_social_server` | `/home/wfzimmerman/xcu_my_apps/xtuff/agentic_social_server` |
| trillions | `/home/wfzimmerman/trillionsofpeople` | `/home/wfzimmerman/xcu_my_apps/xtuff/trillionsofpeople` |
| codexes-factory | `/home/wfzimmerman/nimble/codexes-factory` | `/home/wfzimmerman/xcu_my_apps/nimble/codexes-factory` |
| collectiverse | `/home/wfzimmerman/xtuff/collectiverse` | `/home/wfzimmerman/xcu_my_apps/xtuff/collectiverse` |
| altdoge | `/home/wfzimmerman/altDOGE` | `/home/wfzimmerman/xcu_my_apps/xtuff/altDOGE` |
| max-bialystok | `/home/wfzimmerman/nimble/codexes-factory` | `/home/wfzimmerman/xcu_my_apps/nimble/codexes-factory` |
| resume | `/home/wfzimmerman/resume-site` | `/home/wfzimmerman/resume-site` (unchanged) |

## Deployment Strategy

1. Stop all services
2. Update all systemd service files with correct paths
3. Deploy updated service files
4. Restart all services
5. Clean up old scattered directories (optional)
