# Cloud Services API Keys Setup Guide

This guide explains how to configure API keys for Alibaba Cloud and IBM Cloud services in the Infra Mind platform.

## Overview

The Infra Mind platform supports integration with multiple cloud providers including:
- Amazon Web Services (AWS)
- Microsoft Azure
- Google Cloud Platform (GCP)
- **Alibaba Cloud** ✨ *New*
- **IBM Cloud** ✨ *New*

## Alibaba Cloud Setup

### Prerequisites
1. An active Alibaba Cloud account
2. Access to RAM (Resource Access Management) console

### Step 1: Create Access Keys

1. **Log in to Alibaba Cloud Console**
   - Go to https://ecs.console.aliyun.com
   - Sign in with your account credentials

2. **Navigate to RAM Console**
   - Click on your avatar in the top-right corner
   - Select "AccessKey Management" from the dropdown

3. **Create Access Key**
   - Click "Create AccessKey"
   - Note down the `Access Key ID` and `Access Key Secret`
   - **Important**: Keep these credentials secure and never share them

### Step 2: Configure Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Alibaba Cloud Configuration
INFRA_MIND_ALIBABA_ACCESS_KEY_ID=your-alibaba-access-key-id
INFRA_MIND_ALIBABA_ACCESS_KEY_SECRET=your-alibaba-access-key-secret
INFRA_MIND_ALIBABA_REGION=cn-beijing  # or your preferred region
```

### Step 3: Set Permissions (Optional)

For enhanced security, create a RAM user with specific permissions:

1. **Create RAM User**
   - Go to RAM Console → Users → Create User
   - Choose "Programmatic access"

2. **Attach Policies**
   - `AliyunECSReadOnlyAccess` - For ECS instances
   - `AliyunRDSReadOnlyAccess` - For RDS databases
   - `AliyunOSSReadOnlyAccess` - For Object Storage Service
   - `AliyunBSSReadOnlyAccess` - For billing information

### Available Alibaba Cloud Services

The integration provides access to:
- **ECS (Elastic Compute Service)** - Virtual servers
- **RDS (Relational Database Service)** - Managed databases
- **OSS (Object Storage Service)** - Object storage
- **Function Compute** - Serverless computing
- **Container Service for Kubernetes (ACK)** - Managed Kubernetes

## IBM Cloud Setup

### Prerequisites
1. An active IBM Cloud account
2. Access to IBM Cloud Identity and Access Management (IAM)

### Step 1: Create API Key

1. **Log in to IBM Cloud Console**
   - Go to https://cloud.ibm.com
   - Sign in with your credentials

2. **Navigate to API Keys**
   - Click "Manage" → "Access (IAM)" → "API keys"
   - Or go directly to: https://cloud.ibm.com/iam/apikeys

3. **Create API Key**
   - Click "Create an IBM Cloud API key"
   - Provide a name and description
   - Click "Create"
   - **Download or copy the API key immediately** (you won't be able to see it again)

### Step 2: Get Account ID

1. **Find Account ID**
   - In IBM Cloud console, click on your profile
   - Copy the Account ID from the account information

### Step 3: Configure Environment Variables

Add the following environment variables to your `.env` file:

```bash
# IBM Cloud Configuration
INFRA_MIND_IBM_API_KEY=your-ibm-api-key
INFRA_MIND_IBM_ACCOUNT_ID=your-ibm-account-id
INFRA_MIND_IBM_REGION=us-south  # or your preferred region
INFRA_MIND_IBM_RESOURCE_GROUP_ID=your-resource-group-id  # optional
```

### Step 4: Set Permissions (Optional)

For enhanced security, create a service ID with specific access policies:

1. **Create Service ID**
   - Go to IAM → Service IDs → Create
   - Assign appropriate access policies

2. **Recommended Policies**
   - `Viewer` role for VPC Infrastructure Services
   - `Reader` role for Resource Controller
   - `Reader` role for Container Registry
   - `Reader` role for Kubernetes Service
   - `Reader` role for Watson services

### Available IBM Cloud Services

The integration provides access to:
- **Virtual Server for VPC** - Virtual machines
- **Databases for MongoDB** - Managed MongoDB
- **Cloud Object Storage** - Object storage
- **Red Hat OpenShift on IBM Cloud** - Managed Kubernetes
- **Watson Assistant** - AI-powered virtual assistant
- **Watson Discovery** - AI search and text analytics
- **Code Engine** - Serverless containers

## Security Best Practices

### 1. Environment Variables
- Store API keys in environment variables, never in code
- Use a `.env` file for local development
- Ensure `.env` is in your `.gitignore` file

### 2. Principle of Least Privilege
- Grant only the minimum permissions required
- Use read-only access for cost analysis and discovery
- Create separate keys for different environments

### 3. Key Rotation
- Regularly rotate API keys (recommended: every 90 days)
- Monitor key usage through cloud provider audit logs
- Deactivate unused keys immediately

### 4. Monitoring
- Enable logging for API key usage
- Set up alerts for unusual activity
- Review access logs regularly

## Verification

### Test Alibaba Cloud Connection

```python
from infra_mind.cloud.alibaba import create_alibaba_client

async def test_alibaba():
    client = create_alibaba_client()
    try:
        services = await client.get_services()
        print(f"✅ Alibaba Cloud connected: {len(services.services)} services found")
    except Exception as e:
        print(f"❌ Alibaba Cloud connection failed: {e}")
    finally:
        await client.close()
```

### Test IBM Cloud Connection

```python
from infra_mind.cloud.ibm import create_ibm_client

async def test_ibm():
    client = create_ibm_client()
    try:
        services = await client.get_services()
        print(f"✅ IBM Cloud connected: {len(services.services)} services found")
    except Exception as e:
        print(f"❌ IBM Cloud connection failed: {e}")
    finally:
        await client.close()
```

## Troubleshooting

### Common Alibaba Cloud Issues

1. **Authentication Failed**
   - Verify Access Key ID and Secret are correct
   - Check if the keys are active in RAM console
   - Ensure the region is correctly specified

2. **Permission Denied**
   - Verify the user has necessary policies attached
   - Check if MFA is required for API access

### Common IBM Cloud Issues

1. **Invalid API Key**
   - Ensure the API key is copied correctly
   - Check if the key is active in IBM Cloud IAM
   - Verify the account ID is correct

2. **Resource Not Found**
   - Check if the resource group ID is correct
   - Verify the region is supported for the service
   - Ensure your account has access to the requested services

### Getting Help

If you encounter issues:

1. Check the application logs for detailed error messages
2. Verify your environment variables are properly set
3. Test connectivity using the verification scripts above
4. Consult the cloud provider's documentation for specific API requirements

## Next Steps

After configuring the API keys:

1. **Restart the Application**
   - Restart both frontend and backend services to load new environment variables

2. **Run API Tests**
   - Use the API Integration Test Suite to verify all endpoints work
   - Check the System Status page for cloud provider connectivity

3. **Create Infrastructure Assessments**
   - The new cloud providers will now be available in assessments
   - Cost comparisons will include Alibaba Cloud and IBM Cloud options

---

**Note**: Keep your API keys secure and never commit them to version control. If you suspect a key has been compromised, revoke it immediately and create a new one.