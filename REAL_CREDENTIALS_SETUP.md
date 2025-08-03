# Real Credentials Setup Guide

This guide will help you configure real cloud provider credentials to eliminate the validation warnings and enable full functionality in the demo.

## Quick Setup

### Option 1: Update .env.demo (Recommended for Demo)

Replace the placeholder values in `.env.demo` with your real credentials:

```bash
# LLM Providers (Required for AI functionality)
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here

# AWS Credentials (Optional - for real AWS data)
AWS_ACCESS_KEY_ID=AKIA_YOUR_ACTUAL_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=your_actual_secret_access_key
AWS_DEFAULT_REGION=us-east-1

# Azure Credentials (Optional - for real Azure data)
AZURE_CLIENT_ID=your-actual-azure-client-id
AZURE_CLIENT_SECRET=your-actual-azure-client-secret
AZURE_TENANT_ID=your-actual-azure-tenant-id
AZURE_SUBSCRIPTION_ID=your-actual-azure-subscription-id

# GCP Credentials (Optional - for real GCP data)
GCP_PROJECT_ID=your-actual-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
```

### Option 2: Update main .env file

Update the main `.env` file with real credentials (this will override .env.demo values).

## Obtaining Credentials

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

### AWS Credentials
1. Go to AWS IAM Console
2. Create a new user with programmatic access
3. Attach policies: `ReadOnlyAccess` (minimum) or specific service policies
4. Copy Access Key ID and Secret Access Key

### Azure Credentials
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Create a new app registration
3. Go to Certificates & secrets → Create new client secret
4. Copy Client ID, Client Secret, and Tenant ID
5. Get Subscription ID from Azure Portal → Subscriptions

### GCP Credentials
1. Go to Google Cloud Console → IAM & Admin → Service Accounts
2. Create a new service account
3. Download the JSON key file
4. Set the path in GOOGLE_APPLICATION_CREDENTIALS

## Security Best Practices

1. **Never commit real credentials to version control**
2. **Use environment-specific files** (.env.local, .env.production)
3. **Rotate credentials regularly**
4. **Use minimal required permissions**
5. **Consider using cloud provider credential managers** (AWS IAM roles, Azure Managed Identity, etc.)

## Testing Your Setup

After updating credentials, run:

```bash
python demo_mvp_capabilities.py
```

You should see:
- ✅ No credential validation warnings
- ✅ Real cloud provider data (if configured)
- ✅ Actual LLM responses (if OpenAI key provided)

## Troubleshooting

### AWS Issues
- Ensure your AWS user has the necessary permissions
- Check that your region is correct
- Verify credentials with: `aws sts get-caller-identity`

### Azure Issues
- Ensure the service principal has proper permissions
- Check tenant ID is correct
- Verify with: `az account show`

### GCP Issues
- Ensure service account has proper roles
- Check project ID is correct
- Verify with: `gcloud auth application-default print-access-token`

### OpenAI Issues
- Check API key format (should start with `sk-`)
- Verify you have credits/billing set up
- Test with: `curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models`

## Minimal Setup for Demo

If you only want to eliminate warnings, you can set up just AWS credentials:

```bash
# In .env.demo or .env
AWS_ACCESS_KEY_ID=your_real_aws_key
AWS_SECRET_ACCESS_KEY=your_real_aws_secret
AWS_DEFAULT_REGION=us-east-1
```

This will eliminate the AWS credential warnings while keeping other functionality in demo mode.