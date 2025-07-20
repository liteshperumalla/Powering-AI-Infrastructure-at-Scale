# Infra Mind Demo Scripts

This directory contains demonstration scripts showcasing the cloud integration capabilities of Infra Mind.

## Available Demos

### 🚀 Production Demo (Recommended)

**`demo_real_api_only.py`** - Production-ready real API integration
- Uses ONLY real cloud API data (no mock fallbacks)
- Azure: Real-time VM and SQL Database pricing via public API
- AWS: Real EC2, RDS, and Storage pricing (requires credentials)
- Production error handling and data validation
- Enterprise-grade accuracy for AI agent recommendations

```bash
python demo_real_api_only.py
```

### 🔄 Legacy Demo (Development)

**`demo_multi_cloud_comparison.py`** - Multi-cloud comparison with mock fallbacks
- Includes mock data fallbacks for development
- Useful for testing without API credentials
- Shows multi-cloud comparison capabilities
- Legacy demo for development purposes

```bash
python demo_multi_cloud_comparison.py
```

## API Requirements

### Azure Integration
- ✅ **No credentials required** (uses public Azure Retail Prices API)
- ✅ **Real-time pricing** for Virtual Machines and SQL Database
- ✅ **Global region support**
- ✅ **Data quality filtering** (removes erroneous pricing)

### AWS Integration
- ⚠️ **AWS credentials required** for real API access
- ✅ **Comprehensive pricing** for EC2, RDS, S3, EBS
- ✅ **Full service specifications**
- ✅ **Production error handling**

To enable AWS integration:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
# or run: aws configure
```

## Key Features Demonstrated

- **Real-time pricing data** from cloud providers
- **Multi-cloud cost comparison** and analysis
- **Service filtering** by specifications (CPU, memory, etc.)
- **Production error handling** with graceful degradation
- **Data validation** and quality filtering
- **Comprehensive service discovery** across providers

## Production Benefits

- **100% Accurate Data**: No mock dependencies
- **Enterprise Ready**: Proper authentication and error handling
- **Cost Effective**: Real pricing enables accurate comparisons
- **Scalable**: Handles comprehensive API responses
- **Reliable**: Graceful error handling when APIs unavailable

## Next Steps

For production deployment, consider adding:
- Redis caching for API responses
- Rate limiting compliance
- Background data refresh jobs
- Monitoring and alerting
- Additional cloud providers (GCP)

---

**Recommendation**: Use `demo_real_api_only.py` for production demonstrations and `demo_multi_cloud_comparison.py` for development testing.