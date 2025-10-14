# SSH Key Setup for GCP Deployment

The deployment workflow requires a properly formatted SSH private key stored in GitHub Secrets.

## Current Error

```
Load key "/home/runner/.ssh/id_ed25519": error in libcrypto
wfzimmerman@34.172.181.254: Permission denied (publickey).
```

This indicates the `GCP_SSH_KEY` secret is either:
1. Not properly formatted
2. Missing BEGIN/END markers
3. Has incorrect line endings
4. Is encrypted (should be unencrypted for CI/CD)

## How to Fix

### Option 1: Check Current Key Format

On your local machine, check if you have the correct key:

```bash
# Find the private key
ls -la ~/.ssh/id_*

# Display the key (NEVER commit this to git)
cat ~/.ssh/id_ed25519
# OR
cat ~/.ssh/id_rsa
```

The key should look like:

**For ED25519:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
[multiple lines of base64 data]
-----END OPENSSH PRIVATE KEY-----
```

**For RSA:**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
[multiple lines of base64 data]
-----END RSA PRIVATE KEY-----
```

### Option 2: Generate a New Key for Deployment

```bash
# Generate a new ED25519 key specifically for GitHub Actions
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_actions_deploy -N ""

# Display the private key to copy to GitHub Secrets
cat ~/.ssh/github_actions_deploy

# Display the public key to add to GCP server
cat ~/.ssh/github_actions_deploy.pub
```

### Option 3: Update GitHub Secret

1. Go to: https://github.com/fredzannarbor/xcu_my_apps/settings/secrets/actions
2. Find or create secret: `GCP_SSH_KEY`
3. Paste the **ENTIRE** private key including:
   - The `-----BEGIN` line
   - All the base64 content
   - The `-----END` line
4. Make sure there are NO extra spaces or characters

### Option 4: Add Public Key to GCP Server

SSH into the GCP server and add the public key:

```bash
# On GCP server as wfzimmerman
cd ~/.ssh
nano authorized_keys

# Add the public key (from github_actions_deploy.pub)
# Save and exit

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

### Test the Connection

From your local machine:

```bash
# Test with the private key
ssh -i ~/.ssh/github_actions_deploy wfzimmerman@34.172.181.254 "echo 'Connection successful'"
```

If this works, the same key should work in GitHub Actions.

## Debugging

The workflow now includes:
- SSH key format verification
- Connection test before deployment
- Verbose SSH output
- Clear error messages

Check the GitHub Actions log at:
https://github.com/fredzannarbor/xcu_my_apps/actions

Look for:
- "Checking SSH key format..." - Should show BEGIN line
- "Testing SSH connection..." - Should show "SSH connection successful"

## Alternative: Use GitHub Action

If manual key management is problematic, consider using:

```yaml
- name: Install SSH Key
  uses: shimataro/ssh-key-action@v2
  with:
    key: ${{ secrets.GCP_SSH_KEY }}
    known_hosts: 'placeholder'

- name: Adding Known Hosts
  run: ssh-keyscan -H 34.172.181.254 >> ~/.ssh/known_hosts
```

This action handles key formatting automatically.
