#!/usr/bin/env python3
"""
Launch script for Phase 4 Dashboard
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase4_dashboard import Phase4Dashboard, create_interactive_dashboard

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'html'
    
    if mode == 'interactive':
        print("🚀 Launching interactive dashboard...")
        print("   Open http://localhost:8050 in your browser")
        print("   Press Ctrl+C to stop")
        app = create_interactive_dashboard()
        app.run_server(debug=True, port=8050)
    else:
        print("📊 Generating static HTML dashboard...")
        dashboard = Phase4Dashboard()
        dashboard.generate_dashboard_html()
        print("\n✅ Dashboard generated!")
        print("   Open phase4_output/dashboard.html in your browser")
        print("\n   For interactive dashboard, run:")
        print("   python launch_dashboard.py interactive")

if __name__ == '__main__':
    main()

