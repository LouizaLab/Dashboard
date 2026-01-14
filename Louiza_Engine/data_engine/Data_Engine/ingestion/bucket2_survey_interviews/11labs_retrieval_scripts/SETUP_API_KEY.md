# Setting Up ElevenLabs API Key

## Step 1: Get Your API Key from ElevenLabs

1. Go to [ElevenLabs Dashboard](https://elevenlabs.io/app/settings/api-keys)
2. Sign in to your account
3. Navigate to **Settings** → **API Keys**
4. Click **"Create API Key"** or copy an existing key
5. **Important**: Copy the key immediately - you won't be able to see it again!

## Step 2: Set the API Key

### Option A: Temporary (Current Terminal Session)

```bash
export ELEVENLABS_API_KEY="your-api-key-here"
```

This only works for the current terminal session. When you close the terminal, you'll need to set it again.

### Option B: Permanent (Recommended)

**For macOS/Linux (zsh/bash):**

1. Open your shell profile file:
   ```bash
   # For zsh (default on newer Macs)
   nano ~/.zshrc
   
   # OR for bash
   nano ~/.bashrc
   ```

2. Add this line at the end:
   ```bash
   export ELEVENLABS_API_KEY="your-api-key-here"
   ```

3. Save and exit (Ctrl+X, then Y, then Enter)

4. Reload your shell:
   ```bash
   source ~/.zshrc
   # OR
   source ~/.bashrc
   ```

**For Windows (PowerShell):**

```powershell
# Set for current session
$env:ELEVENLABS_API_KEY="your-api-key-here"

# Set permanently (run as Administrator)
[System.Environment]::SetEnvironmentVariable('ELEVENLABS_API_KEY', 'your-api-key-here', 'User')
```

### Option C: Use a .env File (Most Secure)

1. Create a `.env` file in the repo root:
   ```bash
   echo "ELEVENLABS_API_KEY=your-api-key-here" > .env
   ```

2. Add `.env` to `.gitignore` (so you don't commit your key):
   ```bash
   echo ".env" >> .gitignore
   ```

3. Install python-dotenv:
   ```bash
   pip install python-dotenv
   ```

4. Modify `fetch_transcripts.py` to load from .env (or use the --api-key flag)

## Step 3: Verify It's Set

Check if the key is set:

```bash
echo $ELEVENLABS_API_KEY
```

You should see your API key (or nothing if it's not set).

## Step 4: Test the Script

Run the script to verify it works:

```bash
python scripts/fetch_transcripts.py --verbose
```

If you see "Invalid API key" error, double-check:
- The key is correct (no extra spaces)
- The environment variable is set (`echo $ELEVENLABS_API_KEY`)
- You've reloaded your shell after setting it

## Quick Setup Script

Run this to set it up quickly:

```bash
# Get your API key from ElevenLabs dashboard first, then:
read -sp "Enter your ElevenLabs API key: " API_KEY
echo ""
echo "export ELEVENLABS_API_KEY=\"$API_KEY\"" >> ~/.zshrc
source ~/.zshrc
echo "✅ API key set! Run: python scripts/fetch_transcripts.py"
```

## Security Notes

⚠️ **Never commit your API key to git!**

- Always add `.env` to `.gitignore` if using .env files
- Don't paste your API key in public places
- If you accidentally commit it, rotate the key immediately in ElevenLabs dashboard

## Troubleshooting

**"ELEVENLABS_API_KEY not set"**
- Make sure you've exported it: `export ELEVENLABS_API_KEY="..."`
- Reload your shell: `source ~/.zshrc`
- Or use the `--api-key` flag: `python scripts/fetch_transcripts.py --api-key "your-key"`

**"Invalid API key"**
- Check the key is correct (copy-paste from ElevenLabs dashboard)
- Make sure there are no extra spaces
- Verify the key hasn't expired or been revoked

**Key not persisting**
- Make sure you added it to `~/.zshrc` (not just exported in terminal)
- Reload shell: `source ~/.zshrc`
- Check it's there: `grep ELEVENLABS_API_KEY ~/.zshrc`

