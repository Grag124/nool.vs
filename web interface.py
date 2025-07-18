from flask import Flask, render_template, jsonify, request
import logging
import os
from datetime import datetime
import json

from config import Config
from utils import get_timestamp, format_duration

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

# Global variables to store bot state
bot_status = {
    "active": False,
    "start_time": None,
    "checks_performed": 0,
    "last_check": None,
    "errors": [],
    "ice_butterfly_found": False,
    "last_screenshot": None
}

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    """Get current bot status"""
    status = bot_status.copy()
    
    if status["start_time"]:
        status["duration"] = format_duration(
            int((datetime.now() - status["start_time"]).total_seconds())
        )
    else:
        status["duration"] = "Not started"
    
    status["current_time"] = get_timestamp()
    
    return jsonify(status)

@app.route('/api/logs')
def get_logs():
    """Get recent log entries"""
    logs = []
    
    # Try to read from log file if it exists
    log_file = "bot.log"
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                # Get last 100 lines
                logs = [line.strip() for line in lines[-100:] if line.strip()]
        except Exception as e:
            logs = [f"Error reading log file: {str(e)}"]
    else:
        logs = ["No log file found"]
    
    return jsonify({"logs": logs})

@app.route('/api/config')
def get_config():
    """Get current configuration"""
    config = {
        "monitoring_interval": Config.MONITORING_INTERVAL,
        "status_update_interval": Config.STATUS_UPDATE_INTERVAL,
        "match_threshold": Config.MATCH_THRESHOLD,
        "headless_mode": Config.HEADLESS_MODE,
        "game_url": Config.GAME_URL,
        "discord_channel": Config.DISCORD_CHANNEL_NAME
    }
    
    return jsonify(config)

@app.route('/api/screenshot')
def get_screenshot():
    """Get latest screenshot info"""
    screenshot_info = {
        "available": False,
        "path": None,
        "timestamp": None
    }
    
    if bot_status["last_screenshot"] and os.path.exists(bot_status["last_screenshot"]):
        screenshot_info["available"] = True
        screenshot_info["path"] = bot_status["last_screenshot"]
        screenshot_info["timestamp"] = get_timestamp()
    
    return jsonify(screenshot_info)

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": get_timestamp(),
        "bot_active": bot_status["active"]
    })

def update_bot_status(status_update: dict):
    """Update bot status from external source"""
    bot_status.update(status_update)

def run_web_interface():
    """Run the web interface"""
    app.run(host=Config.WEB_HOST, port=Config.WEB_PORT, debug=False)

if __name__ == "__main__":
    run_web_interface()
