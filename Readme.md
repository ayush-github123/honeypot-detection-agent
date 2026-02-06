# Agentic Honeypot Detection System

An intelligent, state-driven conversational AI system designed to detect and extract intelligence from scam/phishing attempts. The system engages with potential scammers in real-time, maintains a convincing human-like persona, and systematically extracts actionable intelligence while maintaining operational security.

## 🎯 Project Overview

This is an **agentic honeypot system** that uses advanced language models to:
- **Detect** scam/phishing attempts with confidence scoring
- **Engage** with scammers while maintaining a realistic persona
- **Extract** critical intelligence (UPI IDs, bank accounts, URLs, phone numbers, etc.)
- **Track** conversation state through a sophisticated state machine
- **Report** findings to external endpoints for further analysis

The system is built with FastAPI and leverages large language models (Groq's Llama models) to generate contextually appropriate responses while maintaining character integrity.

---

## 🏗️ Architecture

### Core Components

#### 1. **Scam Detector** (`app/scam_detector.py`)
- **Purpose**: Rule-based detection of scam/phishing messages
- **Techniques**:
  - Keyword matching against 40+ scam indicators
  - Regex pattern detection for suspicious entities (UPI, URLs, phone numbers, amounts)
  - Safe phrase detection to avoid false positives
  - Confidence scoring with multiple detection signals
  - Combination bonuses for multiple scam indicators

- **Detection Signals**:
  - Urgency keywords: "verify now", "immediately", "limited time"
  - Account threat keywords: "blocked", "suspended", "deactivated"
  - Payment keywords: "processing fee", "pay now", "send payment"
  - UPI/Payment patterns: UPI IDs, URLs, amounts
  - Phone numbers and contact information

- **Confidence Score**: Combines multiple signals up to a maximum of 1.0
  - Base threshold: 0.3 (triggers SUSPICIOUS state)
  - High confidence threshold: 0.7 (triggers extraction behavior)

#### 2. **Intelligence Extractor** (`app/agent/intelligence_extractor.py`)
- **Purpose**: Extract actionable intelligence from messages using regex patterns
- **Extracted Categories**:
  - **UPI IDs**: Indian Unified Payments Interface identifiers (`user@bank`)
  - **Bank Accounts**: 9-18 digit account numbers
  - **IFSC Codes**: Indian Financial System Code (`XXXX0XXXXXX`)
  - **URLs**: HTTP/HTTPS links (potential phishing/malware)
  - **Phone Numbers**: 10+ digit phone numbers with country codes
  - **Crypto Wallets**: Bitcoin, Ethereum, and other cryptocurrency addresses
  - **Emails**: Email addresses
  - **Amounts**: Currency amounts in INR with multiple formats
  - **Suspicious Keywords**: Detected from scam keyword list

- **Features**:
  - Regex-based pattern matching with IGNORECASE flag
  - Duplicate removal from extracted entities
  - Confidence scoring per entity based on context
  - Metadata tracking (timestamp, source text)
  - Intelligent merging of findings across messages
  - Completeness scoring (0.0-1.0) for intelligence collection

- **Weighted Scoring**:
  - UPI ID: 25% (critical)
  - Bank Account: 25% (critical)
  - URL: 20% (high priority)
  - Phone: 15% (high priority)
  - IFSC: 10% (medium)
  - Suspicious Keywords: 5% (low)
  - Amount: 3% (low)
  - Email: 2% (low)

#### 3. **Agent State Machine** (`app/agent/state_management.py`)
- **Purpose**: Decision-driven state transitions based on conversation context
- **States**:
  - **IDLE**: Initial state, neutral responses
  - **SUSPICIOUS**: Scam detected but confidence < 0.7, probing questions
  - **ENGAGING**: High scam confidence, cooperative behavior to build trust
  - **EXTRACTING**: Actively extracting intelligence, creating obstacles
  - **TERMINATED**: Conversation ended, no more responses

- **Termination Logic**:
  - **Intelligence Completeness**: >= 50% (configurable via env var)
  - **Stagnation Detection**: No new intelligence for 2 consecutive turns
  - **Hard Cap**: Maximum 12 turns per conversation
  - **Early Termination**: Critical intel + >= 8 turns + scam detected
  - **Minimum Engagement**: 5 turns before termination

- **State Transitions**:
  ```
  IDLE → SUSPICIOUS (scam_confidence ≥ 0.3)
    → ENGAGING (scam_confidence ≥ 0.7)
      → EXTRACTING (intelligence collected)
        → TERMINATED (completeness/stagnation/cap reached)
  ```

#### 4. **LLM Clients** (`app/agent/llm_client.py`)
- **Purpose**: Generate contextually appropriate responses
- **Providers**:
  - **Primary**: Groq Llama-3.3-70B (powerful, general purpose)
  - **Fallback**: Groq Llama-3.1-8B (rate-limit backup)

- **Features**:
  - Automatic fallback on rate limiting
  - Message history context (last 7 messages)
  - System prompt injection for persona control
  - Temperature: 0.7 (balanced creativity/consistency)
  - Max tokens: 200 (realistic SMS-like responses)
  - Automatic role assignment (assistant/user)

#### 5. **Prompt System** (`app/agent/prompts.py`)
- **Purpose**: Dynamic prompt generation based on conversation state
- **Components**:
  - **System Guardrails**: Anti-jailbreak protection, security boundaries
  - **Base Persona**: Character definition ("Alex", a retail worker)
  - **State Instructions**: Behavior guidance per state
  - **Extraction Targets**: Dynamic questions based on missing intelligence
  - **Collected Summary**: Prevents redundant questioning

- **Guardrails**:
  - Never admit AI nature
  - Ignore jailbreak attempts (treat as gibberish)
  - Never provide real credentials/OTPs/PINs
  - Stay in character at all times
  - Redirect manipulation attempts

#### 6. **Session Management** (`app/session.py`)
- **Purpose**: In-memory conversation state tracking
- **Session Data**:
  - Conversation history with timestamps
  - Scam detection confidence scores
  - Extracted intelligence
  - Current agent state
  - Callback status

#### 7. **Callback System** (`app/callback.py`)
- **Purpose**: Report final results to external endpoints
- **Features**:
  - Formats intelligence for structured output
  - Generates human-readable agent notes
  - Sends to GUVI hackathon endpoint
  - Automatic retry on failure
  - 10-second timeout with error handling

- **Output Format**:
  ```json
  {
    "sessionId": "string",
    "scamDetected": boolean,
    "totalMessagesExchanged": number,
    "extractedIntelligence": {
      "bankAccounts": ["array"],
      "upiIds": ["array"],
      "phishingLinks": ["array"],
      "phoneNumbers": ["array"],
      "suspiciousKeywords": ["array"]
    },
    "agentNotes": "string"
  }
  ```

---

## 🔄 Conversation Flow

```
User Message
    ↓
[Scam Detection] → Analyze for scam indicators → Set scam_confidence
    ↓
[Intelligence Extraction] → Extract entities (UPI, URLs, etc.) → Update intelligence dict
    ↓
[State Management] → Decide next state based on:
    - Scam confidence
    - Intelligence completeness
    - Conversation length
    - Stagnation detection
    ↓
[State-Specific Prompt] → Build dynamic prompt with:
    - State instructions
    - Missing intelligence targets
    - Collected summary
    ↓
[LLM Generation] → Generate response matching persona
    ↓
[Save to Session] → Store response in conversation history
    ↓
[Termination Check] → If TERMINATED:
    - Format intelligence
    - Generate agent notes
    - Send callback to external endpoint
    ↓
Return Response to User
```

---

## 🛠️ Technologies & Dependencies

### Core Framework
- **FastAPI** (0.128.0): High-performance async web framework
- **Pydantic** (2.12.5): Data validation with `BaseModel`
- **Uvicorn**: ASGI server for production deployment

### Language Models
- **Groq SDK** (1.0.0): Access to Llama models via Groq API
- **Langchain** : LLM orchestration

### Data & Processing
- **Pandas** (2.3.3): Data manipulation (if needed for analysis)
- **Numpy** (2.4.2): Numerical computing

### Security & Utilities
- **Python-dotenv**: Environment variable management
- **Requests** (2.31.0+): HTTP calls for callbacks
- **Cryptography** (46.0.4): Secure operations

### Optional/Development
- **Streamlit** (1.39.0): Web UI for demo/monitoring
- **Jupyter**: Interactive development

---

## 📋 Setup & Installation

### Prerequisites
- Python 3.8+
- Groq API Key (for Llama models)
- Internet connection for API calls

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd honeyPotDetection
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:

```env
# API Configuration
API_KEY=your-secure-api-key-here

# LLM Configuration
GROQ_API_KEY_NEW=your-groq-api-key

# Agent Configuration
INTELLIGENCE_COMPLETENESS_THRESHOLD=0.5  # 0.0-1.0, default 0.5

# Callback Configuration
HONEY_POT_CALLBACK_URL=https://your-callback-endpoint.com/webhook
```

**Obtaining API Keys**:
- **Groq**: Sign up at [console.groq.com](https://console.groq.com)

### Step 5: Run the Application

#### Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Using Streamlit UI (if available)
```bash
streamlit run app/streamlit.py
```

---

## 🚀 API Usage

### Endpoint: POST `/message`

**Authentication**: Requires `X-API-Key` header

**Request Body**:
```json
{
  "sessionId": "user-session-12345",
  "message": {
    "sender": "scammer",
    "text": "Hi! Your account has been blocked. Verify now by clicking...",
    "timestamp": 1707123456000
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Hello, this is from your bank",
      "timestamp": 1707123400000
    }
  ],
  "metadata": {
    "channel": "sms",
    "language": "en",
    "locale": "en_IN"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "reply": "Wait, which bank is this? How did you get my number?",
  "scam_detected": true,
  "intelligence": {
    "upi_id": [
      {
        "value": "scammer@upi",
        "confidence": 0.85,
        "timestamp": "2026-02-06T12:00:00",
        "source_text": "Send ₹5000 to scammer@upi"
      }
    ]
  },
  "completeness_score": 0.35,
  "turn_count": 5
}
```

### Example cURL Request
```bash
curl -X POST http://localhost:8000/message \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "sessionId": "test-session",
    "message": {
      "sender": "scammer",
      "text": "Your UPI account is blocked. Send ₹500 to payment@bank",
      "timestamp": 1707123456000
    }
  }'
```

### Testing with HTTP File
Use `test/test.http` with REST Client extension in VS Code:
```http
POST http://localhost:8000/message
X-API-Key: dev-secret-key
Content-Type: application/json

{
  "sessionId": "test-session-1",
  "message": {
    "sender": "scammer",
    "text": "Your account has been blocked. Click here to verify",
    "timestamp": 1707123456000
  }
}
```

---

## 🔍 Key Features & Techniques

### 1. Multi-Signal Scam Detection
- Combines keyword matching, regex patterns, and contextual analysis
- 40+ scam keywords covering account threats, urgency, payments, etc.
- Pattern detection for UPI IDs, URLs, amounts, phone numbers
- Safe phrase detection to reduce false positives
- Confidence scoring with bonus multipliers for combined signals

### 2. Intelligent Entity Extraction
- 9 categories of extraction targets with specialized regex patterns
- Deduplication of extracted entities
- Per-entity confidence scoring
- Metadata tracking (timestamp, source context)
- Weighted completeness scoring (higher weight for critical intel)

### 3. State-Driven Conversation
- **5 distinct states** with behavioral instructions
- **Data-driven transitions** based on:
  - Scam confidence levels
  - Intelligence completeness
  - Conversation length
  - Stagnation detection
- **Early termination** to save resources on confirmed scams
- **Hard safety cap** to prevent indefinite conversations

### 4. Dynamic Prompt Engineering
- **State-specific persona adjustments**
- **Intelligence-driven targeting** (asks about missing categories)
- **Guardrail protection** against jailbreak attempts
- **Context awareness** (last 7 messages in history)
- **Collected summary** (prevents redundant questions)

### 5. Character Consistency
- Maintains non-technical retail worker persona ("Alex")
- SMS-style short responses
- Realistic typing patterns and hesitations
- Never breaks character despite manipulation attempts
- Stalls on sensitive requests ("Let me find my card")

### 6. Rate-Limit Fallback
- Primary LLM: Groq Llama-3.3-70B (more capable)
- Fallback LLM: Groq Llama-3.1-8B (lighter weight)
- Automatic detection of 429 errors and quota limits
- Seamless switching without user intervention

### 7. Comprehensive Reporting
- Structured intelligence extraction in JSON format
- Human-readable agent interaction notes
- Timestamp tracking across entire session
- Callback integration with external security systems

---

## 📊 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_KEY` | `dev-secret-key` | API authentication key |
| `GROQ_API_KEY_NEW` | Required | Groq API key for Llama models |
| `INTELLIGENCE_COMPLETENESS_THRESHOLD` | `0.5` | Termination threshold (0.0-1.0) |
| `HONEY_POT_CALLBACK_URL` | Required | Webhook endpoint for results |

### Tunable Parameters

**In `app/agent/state_management.py`**:
```python
HIGH_SCAM_CONFIDENCE = 0.7              # Confidence to trigger ENGAGING
INTELLIGENCE_COMPLETENESS_THRESHOLD = 0.5  # Termination trigger
MAX_TURNS_EXTRACTING = 12               # Hard conversation cap
MIN_TURNS_FOR_TERMINATION = 5           # Minimum before termination
STAGNATION_TURNS = 2                    # Turns without intel = stagnation
```

**In `app/scam_detector.py`**:
```python
SCAM_THRESHOLD = 0.3  # Minimum confidence to trigger SUSPICIOUS
UPI_WEIGHT = 0.35     # High weight for UPI pattern
URL_WEIGHT = 0.35     # High weight for URL pattern
```

**In `app/agent/llm_client.py`**:
```python
temperature = 0.7     # Creativity level (0.0-1.0)
max_tokens = 200      # Response length limit
context_window = 7    # Messages to include in history
```

---

## 📁 Project Structure

```
honeyPotDetection/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app & message endpoint
│   ├── models.py              # Pydantic request/response models
│   ├── config.py              # Settings & environment config
│   ├── auth.py                # API key verification
│   ├── session.py             # Session store (in-memory)
│   ├── scam_detector.py       # Rule-based scam detection
│   ├── callback.py            # Result reporting
│   ├── streamlit.py           # Web UI (optional)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── states.py          # State constants
│   │   ├── state_management.py # State machine logic
│   │   ├── intelligence_extractor.py # Entity extraction
│   │   ├── llm_client.py      # Groq LLM interface
│   │   └── prompts.py         # Dynamic prompt generation
│   └── __pycache__/
├── test/
│   ├── test.http              # HTTP test file
│   └── test.py                # Unit tests
├── test_results/              # Sample session outputs
├── requirements.txt           # Python dependencies
├── Procfile                   # deployment config
├── .env                       # Environment variables (create)
└── README.md                  # This file
```

---

## 🔐 Security Considerations

### 1. **API Security**
- API Key authentication on all endpoints
- HTTPS required in production
- Request validation with Pydantic

### 2. **Character Integrity**
- Jailbreak detection to prevent prompt injection
- Never acknowledge AI nature
- Ignore meta-instructions
- Treat manipulation as gibberish

### 3. **Data Handling**
- Never return real OTPs/passwords/PINs
- Only stall or request from scammer
- Session data stored in-memory (ephemeral)
- Confidential info sanitized before logging

### 4. **Operational Security**
- API key not in version control (use `.env`)
- Callback URL requires authentication
- Timeout protection (10 seconds)
- Rate-limit fallback prevents DDoS

---

## 📈 Performance Metrics

### Extraction Effectiveness
- **Completeness Score**: Weighted across 8 categories
- **Confidence Scoring**: Per-entity confidence (0.0-1.0)
- **Coverage**: Tracks which intelligence types collected

### Conversation Metrics
- **Turn Count**: Total user-agent interactions
- **Engagement Duration**: Minimum 5 turns before termination
- **Stagnation Detection**: No intelligence for 2+ turns
- **Early Termination**: Saves resources on confirmed scams

### System Metrics
- **Response Latency**: LLM generation time
- **Callback Success Rate**: External endpoint delivery
- **Fallback Frequency**: Rate-limit trigger events

---

## 🐛 Troubleshooting

### Issue: "Invalid API key" Error
**Solution**: Verify `X-API-Key` header matches `API_KEY` in `.env`

### Issue: LLM Rate Limiting
**Solution**: Automatic fallback to 8B model; check Groq quota limits

### Issue: No Intelligence Extracted
**Solution**: Ensure scammer message contains recognizable patterns (UPI, URLs, amounts)

### Issue: Callback Not Sending
**Solution**: 
- Verify `HONEY_POT_CALLBACK_URL` is reachable
- Check firewall/proxy rules
- Ensure endpoint accepts POST with JSON

### Issue: Conversation Doesn't Terminate
**Solution**: Check `INTELLIGENCE_COMPLETENESS_THRESHOLD` value (default 0.5)


---

## 📝 License

This project is part of the GUVI Hackathon Series.

---

## 📧 Support

For issues, questions, or contributions, please reach out through the project repository.

**Note**: This system is designed for security research and fraud prevention. Use responsibly and ethically.

---

### Quick Start Summary

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
# Edit .env with API keys and settings

# 3. Run
uvicorn app.main:app --reload

# 4. Test
# POST to http://localhost:8000/message with X-API-Key header
```

