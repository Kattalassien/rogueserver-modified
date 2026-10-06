# RogueServer Enhanced Host - Quick Start Guide

## 🚀 Launch in 2 Minutes

### Step 1: Setup
```bash
cd /path/to/rogueserver-modified
cp host.ini.example host.ini
```

### Step 2: Configure for Your Network
Edit `host.ini`:
```ini
[host]
host = 0.0.0.0
dashboard_port = 8765
admin_token = your_secure_password
```

### Step 3: Launch
```bash
python3 desktop_host.py
```

### Step 4: Access Dashboard
- **Desktop**: `http://localhost:8765`
- **iPhone/Other Devices**: `http://<YOUR_PC_IP>:8765`

---

## 📊 Dashboard URLs Available

| URL | Purpose | Authentication |
|-----|---------|-----------------|
| `/` | Status dashboard | None |
| `/editor` | Server config | admin_token |
| `/variables` | Game settings | admin_token |
| `/mods` | Mod manager | admin_token |
| `/api/status` | JSON status | None |
| `/api/variables` | JSON variables | None |
| `/api/mods` | JSON mods | None |

---

## 🎮 Common Tasks

### Modify Game Variables on iPhone
1. Connect to WiFi (same network as desktop)
2. Open Safari: `http://<PC_IP>:8765/variables`
3. Change desired values (catch limit, difficulty, etc.)
4. Enter admin_token and save
5. Changes apply immediately

### Add a Mod
1. Navigate to `http://localhost:8765/mods`
2. Enter mod name and GitHub URL
3. Select "Enable" or "Disable"
4. Enter admin_token and save

### Check Server Logs
```bash
tail -f host.log
```

### Validate Configuration (No Launch)
```bash
python3 desktop_host.py --check
```

---

## ✓ What's Included

### Enhanced Features
- ✓ Multi-window dashboard with 4 main sections
- ✓ Real-time game variable editor (10+ configurable values)
- ✓ Mod management system for tracking mods/scripts
- ✓ iPhone/LAN access support
- ✓ Comprehensive error logging
- ✓ Web + GUI dual interfaces
- ✓ No external Python dependencies

### Files Created
- `desktop_host.py` - Enhanced control panel
- `game_variables.json` - Game configuration
- `mods.json` - Mod tracking
- `ENHANCED_HOST_README.md` - Full documentation
- `IPHONE_LAN_GUIDE.md` - iPhone setup guide
- `PROJECT_SUMMARY.md` - Architecture & roadmap

---

## 🔧 Configuration Reference

### Game Variables (10 configurable)
```json
{
  "pokemonCatchLimit": 999,          // Max catchable Pokémon
  "maxLevel": 100,                   // Max level
  "difficultyMultiplier": 1.0,       // Difficulty 0.5-2.0
  "experienceMultiplier": 1.0,       // XP gain
  "enableRandomEvents": true,        // Random battles
  "enableTrainerScaling": true,      // Dynamic trainer difficulty
  "allowSwitching": true,            // Mid-battle switching
  "startingPokemonLevel": 5,         // Starting level
  "basePokemonStats": "normal",      // Stats preset
  "trainerDifficulty": "normal"      // Trainer difficulty
}
```

### Server Configuration (host.ini)
```ini
[host]
host = 0.0.0.0                        # Network binding
dashboard_port = 8765                 # Dashboard port
game_url = http://localhost:8000      # Game server
server_url = http://localhost:8001    # API server
launch_command = docker compose -f docker-compose.Development.yml up --build
stop_command = docker compose -f docker-compose.Development.yml down
admin_token = your_password           # Authentication
```

---

## 📱 iPhone Access Steps

1. **Find your PC's IP** (on your PC):
   ```bash
   # macOS
   ipconfig getifaddr en0
   # Linux
   hostname -I
   # Windows
   ipconfig
   ```
   Example: `192.168.1.50`

2. **Connect iPhone to same WiFi**

3. **Open Safari and visit**:
   - Dashboard: `http://192.168.1.50:8765`
   - Variables: `http://192.168.1.50:8765/variables`
   - Mods: `http://192.168.1.50:8765/mods`

4. **Enter admin_token when prompted**

---

## 🐛 Troubleshooting

### "Cannot connect"
```bash
# Check if service running
docker ps

# Check logs
tail -f host.log

# Verify network
ping <YOUR_PC_IP>
```

### "Admin token required"
- Set `admin_token` in `host.ini`
- Restart the script
- Try again

### "Server not running"
```bash
# Start Docker
docker compose -f docker-compose.Development.yml up --build

# Monitor logs
docker compose logs -f
```

### "Connection refused"
- Ensure port 8765 is not in use
- Check firewall settings
- Verify `host = 0.0.0.0` in config

---

## 📚 Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| **QUICK_START.md** | Get running in 2 minutes | First time setup |
| **IPHONE_LAN_GUIDE.md** | iPhone/LAN access | Need mobile access |
| **ENHANCED_HOST_README.md** | Full feature documentation | Understanding capabilities |
| **PROJECT_SUMMARY.md** | Architecture & roadmap | Developer/contributor |

---

## 🎯 Next Steps & Generated Prompts

### Immediate (Right Now)
1. ✓ Copy `host.ini.example` to `host.ini`
2. ✓ Set admin_token in config
3. ✓ Run `python3 desktop_host.py`
4. ✓ Open `http://localhost:8765`

### Short Term (Next Session)
**Prompt**: "Configure game variables for a custom difficulty run"
```
- Open /variables
- Set pokemonCatchLimit to 50
- Set difficultyMultiplier to 1.5
- Enable trainerScaling
- Save and start playing
```

**Prompt**: "Add a favorite mod to the server"
```
- Navigate to /mods
- Enter mod name (e.g., "Shiny Mod")
- Enter GitHub URL
- Select "Enable"
- Save configuration
```

**Prompt**: "Check server health and logs"
```
- Visit /api/status for JSON output
- tail -f host.log for detailed logs
- Monitor docker ps for container status
```

### Medium Term (This Week)
**Prompt**: "Setup iPhone access to the server"
```
1. Find PC LAN IP: ipconfig getifaddr en0
2. Set host = 0.0.0.0 in host.ini
3. Set admin_token = strong_password
4. Restart: python3 desktop_host.py
5. On iPhone: open http://<PC_IP>:8765
```

**Prompt**: "Automate variable changes during gameplay"
```
# Use curl to update variables via API
curl -X POST http://localhost:8765/variables \
  -d "var_pokemonCatchLimit=100&token=admin_token"
```

**Prompt**: "Monitor server performance"
```
# Watch real-time stats
watch 'python3 desktop_host.py --check | jq .running'

# Monitor Docker resources
docker stats

# Check network usage
iftop -i eth0
```

### Long Term (Next Month)
**Prompt**: "Integrate with Notion for documentation"
```
- Export game variables to Notion database
- Document mod compatibility matrix
- Track server uptime and statistics
- Backup configuration to cloud
```

**Prompt**: "Create automated mod testing pipeline"
```
- Scan enabled mods for conflicts
- Run compatibility checks
- Auto-rollback on errors
- Report results to dashboard
```

**Prompt**: "Setup public Internet access"
```
- Configure HTTPS with Caddy
- Enable strong authentication
- Use Tailscale/ngrok for tunnel
- Monitor /api/status endpoint
- Setup automated backups
```

---

## 💡 Pro Tips

### Real-Time Variable Changes
Variables don't require server restart. Perfect for:
- Testing different difficulty levels
- Adjusting catch limits mid-run
- Tweaking trainer difficulty
- Balancing XP gains

### Batch Configuration
Edit `game_variables.json` directly for bulk changes:
```bash
# Backup first
cp game_variables.json game_variables.json.bak

# Edit variables
nano game_variables.json

# Reload via web UI
curl http://localhost:8765/api/variables
```

### Mod Organization
Structure mods.json for easy management:
```json
{
  "enabled": [
    {"name": "core-mod", "url": "...", "version": "1.0"},
    {"name": "difficulty-mod", "url": "...", "version": "2.1"}
  ],
  "disabled": [
    {"name": "experimental-mod", "url": "...", "reason": "testing"}
  ]
}
```

### Docker Maintenance
```bash
# View all images
docker images | grep rogueserver

# Clean up old images
docker image prune

# Reset everything
docker system prune -a

# Rebuild after code changes
docker build -t rogueserver:dev .
```

---

## 📞 Support Resources

### Check These First
1. **Logs**: `tail -f host.log`
2. **Status**: `python3 desktop_host.py --check`
3. **Docker**: `docker compose logs`
4. **Network**: `ping <IP>` and `netstat -tulpn | grep 8765`

### Common Solutions
- **Port conflict**: Change `dashboard_port` in host.ini
- **Auth issues**: Reset `admin_token` in host.ini
- **Connection issues**: Use correct LAN IP, check firewall
- **Service failure**: Restart Docker: `docker compose down && docker compose up`

### Documentation
- See **ENHANCED_HOST_README.md** for full feature list
- See **IPHONE_LAN_GUIDE.md** for mobile access
- See **PROJECT_SUMMARY.md** for architecture details

---

## 🎉 You're Ready!

Your PokéRogue server is now:
✓ Running on your desktop
✓ Accessible from iPhone on the same WiFi
✓ Configured with real-time game variables
✓ Prepared for mod management
✓ Logging all operations comprehensively

**Next Command**:
```bash
python3 desktop_host.py
```

Then open `http://localhost:8765` in your browser.

**Enjoy hosting!** 🚀

---

**Version**: 1.0
**Last Updated**: 2026-10-06
**Status**: ✓ Production Ready
