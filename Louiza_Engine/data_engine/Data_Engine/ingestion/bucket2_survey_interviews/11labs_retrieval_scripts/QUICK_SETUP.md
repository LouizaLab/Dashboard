# Quick Setup - Add Your API Key

I see you added your API key to the documentation file, but you need to actually **set it as an environment variable**.

## Quick Fix (Choose One):

### Option 1: Set it now (temporary - for testing)

Open your terminal and run:

```bash
export ELEVENLABS_API_KEY="c69d24452a72ca7415664d661fbf11aef7f38ba4911a5788681f3ecd69c8c25a"
```

Then test it:
```bash
python scripts/fetch_transcripts.py
```

### Option 2: Set it permanently (recommended)

Add it to your shell profile so it's always available:

```bash
# Open your shell profile
nano ~/.zshrc

# Add this line at the end:
export ELEVENLABS_API_KEY="c69d24452a72ca7415664d661fbf11aef7f38ba4911a5788681f3ecd69c8c25a"

# Save: Ctrl+X, then Y, then Enter

# Reload:
source ~/.zshrc
```

### Option 3: Use the setup script

```bash
bash scripts/setup_api_key.sh
```

When prompted, paste: `c69d24452a72ca7415664d661fbf11aef7f38ba4911a5788681f3ecd69c8c25a`

## Verify It's Set

```bash
echo $ELEVENLABS_API_KEY
```

You should see your API key (or it will be hidden but set).

## Important Security Note

⚠️ **Remove your API key from SETUP_API_KEY.md** - that file might be committed to git!

The API key should only be:
- ✅ In your environment variable (`~/.zshrc`)
- ✅ In a `.env` file (which is gitignored)
- ❌ NOT in documentation files that might be committed

