# Enhanced RogueServer Desktop Host Control Panel

## Overview

This enhanced version of the desktop control panel provides a comprehensive, modular hosting solution for PokéRogue servers with real-time configuration management, mod support, and game variable editing.

## Features

### 1. **Multi-Window Dashboard**
   - **Dashboard** (`/`): Overview of server status and quick links
   - **Configuration Editor** (`/editor`): Manage server settings (ports, URLs, launch commands)
   - **Game Variables Editor** (`/variables`): Adjust game mechanics in real-time
   - **Mod Manager** (`/mods`): Manage mods, hacks, and user scripts

### 2. **Game Variables Management**
Real-time editing of game configuration:
- `pokemonCatchLimit`: Maximum catchable Pokémon (default: 999)
- `maxLevel`: Maximum Pokémon level (default: 100)
- `difficultyMultiplier`: Game difficulty scaling (default: 1.0)
- `experienceMultiplier`: Experience gain multiplier (default: 1.0)
- `enableRandomEvents`: Toggle random events
- `enableTrainerScaling`: Scale trainer difficulty
- `allowSwitching`: Allow mid-battle switching
- `startingPokemonLevel`: Initial level
- `basePokemonStats`: Stats configuration
- `trainerDifficulty`: Trainer difficulty level

All variables are persisted to `game_variables.json` and can be modified without restarting.

### 3. **Mod Management System**
Track and manage:
- **Enabled Mods**: Active modifications (from GitHub repos, local hacks)
- **Disabled Mods**: Mods ready to activate
- **User Scripts**: Scripts from GreasyFork and other sources
- **Metadata**: Tracking information

### 4. **API Endpoints**
- `GET /api/status` - JSON server status and URLs
- `GET /api/config` - Server configuration (excluding admin token)
- `GET /api/variables` - Current game variables
- `GET /api/mods` - Installed mods and scripts

### 5. **Enhanced Error Handling & Logging**
- Comprehensive logging to `host.log`
- All errors caught and logged without crashing the dashboard
- Exception details captured for debugging
- Server remains accessible even if services fail

### 6. **Multi-Machine Access**
- Configure `host = 0.0.0.0` to access from iPhone/other devices on LAN
- Auto-detects public LAN IP
- Dashboard URLs provided for easy access from any device

## Usage

### Quick Start

```bash
cp host.ini.example host.ini
python3 desktop_host.py
```

### Configuration

**host.ini** settings:
```ini
[host]
host = 0.0.0.0                                    # Bind address for LAN access
dashboard_port = 8765                             # Dashboard port
game_url = http://localhost:8000                  # Game server URL
server_url = http://localhost:8001                # API server URL
launch_command = docker compose -f docker-compose.Development.yml up --build
stop_command = docker compose -f docker-compose.Development.yml down
admin_token = your-secret-token                   # Required to save changes
```

### Game Variables

Edit `game_variables.json` directly or via `/variables` UI:
```json
{
  "pokemonCatchLimit": 999,
  "maxLevel": 100,
  "difficultyMultiplier": 1.0,
  "experienceMultiplier": 1.0,
  "enableRandomEvents": true,
  "enableTrainerScaling": true,
  "allowSwitching": true,
  "startingPokemonLevel": 5,
  "basePokemonStats": "normal",
  "trainerDifficulty": "normal"
}
```

### Mods Configuration

Edit `mods.json` directly or via `/mods` UI:
```json
{
  "enabled": [
    {"name": "my-mod", "url": "https://github.com/user/pokerogue-mod"}
  ],
  "disabled": [],
  "userScripts": [
    {"name": "script-name", "url": "https://greasyfork.org/scripts/..."}
  ],
  "metadata": {
    "lastUpdated": "2026-10-06",
    "version": "1.0"
  }
}
```

## Architecture

### Files Generated/Modified

1. **desktop_host.py** (Enhanced)
   - Multi-endpoint HTTP server
   - Variable and mod management
   - Comprehensive error handling
   - Improved Tk GUI with multiple buttons

2. **game_variables.json** (New)
   - Persistent game configuration
   - Automatically created if missing
   - Can be edited via UI or directly

3. **mods.json** (New)
   - Mod tracking and management
   - Automatically created if missing
   - Supports enabled/disabled/user-scripts

4. **host.log** (Enhanced)
   - All errors caught and logged
   - Server continues running
   - Full stack traces for debugging

## Network Access

### Local Machine
- Dashboard: `http://localhost:8765`
- Editor: `http://localhost:8765/editor`
- Variables: `http://localhost:8765/variables`
- Mods: `http://localhost:8765/mods`

### iPhone/Other Devices (Same LAN)
1. Find your PC's LAN IP: `ipconfig getifaddr en0` (macOS) or `hostname -I` (Linux)
2. Access dashboard: `http://<PC_IP>:8765`
3. Access editor: `http://<PC_IP>:8765/editor`
4. Access variables: `http://<PC_IP>:8765/variables`
5. Access mods: `http://<PC_IP>:8765/mods`

### Public Internet
For Internet access:
1. Configure your router for port forwarding (ports 8765, 8000, 8001)
2. **IMPORTANT**: Set a strong `admin_token` in `host.ini`
3. Use a tunnel service (ngrok, Tailscale) for privacy

## Security Notes

- Set `admin_token` before exposing beyond your LAN
- Admin token required for all POST operations (save changes)
- Token uses `secrets.compare_digest()` for timing-attack resistance
- Configuration stored locally, no external credentials required
- Supabase/Notion optional; not required for basic functionality

## Verification

### Pre-Launch Checks
```bash
python3 desktop_host.py --check
```
Output shows all URLs and configuration.

### Log Monitoring
```bash
tail -f host.log
```
Real-time view of server operations and errors.

## Error Recovery

If Docker/Go/MariaDB fails:
- Dashboard remains accessible at `http://localhost:8765`
- All errors logged with full stack traces
- Retry button allows restarting services
- Configuration can be modified for next launch
- No manual intervention needed

## Integration with Existing Systems

### Mod Sources Supported
- **GitHub**: Custom mods and hacks
- **GreasyFork**: User scripts for PokéRogue
- **Local**: Git clones or ZIP extractions

### Customization
- Add more variables in `game_variables.json`
- Extend mod manager with additional metadata
- Modify Tk GUI buttons for custom workflows
- Add new API endpoints as needed

## Changelog

### Version 1.0 (Initial Release)
- ✓ Multi-endpoint HTTP dashboard
- ✓ Game variables real-time editor
- ✓ Mod manager interface
- ✓ Comprehensive error logging
- ✓ Modular architecture for easy extension
- ✓ Support for iPhone access via LAN
- ✓ Configuration persistence (INI, JSON)
- ✓ Enhanced Tk GUI with multiple buttons

## Future Enhancements

- [ ] Web-based GUI (no Tk dependency)
- [ ] Database migration from Supabase
- [ ] Notion integration for documentation
- [ ] Automated mod updates from GitHub
- [ ] Real-time player monitoring dashboard
- [ ] Remote backup/restore functionality
- [ ] Performance metrics and analytics

---

**License**: AGPL v3 (same as rogueserver)
**Author**: Enhanced for modular, multi-window desktop hosting
**Last Updated**: 2026-10-06
