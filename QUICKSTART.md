# 🚀 Quick Start Guide - Claw-Litle 1.0

Get started with Claw-Litle in less than 5 minutes!

---

## ⚡ Quick Installation

### On Termux (Android)

```bash
# 1. Install dependencies
pkg update && pkg install python clang llvm libjpeg-turbo libffi zlib ncurses
pkg install rust

# 2. Clone repository
git clone https://github.com/yurislay9-ui/Claw-Litle.git
cd claw-litle

# 3. Create virtual environment
python -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements-termux.txt

# 5. Done!
python -m claw_litle --version
```

### On PC (Linux/Mac/Windows)

```bash
# 1. Clone
git clone https://github.com/yurislay9-ui/Claw-Litle.git
cd claw-litle

# 2. Install
pip install -r requirements.txt

# 3. Run
python -m claw_litle --version
```

---

## 🎯 First Steps

### 1. Verify Installation

```bash
# Check version
claw --version

# Get help
claw --help

# Check status
claw status
```

### 2. Configure API Keys (Optional)

```bash
# Google Search API (optional)
export CLAW_GOOGLE_API_KEY="your_api_key"
export CLAW_GOOGLE_CX="your_search_engine_id"

# Telegram Bot (optional)
export CLAW_TELEGRAM_BOT_TOKEN="your_bot_token"
```

### 3. Your First Query

```bash
# Ask something
claw "What is the capital of Spain?"

# Web search
claw search "Python news 2024"

# Generate code
claw code "script that shows hello world"
```

---

## 🔥 Essential Commands

### Interactive Mode

```bash
# Start conversation
claw interactive

# Conversation example:
# > What is machine learning?
# > What are its applications?
# > How can I learn more?
# > exit
```

### Search

```bash
# Automatic search
claw search "Python tutorial"

# With specific engine
claw search "Python" --engine google
claw search "Python" --engine bing
claw search "Python" --engine brave

# Semantic search
claw semantic "machine learning"
```

### Code

```bash
# Generate script
claw code "function that calculates fibonacci"

# With template
claw code "REST API" --template flask_api

# Auto-correct
claw code "my_script.py" --self-heal
```

### Tasks

```bash
# Schedule task
claw task schedule "backup" --cron "0 2 * * *" --command "claw backup create"

# List tasks
claw task list

# Run workflow
claw workflow run daily_report
```

---

## 📱 Mobile Optimization

### Check Resources

```bash
# System status
claw monitor resources

# Battery
claw monitor battery
```

### Power Modes

```bash
# Change mode
claw power-mode balanced      # Default
claw power-mode performance   # Maximum performance
claw power-mode power-save    # Power saving
claw power-mode ultra-save    # Maximum saving
```

---

## 🛠️ Useful Commands

### Backup and Restoration

```bash
# Create backup
python scripts/backup_manager.py create

# List backups
python scripts/backup_manager.py list

# Restore
python scripts/backup_manager.py restore --name claw_backup_20240406
```

### Updates

```bash
# Check for updates
python scripts/auto_updater.py check

# Update
python scripts/auto_updater.py update
```

### Tests

```bash
# Run all tests
bash tests/run_all_tests.sh

# Specific tests
pytest tests/unit/test_hybrid_engine.py -v
```

---

## 🆘 Troubleshooting

### Error: "Module not found"

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Error: "Insufficient memory"

```bash
# Activate power save mode
claw power-mode power-save

# Reduce agents
export CLAW_MAX_AGENTS=2
```

### Error: "Thermal throttling"

```bash
# Pause for 30 seconds
sleep 30

# Reduce load
claw power-mode ultra-save
```

---

## 📚 More Information

- **Full documentation**: `docs/`
- **Interactive tutorial**: `docs/TUTORIAL_INTERACTIVO.md`
- **Examples**: `examples/`
- **API Reference**: `docs/api-reference.md`
- **Troubleshooting**: `docs/troubleshooting.md`

---

## 🎉 Done!

You now have Claw-Litle 1.0 configured and running. Explore the documentation to take advantage of all its features.

**Recommended commands to continue:**
```bash
claw interactive          # Conversation mode
claw search "Python tips" # Web search
claw code "my project"    # Generate code
claw --help               # View all commands
```

---

**Need help?**
- GitHub Issues: https://github.com/yurislay9-ui/Claw-Litle/issues
- Discussions: https://github.com/yurislay9-ui/Claw-Litle/discussions
- Email: support@clawlitle.com (Pro/Enterprise)