# AI Data Population Script

## Overview
This script populates MongoDB with realistic test data for AI Models and AI Features.

## What It Creates

### AI Models (13 models)

**Provider Types:**
1. **OpenAI** (5 models)
   - GPT-4 Turbo
   - GPT-4o
   - GPT-4o-mini
   - GPT-3.5 Turbo
   - GPT-4 32K

2. **Anthropic** (3 models)
   - Claude 3.5 Sonnet
   - Claude 3 Opus
   - Claude 3 Haiku

3. **Google** (3 models)
   - Gemini 1.5 Pro
   - Gemini 1.5 Flash
   - Gemini Pro (Legacy - Inactive)

4. **Azure OpenAI** (2 models)
   - Azure GPT-4 East US
   - Azure GPT-3.5 Turbo West US

5. **AWS Bedrock** (2 models)
   - Claude 3 Sonnet (Bedrock)
   - Titan Text Express (Inactive)

6. **Local/Offline** (3 models)
   - Llama 3.1 405B (localhost:8000)
   - Llama 3.1 70B (localhost:8001)
   - Mixtral 8x7B (localhost:8003) (Inactive)

7. **Cohere** (2 models)
   - Command R+
   - Command

8. **Hugging Face** (1 model)
   - FLAN-T5 XXL (Inactive)

**Each Model Includes:**
- Realistic usage statistics (50K - 500K requests)
- Cost tracking ($0 for local, varies for cloud)
- Performance metrics (latency, success rate)
- Monthly usage counters
- Rate limits
- Created/updated timestamps
- Appropriate status (active/inactive)

### AI Features (10 features)

1. **Sentiment Analysis** (😊)
   - Type: Analysis
   - 12,543 conversations
   - 94.2% accuracy
   - Status: Active

2. **Auto-Tagging** (🏷️)
   - Type: Classification
   - 15,234 conversations
   - 91.8% accuracy
   - Status: Active

3. **Response Generation** (✍️)
   - Type: Generation
   - 8,932 conversations
   - 88.5% accuracy
   - Status: Active

4. **Bot Detection** (🤖)
   - Type: Detection
   - 23,445 conversations
   - 96.7% accuracy
   - Status: Active

5. **Urgency Classification** (🎯)
   - Type: Priority
   - 7,821 conversations
   - 89.3% accuracy
   - Status: Active

6. **Entity Extraction** (🔍)
   - Type: NLP
   - 4,532 conversations
   - 85.1% accuracy
   - Status: Inactive

7. **Multilingual Support** (🌍)
   - Type: Translation
   - 9,876 conversations
   - 92.4% accuracy
   - Status: Active

8. **Intent Detection** (🧠)
   - Type: Analysis
   - 11,234 conversations
   - 90.1% accuracy
   - Status: Active

9. **Conversation Summarization** (📝)
   - Type: Generation
   - 5,432 conversations
   - 87.9% accuracy
   - Status: Active

10. **Topic Categorization** (📂)
    - Type: Classification
    - 9,876 conversations
    - 88.6% accuracy
    - Status: Active

**Each Feature Includes:**
- Detailed configuration
- Usage statistics
- Accuracy and success rates
- Processing time metrics
- Monthly counters
- Last used timestamps
- Tags for organization

## How to Use

### 1. Update Company ID

Edit `populate_ai_data.py` line 13:
```python
SAMPLE_COMPANY_ID = "your_actual_company_id"
```

To get an actual company ID from your database:
```bash
# Connect to MongoDB
mongosh

# Switch to database
use khoros_ai_care

# Find a company
db.companies.findOne()

# Copy the _id value
```

### 2. Run the Script

```bash
cd /Users/seshireddy/projects/khoros-ai-care-expert/khoros-ai-care-expert-api
python populate_ai_data.py
```

### 3. Expected Output

```
============================================================
Populating AI Data for Khoros AI Care Expert
============================================================
Company ID: company_123
MongoDB: mongodb://localhost:27017
Database: khoros_ai_care
============================================================

📦 Populating AI Models (LLM Providers)...
✅ Inserted 13 AI models

⚡ Populating AI Features...
✅ Inserted 10 AI features

============================================================
✅ Data population complete!
============================================================

Summary:
  • AI Models: 13
  • AI Features: 10

You can now:
  1. Start the API: python main.py
  2. View data: http://localhost:9000/docs
  3. Access frontend: http://localhost:8080/console/aicareexpert/
============================================================
```

## Verify Data

### Check MongoDB

```bash
mongosh

use khoros_ai_care

# Count AI models
db.llm_providers.countDocuments()

# Count AI features
db.ai_features.countDocuments()

# View AI models
db.llm_providers.find().pretty()

# View AI features
db.ai_features.find().pretty()
```

### Test via API

```bash
# Start API
python main.py

# List AI models (requires auth)
curl http://localhost:9000/api/llm-providers/

# List AI features (requires auth)
curl http://localhost:9000/api/ai-features/
```

### View in Frontend

1. Start backend: `python main.py`
2. Open: http://localhost:8080/console/aicareexpert/
3. Navigate to:
   - **AI Models**: Should show 13 models
   - **AI Features**: Should show 10 features

## Data Characteristics

### Realistic Statistics
- **Usage data**: Random but realistic ranges
- **Success rates**: 94% - 99.9%
- **Latency**: 0.2s - 3.0s depending on model
- **Costs**: $0 (local) to $2,500/month (premium)
- **Activity**: Recent timestamps (seconds to days ago)

### Provider Coverage
- ✅ Public APIs (OpenAI, Anthropic, Google)
- ✅ Enterprise Cloud (Azure, AWS Bedrock)
- ✅ Local/Offline (Llama, Mixtral)
- ✅ Third-party (Cohere, Hugging Face)

### Status Mix
- **Active**: 10 models, 8 features
- **Inactive**: 3 models, 2 features

## Customization

### Add More Models

Edit the `ai_models` array in `populate_ai_models()`:

```python
{
    "company_id": SAMPLE_COMPANY_ID,
    "name": "Your Model Name",
    "provider_type": "openai",  # or anthropic, google, etc.
    "models": [{
        "model_id": "your-model-id",
        "display_name": "Display Name",
        "max_tokens": 4096,
        "input_cost_per_1k_tokens": 0.001,
        "output_cost_per_1k_tokens": 0.003
    }],
    "credentials": {
        "api_key": "your-api-key"
    },
    "status": "active",
    "description": "Model description"
}
```

### Add More Features

Edit the `ai_features` array in `populate_ai_features()`:

```python
{
    "company_id": SAMPLE_COMPANY_ID,
    "name": "Your Feature Name",
    "feature_type": "Analysis",  # or Classification, Generation, etc.
    "description": "Feature description",
    "icon": "🎯",
    "enabled": True,
    "config": {
        # Feature-specific configuration
    }
}
```

## Troubleshooting

### Error: "Collection not found"
MongoDB will auto-create collections on first insert. No action needed.

### Error: "Connection refused"
Ensure MongoDB is running:
```bash
# Check if MongoDB is running
ps aux | grep mongod

# Start MongoDB (if not running)
brew services start mongodb-community
# or
mongod --dbpath /path/to/data
```

### Error: "Module not found"
Install dependencies:
```bash
pip install motor pymongo pydantic
```

## Clean Up Data

To remove all test data:

```bash
mongosh

use khoros_ai_care

# Remove AI models
db.llm_providers.deleteMany({"company_id": "company_123"})

# Remove AI features
db.ai_features.deleteMany({"company_id": "company_123"})
```

Or uncomment lines in the script:
```python
# Line 202 in populate_ai_models()
await collection.delete_many({"company_id": SAMPLE_COMPANY_ID})

# Line 356 in populate_ai_features()
await collection.delete_many({"company_id": SAMPLE_COMPANY_ID})
```

## Summary

This script creates a complete, realistic dataset for testing the AI Care Expert platform:

- ✅ 13 AI models across 7 provider types
- ✅ 10 AI features across 7 feature types
- ✅ Realistic usage statistics
- ✅ Mix of active/inactive items
- ✅ Proper timestamps and metadata
- ✅ Ready for immediate use in frontend

Run the script and your AI Care Expert admin console will have real data to work with! 🚀
