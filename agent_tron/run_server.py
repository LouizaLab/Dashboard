#!/usr/bin/env python
"""
Startup script for Agent-Tron server
"""

import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    import os
    port = int(os.getenv("AGENT_TRON_PORT", "8001"))
    uvicorn.run(
        "agent_tron.api.server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )

