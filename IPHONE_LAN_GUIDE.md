# iPhone & LAN Access Guide

## Quick Setup for iPhone Access

### Step 1: Configure for Network Access

Edit `host.ini`:
```ini
[host]
host = 0.0.0.0
dashboard_port = 8765
game_url = http://localhost:8000
server_url = http://localhost:8001
launch_command = docker compose -f docker-compose.Development.yml up --build
stop_command = docker compose -f docker-compose.Development.yml down
admin_token = set_a_strong_password_here
```

**Key Setting**: `host = 0.0.0.0` enables access from any device on your network.

### Step 2: Find Your Desktop's LAN IP

**macOS:**
```bash
ipconfig getifaddr en0
```

**Linux:**
```bash
hostname -I
```

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your active network adapter (e.g., `192.168.x.x`)

### Step 3: Launch the Server

```bash
python3 desktop_host.py
```

The script will:
1. Auto-detect your LAN IP
2. Show dashboard URLs
3. Launch the Docker Compose stack
4. Keep the dashboard running even if errors occur

### Step 4: Access from iPhone

1. Connect iPhone to the **same WiFi network** as your desktop
2. Open Safari and navigate to: `http://<YOUR_PC_IP>:8765`
   - Replace `<YOUR_PC_IP>` with the IP from Step 2
   - Example: `http://192.168.1.50:8765`

### Available URLs on iPhone

Once connected, you can access:

| URL | Purpose |
|-----|---------|
| `http://192.168.x.x:8765/` | Dashboard (status overview) |
| `http://192.168.x.x:8765/editor` | Configuration editor (requires admin token) |
| `http://192.168.x.x:8765/variables` | Game variables editor (requires admin token) |
| `http://192.168.x.x:8765/mods` | Mod manager (requires admin token) |
| `http://192.168.x.x:8765/api/status` | JSON status (machine-readable) |
| `http://192.168.x.x:8001` | Game server API (PokeRogue connects here) |
| `http://192.168.x.x:8000` | Game frontend (if running) |

## Playing PokeRogue on iPhone

### Option 1: Use Official PokeRogue with Custom API

1. Open PokeRogue in Safari on iPhone
2. Look for server configuration options
3. Set API endpoint to: `http://<YOUR_PC_IP>:8001`
4. Start playing

### Option 2: Local HTML Setup (Recommended)

Copy the PokeRogue game files to your desktop and serve via the existing setup:
```bash
# Copy game files to a location Docker can serve
cp -r pokerogue-game/* /path/to/rogueserver/public/
```

Then access at: `http://<YOUR_PC_IP>:8000`

## Modifying Settings on iPhone

### Real-Time Game Variables

Access `http://192.168.x.x:8765/variables` to modify:
- **pokemonCatchLimit**: Max catchable Pokémon (default: 999)
- **maxLevel**: Max Pokémon level (default: 100)
- **difficultyMultiplier**: Difficulty scaling (default: 1.0)
- **experienceMultiplier**: XP gain (default: 1.0)
- And more...

Changes take effect immediately for new games (no restart needed).

### Server Configuration

Access `http://192.168.x.x:8765/editor` to modify:
- Dashboard port
- Game/API server URLs
- Launch/stop commands
- Admin token

⚠️ **Note**: Configuration changes require a server restart to take effect.

### Managing Mods

Access `http://192.168.x.x:8765/mods` to:
- Add mods from GitHub
- Enable/disable modifications
- Import user scripts from GreasyFork
- Track mod versions and updates

## Troubleshooting

### "Cannot connect to server"
- Ensure desktop and iPhone are on **same WiFi**
- Check firewall settings on desktop (ports 8765, 8001, 8000 must be open)
- Verify IP address is correct (run Step 2 again)
- Try pinging the IP: `ping <YOUR_PC_IP>`

### "Admin token required"
- Set `admin_token` in `host.ini`
- Restart `python3 desktop_host.py`
- Enter token when prompted in browser

### "Connection refused"
- Confirm Docker is running: `docker ps`
- Check host.log for errors: `tail -f host.log`
- Restart the script: `python3 desktop_host.py`

### Dashboard shows "server not running"
- Check Docker Compose status: `docker compose -f docker-compose.Development.yml ps`
- View logs: `docker compose -f docker-compose.Development.yml logs`
- Manually start: `docker compose -f docker-compose.Development.yml up --build`

## Security Notes for LAN

✓ **Safe on trusted networks:**
- Set a strong admin_token
- Only expose editor/variables/mods URLs to trusted users
- Use HTTPS tunnel for Internet access

⚠️ **Before exposing to Internet:**
- Set very strong admin_token (20+ characters)
- Use VPN or tunnel service (ngrok, Tailscale, Cloudflare Tunnel)
- Configure firewall rules strictly
- Monitor host.log for suspicious activity
- Do NOT expose without authentication

## Network Diagram

```
iPhone (Safari)
    ↓
WiFi Network
    ↓
Desktop PC (192.168.x.x)
    ├─ dashboard_port 8765 ← HTTP UI & API
    ├─ server_port 8001 ← PokeRogue API
    └─ game_port 8000 ← Game Frontend
         ↓
    Docker Compose
         ├─ Go API Server
         └─ MariaDB Database
```

## Performance Tips

- Keep dashboard open in a separate Safari tab for real-time status
- Batch variable changes before saving
- Use mod manager to disable unused mods
- Monitor CPU/RAM in Docker: `docker stats`
- Check network latency: `ping <YOUR_PC_IP>`

---

**Next Step**: See [ENHANCED_HOST_README.md](ENHANCED_HOST_README.md) for full documentation.
