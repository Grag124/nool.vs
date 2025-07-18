#!/usr/bin/env python3
"""
Ice Butterfly Monitor Bot
A Discord bot that monitors taming.io shop for the Ice Butterfly pet using image recognition.
"""

import asyncio
import threading
import signal
import sys
import os
from datetime import datetime

from config import Config
from utils import setup_logging, create_reference_image_if_missing
from discord_bot import IceButterflyBot
from web_interface import run_web_interface, update_bot_status

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def validate_environment():
    """Validate environment and configuration"""
    logger = setup_logging(Config.LOG_LEVEL)
    
    # Validate configuration
    config_errors = Config.validate()
    if config_errors:
        logger.error("Configuration validation failed:")
        for error in config_errors:
            logger.error(f"  - {error}")
        return False
    
    # Create reference image if missing
    create_reference_image_if_missing(logger)
    
    # Check for required files
    required_files = [Config.REFERENCE_IMAGE_PATH]
    for file_path in required_files:
        if not os.path.exists(file_path):
            logger.error(f"Required file not found: {file_path}")
            return False
    
    logger.info("Environment validation successful")
    return True

def start_web_interface():
    """Start the web interface in a separate thread"""
    logger = setup_logging(Config.LOG_LEVEL)
    
    try:
        logger.info(f"Starting web interface on {Config.WEB_HOST}:{Config.WEB_PORT}")
        run_web_interface()
    except Exception as e:
        logger.error(f"Error starting web interface: {str(e)}")

def main():
    """Main entry point"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Setup logging
    logger = setup_logging(Config.LOG_LEVEL)
    
    logger.info("=" * 60)
    logger.info("Ice Butterfly Monitor Bot Starting")
    logger.info("=" * 60)
    
    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        return 1
    
    # Start web interface in background thread
    web_thread = threading.Thread(target=start_web_interface, daemon=True)
    web_thread.start()
    
    # Create and start Discord bot
    try:
        bot = IceButterflyBot()
        
        # Update web interface with bot status
        update_bot_status({
            "active": True,
            "start_time": datetime.now(),
            "checks_performed": 0,
            "last_check": None,
            "errors": [],
            "ice_butterfly_found": False,
            "last_screenshot": None
        })
        
        logger.info("Starting Discord bot...")
        bot.run(Config.DISCORD_BOT_TOKEN)
        
    except Exception as e:
        logger.error(f"Error running Discord bot: {str(e)}")
        return 1
    
    logger.info("Bot shutdown complete")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
