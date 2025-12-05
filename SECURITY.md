# Security Guidelines

## Environment Variables and Secrets

### ⚠️ CRITICAL: Never Commit Secrets

**NEVER commit these files to git:**
- `.env` files
- Any file containing API keys, passwords, or tokens
- Database credentials
- Private keys (`.key`, `.pem`, `.p12`, `.pfx`)

### Setup Process

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual values in `.env`:**
   - Add your OpenAI API key
   - Set authentication secrets
   - Configure database URLs

3. **Verify .env is gitignored:**
   ```bash
   git check-ignore .env
   # Should output: .env
   ```

### If You Accidentally Committed Secrets

If you've accidentally committed secrets to git:

1. **Immediately rotate/revoke the exposed credentials**
   - For OpenAI: Generate a new API key at https://platform.openai.com/api-keys
   - Delete the old compromised key

2. **Remove from git history:**
   ```bash
   # Remove .env from git history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Or use BFG Repo-Cleaner (faster):
   # bfg --delete-files .env
   ```

3. **Force push (after backing up):**
   ```bash
   git push origin --force --all
   git push origin --force --tags
   ```

4. **Inform team members** to rebase their branches

## Best Practices

1. **Use .env.example** - Keep this updated with all required variables (without real values)
2. **Check before commit:**
   ```bash
   git diff --cached | grep -i "api_key\|secret\|password"
   ```
3. **Use pre-commit hooks** to scan for secrets
4. **Rotate keys regularly** - Even if not compromised
5. **Use environment-specific configs** - Different keys for dev/staging/prod

## Protected Information

Never commit:
- API keys (OpenAI, AWS, Azure, etc.)
- Database passwords
- Authentication secrets
- Private keys and certificates
- User data
- Configuration files with credentials

## Recommended Tools

- **git-secrets** - Prevents committing secrets
- **truffleHog** - Finds secrets in git history
- **gitleaks** - Scans for secrets
- **pre-commit** - Git hooks framework

## Contact

If you discover a security vulnerability, please report it privately rather than opening a public issue.

