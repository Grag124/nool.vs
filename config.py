import os
from typing import Optional

class Config:
    """Configuration settings for the Ice Butterfly Monitor Bot"""
    
    # Discord Configuration
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")
    DISCORD_CHANNEL_NAME: str = os.getenv("DISCORD_CHANNEL_NAME", "general")
    
    # Monitoring Configuration
    MONITORING_INTERVAL: int = int(os.getenv("MONITORING_INTERVAL", "10"))  # seconds
    STATUS_UPDATE_INTERVAL: int = int(os.getenv("STATUS_UPDATE_INTERVAL", "600"))  # 10 minutes
    
    # Browser Configuration
    HEADLESS_MODE: bool = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30"))
    
    # Image Recognition Configuration
    MATCH_THRESHOLD: float = float(os.getenv("MATCH_THRESHOLD", "0.8"))
    REFERENCE_IMAGE_PATH: str = os.getenv("REFERENCE_IMAGE_PATH", "ice_butterfly_reference.png")
    
    # Game Configuration
    GAME_URL: str = os.getenv("GAME_URL", "https://taming.io")
    
    # Web Interface Configuration
    WEB_PORT: int = int(os.getenv("WEB_PORT", "5000"))
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not cls.DISCORD_BOT_TOKEN:
            errors.append("DISCORD_BOT_TOKEN is required")
        
        if cls.MONITORING_INTERVAL < 1:
            errors.append("MONITORING_INTERVAL must be at least 1 second")
        
        if cls.MATCH_THRESHOLD < 0 or cls.MATCH_THRESHOLD > 1:
            errors.append("MATCH_THRESHOLD must be between 0 and 1")
        
        return errors
    
    @classmethod
    def get_chrome_options(cls):
        """Get Chrome options for selenium"""
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        
        if cls.HEADLESS_MODE:
            chrome_options.add_argument('--headless')
        
        # Standard Chrome options for containerized environments
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # User agent to avoid detection
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        return chrome_options
