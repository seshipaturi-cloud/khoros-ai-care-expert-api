# Utility Scripts

This folder contains utility scripts for managing and seeding data in the Khoros AI Care Expert system.

## Available Utilities

### 1. LLM Providers Seeder (`seed_llm_providers.py`)

Seeds sample LLM provider configurations into MongoDB via the API.

#### Features:
- Creates 5 pre-configured LLM providers (OpenAI, Anthropic, Azure OpenAI, AWS Bedrock, Google Vertex AI)
- Automatically creates a default company if needed
- Checks for existing providers to avoid duplicates
- Provides detailed logging of the seeding process
- Tests the seeded data by fetching all providers

#### Usage:

**Option 1: Using the shell script (recommended)**
```bash
cd khoros-ai-care-expert-api
./utils/run_seed_providers.sh
```

**Option 2: Direct Python execution**
```bash
cd khoros-ai-care-expert-api
python utils/seed_llm_providers.py
```

**Option 3: With custom API URL**
```bash
export API_BASE_URL="http://your-api-server:8000"
python utils/seed_llm_providers.py
```

#### Configuration:

The script uses the following environment variables:
- `API_BASE_URL`: API server URL (default: `http://localhost:8000`)
- `API_TOKEN`: Authorization token if required (default: empty)

#### Sample Providers Created:

1. **OpenAI Production**
   - Provider Type: OpenAI
   - Models: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
   - Features: Function calling, streaming
   - Default provider for the company

2. **Anthropic Claude**
   - Provider Type: Anthropic
   - Models: Claude 3 Opus, Sonnet, Haiku
   - Features: Vision support, large context window

3. **Azure OpenAI Service**
   - Provider Type: Azure OpenAI
   - Models: Azure GPT-4, GPT-3.5 Turbo
   - Features: Enterprise compliance, dedicated endpoints

4. **AWS Bedrock**
   - Provider Type: AWS Bedrock
   - Models: Claude 2, Amazon Titan, Llama 2
   - Features: Multiple model families, AWS integration

5. **Google Vertex AI**
   - Provider Type: Google Vertex
   - Models: Gemini Pro, Gemini Pro Vision, PaLM 2
   - Features: Vision support, multimodal capabilities

#### Important Notes:

⚠️ **API Keys**: The script includes dummy API keys. You must replace these with actual API keys before using the providers:
- OpenAI: Replace `sk-proj-test123456789`
- Anthropic: Replace `sk-ant-test123456789`
- Azure: Update endpoint and key
- AWS: Update access key and secret
- Google: Update API key and project ID

⚠️ **Company ID**: The script uses `default_company_001`. Update this if you need to assign providers to a different company.

#### Customization:

To add or modify providers, edit the `LLM_PROVIDERS_DATA` list in `seed_llm_providers.py`:

```python
LLM_PROVIDERS_DATA = [
    {
        "company_id": "your_company_id",
        "name": "Custom Provider",
        "provider_type": "openai",
        "api_key": "your-api-key",
        # ... other fields
    }
]
```

## Prerequisites

1. **MongoDB**: Ensure MongoDB is running
2. **API Server**: Start the FastAPI server:
   ```bash
   cd khoros-ai-care-expert-api
   uvicorn main:app --reload --port 8000
   ```
3. **Python Dependencies**: Install required packages:
   ```bash
   pip install httpx
   ```

## Troubleshooting

### API Connection Error
- Verify the API server is running on the correct port
- Check `API_BASE_URL` environment variable

### Authentication Error
- If your API requires authentication, set the `API_TOKEN` environment variable
- Ensure the token has sufficient permissions

### Duplicate Provider Error
- The script checks for existing providers by name
- Delete existing providers via the web interface or API if needed

### Company Not Found
- The script will automatically create a default company
- Ensure you have permission to create companies

## Additional Utilities

More utilities can be added to this folder for:
- Seeding test data for brands, AI agents, users
- Data migration scripts
- Backup and restore utilities
- Performance testing scripts
- Data cleanup utilities

## Support

For issues or questions about these utilities, please refer to the main project documentation or create an issue in the project repository.