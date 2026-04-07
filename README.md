# Claw-Litle 1.0

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Platform](https://img.shields.io/badge/platform-Termux%20ARM64-red.svg)

**Personal Agentic Operating System**
*100% LOCAL/OFFLINE - Optimized for Termux ARM64*

[Installation](#installation) • [Documentation](docs/) • [Architecture](docs/architecture.md) • [Security](docs/security.md)

</div>

---

## 🚀 Main Features

### 🔥 Hybrid 4-Level Engine
- **Level 1: Regex** (~0ms) - Instant exact patterns
- **Level 2: Fuzzy** (~1-2ms) - Approximate matching with Levenshtein
- **Level 3: Semantic** (~5-15ms) - ONNX MiniLM Embeddings
- **Level 4: Expert Rules** - Validation with expert rules

### 🤖 Multi-Agent Swarm System
- **6 Search Agents**: Google, Bing, Brave, Deep Scraper, Semantic, Synthesizer
- **Thermal Control**: Maximum 2 concurrent agents on mobile
- **Semantic Consensus**: Improved TF-IDF for result synthesis

### 🛡️ Hardened Security
- **Gateway Layer 0**: Sanitization, JWT auth, rate limiting
- **Sandbox Executor**: Secure execution with hard timeout (10s)
- **Self-Healing Engine**: Auto-correction in 3 iterations
- **Buddy Reviewer**: Parallel quality review

### 📱 ARM64 Optimized
- **<350MB RAM peak** - Lazy loading of models
- **Thermal Guard** - CPU temperature control
- **Battery Saver** - Power saving mode
- **No Docker/GUI** - 100% native terminal

---

## 📚 Usage Examples

Explore the `examples/` folder for practical examples:

```bash
# Web search with Swarm Intelligence
python examples/01_web_search_example.py

# Code generation with Self-Healing
python examples/02_code_generation_example.py
```

See [examples/README.md](examples/README.md) for more details.

---

## 📋 Requirements

### Minimum
- Python 3.11+
- 2GB RAM (4GB recommended)
- Termux on Android ARM64
- Internet connection (optional)

### Supported Platforms
- ✅ **Termux ARM64** (primary)
- ✅ **Raspberry Pi 4/5** (ARM64)
- ✅ **Linux x86_64** (development)
- ✅ **macOS** (development)

---

## ⚡ Quick Installation

### On Termux (Android)

```bash
# 1. Update Termux
pkg update && pkg upgrade

# 2. Install system dependencies
pkg install python git clang curl wget

# 3. Clone repository
git clone https://github.com/yurislay9-ui/Claw-Litle.git
cd claw-litle

# 4. Create virtual environment
python -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements-termux.txt

# 6. Run
python -m claw_litle
```

### On Laptop/PC (Development)

```bash
# 1. Clone repository
git clone https://github.com/yurislay9-ui/Claw-Litle.git
cd claw-litle

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python -m claw_litle
```

---

## 🎮 Basic Usage

### Start the Bot

```bash
python -m claw_litle
```

### Main Commands

```
🔍 Searches:
   search [term]          - Multi-agent web search
   info [term]            - Local semantic search

💻 Code:
   create [app/script]    - Generate Python code
   fix [code]             - Auto-correct code

⚙️ System:
   status                 - View system status
   doctor                 - Full diagnosis
   clean                  - Clear cache

❓ Help:
   help                   - Show this help
   exit                   - Exit system
```

### Examples

```
:input: search iPhone 15 price
🤖 🔄 Processing: web_search...

:input: create scraper for Amazon
🤖 🔄 Processing: code_generation...

:input: status
🤖 System Status:
   ✓ Gateway: 0 active users
   ✓ Engine: Active levels: 4/4
   ✓ Router: 0 cached entries
   ✓ Handlers: 12 registered
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 0: GATEWAY                         │
│  Sanitization • JWT Auth • Rate Limiting • Anti-Fraud      │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 1: CORE ENGINE                     │
│  ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Level 1 │→│ Level 2 │→│  Level 3 │→│    Level 4       │ │
│  │  Regex  │ │  Fuzzy  │ │ Semantic │ │   Expert Rules   │ │
│  │  (~0ms) │ │ (~1-2ms)│ │ (~5-15ms)│ │    (always)      │ │
│  └─────────┘ └─────────┘ └──────────┘ └──────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 2: ROUTER                          │
│  Intent Classification • Dispatch • Cache • Error Handling │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 3: AGENTS                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │   Swarm    │ │  Code Gen  │ │   Vision   │ │  Tasks   │ │
│  │  Manager   │ │  Engine    │ │   Agency   │ │  Engine  │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 4: SYNTHESIS                       │
│  Improved TF-IDF • Buddy Reviewer • Semantic Consensus     │
├─────────────────────────────────────────────────────────────┤
│                    LAYER 5: PERSISTENCE                     │
│  SQLite + sqlite-vec (WAL) • SQLCipher • Memory Store      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
claw-litle/
├── src/
│   ├── __main__.py           # Main entry point
│   ├── __init__.py           # Main package
│   ├── gateway.py            # Security Gateway
│   ├── router.py             # Intent Router
│   ├── environment_detector.py # Environment Detector
│   │
│   ├── engine/               # 4-Level Engine
│   │   ├── nivel_1_regex.py  # Regex Filter (~0ms)
│   │   ├── nivel_2_fuzzy.py  # Fuzzy Matching (~1-2ms)
│   │   ├── nivel_3_semantic.py # Semantic Embeddings
│   │   └── nivel_4_expert.py # Expert Rules
│   │
│   ├── agents/               # Multi-Agent System
│   │   ├── swarm_manager.py  # Agent orchestrator
│   │   ├── google_searcher.py
│   │   ├── bing_searcher.py
│   │   ├── brave_searcher.py
│   │   ├── deep_scraper.py
│   │   ├── semantic_searcher.py
│   │   └── synthesizer.py
│   │
│   ├── code_gen/             # Code Generation
│   │   ├── template_engine.py
│   │   ├── sandbox_executor.py
│   │   ├── self_healing_engine.py
│   │   └── buddy_reviewer.py
│   │
│   ├── vision/               # Vision Agency
│   │   ├── permission_manager.py
│   │   ├── screen_capture.py
│   │   ├── ui_parser.py
│   │   ├── pii_detector.py
│   │   ├── action_planner.py
│   │   ├── action_executor.py
│   │   └── data_extractor.py
│   │
│   ├── tasks/                # Task Engine
│   │   ├── task_manager.py
│   │   ├── scheduler.py
│   │   └── workflow_engine.py
│   │
│   ├── tools/                # Tools
│   │   ├── file_manager.py
│   │   ├── shell_executor.py
│   │   ├── system_info.py
│   │   ├── calculator.py
│   │   └── utilities.py
│   │
│   ├── channels/             # Communication Channels
│   │   ├── terminal_cli.py
│   │   ├── telegram_bot.py
│   │   └── websocket_handler.py
│   │
│   ├── persistence/          # Persistence
│   │   ├── vector_store_sqlite.py
│   │   ├── memory_store.py
│   │   ├── config_store.py
│   │   └── usage_analytics.py
│   │
│   ├── security/             # Security
│   │   ├── auth.py
│   │   ├── rate_limiter.py
│   │   ├── anti_fraud.py
│   │   ├── encryption.py
│   │   ├── audit_logger.py
│   │   └── code_integrity.py
│   │
│   ├── monitoring/           # Monitoring
│   │   ├── thermal_monitor.py
│   │   ├── resource_monitor.py
│   │   └── health_checker.py
│   │
│   ├── features/             # Advanced Features
│   │   ├── feature_flags.py
│   │   ├── query_complexity_analyzer.py
│   │   ├── self_refining_engine.py
│   │   ├── adaptive_thinking_controller.py
│   │   ├── kairos_daemon.py
│   │   ├── context_manager.py
│   │   ├── security_analyst.py
│   │   └── enhanced_buddy_reviewer.py
│   │
│   └── config/               # Configuration
│       ├── defaults.toml
│       ├── intents_registry.json
│       ├── environment_profiles/
│       │   ├── termux_arm64.json
│       │   ├── termux_light.json
│       │   ├── raspberry_pi.json
│       │   └── laptop_pc.json
│       └── templates/
│           ├── python/
│           └── self_healing_fixes/
│
├── tests/                    # Tests
│   ├── unit/
│   ├── integration/
│   ├── conftest.py
│   └── test_*.py
│
├── scripts/                  # Installation Scripts
│   ├── install.sh
│   ├── install_termux.sh
│   ├── setup_background.sh
│   ├── monitor_thermal.sh
│   └── download_models.py
│
├── docs/                     # Documentation
│   ├── installation.md
│   ├── architecture.md
│   ├── security.md
│   ├── api-reference.md
│   ├── plugin-sdk.md
│   └── troubleshooting.md
│
├── models/                   # ONNX Models
│   └── all-MiniLM-L6-v2.onnx
│
├── assets/                   # Resources
│   ├── banners/
│   ├── icons/
│   └── themes/
│
├── pyproject.toml            # Project configuration
├── requirements.txt          # General dependencies
├── requirements-termux.txt   # Termux dependencies
├── requirements-dev.txt      # Development dependencies
├── LICENSE                   # MIT License
├── CHANGELOG.md              # Change history
└── README.md                 # This file
```

---

## 🔧 Configuration

### Environment Profiles

The system automatically detects the environment and selects the optimal profile:

| Profile | RAM | Agents | ONNX | Use Case |
|---------|-----|--------|------|----------|
| `termux_arm64` | 350MB | 2 | ✓ | Android ARM64 |
| `termux_light` | 200MB | 1 | ✗ | Older Android |
| `raspberry_pi` | 500MB | 3 | ✓ | Raspberry Pi 4/5 |
| `laptop_pc` | 1000MB | 6 | ✓ | Development |

### Environment Variables

```bash
# Telegram Bot (optional)
export TELEGRAM_TOKEN="your-bot-token"

# Log level
export CLAW_LOG_LEVEL="INFO"

# Data path
export CLAW_DATA_DIR="/sdcard/clawlitle-data/"
```

---

## 🛡️ Security

### Design Principles

1. **No dangerous eval/exec** - Strict sandbox
2. **Rate limiting** - Anti-abuse per user
3. **Sanitization** - XSS/injection prevention
4. **JWT Auth** - Optional authentication
5. **Audit logging** - Complete traceability

### Import Whitelist

Only these imports are allowed in generated code:

```python
# Allowed
requests, beautifulsoup4, flask, fastapi, sqlite3, rich, click
schedule, pandas, python-telegram-bot, httpx, pillow, jinja2
pydantic, aiofiles, datetime, json, re, os, sys, math, random
logging, asyncio, threading, time
```

---

## 📊 Performance

### Benchmarks (Termux ARM64)

| Operation | Time | RAM |
|-----------|------|-----|
| Regex Match | ~0.1ms | <1MB |
| Fuzzy Match | ~1-2ms | <5MB |
| Semantic Match | ~10-15ms | ~100MB |
| Multi-Agent Search | ~2-5s | ~200MB |
| Code Generation | ~1-3s | ~150MB |

### Optimizations

- **Lazy Loading** - ONNX models only when RAM available
- **Short-Circuit** - Stops execution if lower level resolves
- **Aggressive Cache** - 24h TTL by default
- **Thermal Throttling** - Reduces agents if temp > 70°C

---

## 🤝 Contributing

1. Fork the repository
2. Create a branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Linting
flake8 src/
black --check src/

# Type checking
mypy src/
```

---

## 📄 License

This project is under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Termux** - Amazing Android terminal
- **ONNX Runtime** - Efficient ARM64 inference
- **Rich** - Beautiful and professional terminal
- **SQLite** - Lightweight and powerful database

---

<div align="center">

**Claw-Litle 1.0**

*Made with ❤️ for the Termux community*

[⬆ Back to top](#claw-litle-10)

</div>