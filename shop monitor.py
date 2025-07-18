import os
import time
import random
import string
from typing import Optional, Tuple
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import undetected_chromedriver as uc

from config import Config
from utils import ensure_directory_exists, generate_screenshot_filename, retry_operation

class ShopMonitor:
    """Handles browser automation and shop monitoring for taming.io"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.driver = None
        self.is_logged_in = False
        self.shop_accessible = False
        self.last_screenshot_path = None
        
        # Create screenshots directory
        ensure_directory_exists("screenshots/")
        
        # Create screenshots directory if it doesn't exist
        os.makedirs("screenshots", exist_ok=True)
    
    def setup_driver(self) -> bool:
        """Setup Chrome driver with undetected-chromedriver"""
        try:
            self.logger.info("Setting up Chrome driver...")
            
            # Use undetected-chromedriver for better Cloudflare bypass
            chrome_options = Config.get_chrome_options()
            
            # Try to use undetected-chromedriver first
            try:
                self.driver = uc.Chrome(options=chrome_options, version_main=None)
                self.logger.info("Undetected Chrome driver initialized successfully")
            except Exception as e:
                self.logger.warning(f"Failed to initialize undetected Chrome driver: {str(e)}")
                
                # Fallback to regular Chrome driver
                try:
                    service = Service('/usr/bin/chromedriver')
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.logger.info("Regular Chrome driver initialized successfully")
                except Exception as e2:
                    self.logger.error(f"Failed to initialize regular Chrome driver: {str(e2)}")
                    return False
            
            # Set window size and timeouts
            self.driver.set_window_size(1920, 1080)
            self.driver.implicitly_wait(Config.BROWSER_TIMEOUT)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up Chrome driver: {str(e)}")
            return False
    
    def navigate_to_game(self) -> bool:
        """Navigate to taming.io"""
        try:
            self.logger.info(f"Navigating to {Config.GAME_URL}")
            self.driver.get(Config.GAME_URL)
            
            # Wait for page to load
            WebDriverWait(self.driver, Config.BROWSER_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.logger.info("Successfully navigated to taming.io")
            return True
            
        except TimeoutException:
            self.logger.error("Timeout waiting for taming.io to load")
            return False
        except Exception as e:
            self.logger.error(f"Error navigating to taming.io: {str(e)}")
            return False
    
    def login_as_guest(self) -> bool:
        """Login as guest user with enhanced detection and wait logic"""
        try:
            self.logger.info("Attempting to login as guest...")
            
            # Wait for page to fully load
            time.sleep(8)
            
            # Take initial screenshot for debugging
            self.driver.save_screenshot("screenshots/initial_page.png")
            
            # Look for play/login buttons with more comprehensive selectors
            play_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'start')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
                "//input[@type='button' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'play')]",
                ".play-button, .play-btn, .start-button, .start-btn",
                "#play-button, #play-btn, #start-button, #start-btn",
                "[data-testid='play-button'], [data-testid='start-button']",
                "button[class*='play'], button[class*='start']",
                "a[class*='play'], a[class*='start']"
            ]
            
            play_button = None
            for selector in play_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        # Check if element is visible and clickable
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                play_button = element
                                self.logger.info(f"Found play button with selector: {selector}")
                                break
                        if play_button:
                            break
                except Exception as e:
                    continue
            
            if play_button:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", play_button)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", play_button)
                time.sleep(5)
                self.logger.info("Clicked play button")
                
                # Take screenshot after clicking play
                self.driver.save_screenshot("screenshots/after_play_click.png")
            
            # Look for guest login options with enhanced selectors
            guest_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guest')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'anonymous')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'continue')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'skip')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guest')]",
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guest')]",
                "//input[@type='button' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'guest')]",
                ".guest-button, .guest-btn, .anonymous-button, .anonymous-btn",
                "#guest-button, #guest-btn, #anonymous-button, #anonymous-btn",
                "[data-testid='guest-button'], [data-testid='anonymous-button']",
                "button[class*='guest'], button[class*='anonymous']",
                "a[class*='guest'], a[class*='anonymous']"
            ]
            
            guest_button = None
            for selector in guest_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        # Check if element is visible and clickable
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                guest_button = element
                                self.logger.info(f"Found guest button with selector: {selector}")
                                break
                        if guest_button:
                            break
                except Exception as e:
                    continue
            
            if guest_button:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", guest_button)
                time.sleep(2)
                self.driver.execute_script("arguments[0].click();", guest_button)
                time.sleep(8)
                self.logger.info("Clicked guest button")
                
                # Take screenshot after guest login
                self.driver.save_screenshot("screenshots/after_guest_login.png")
                
                # Wait for any loading/transition
                time.sleep(5)
                
                self.is_logged_in = True
                return True
            
            # If no guest button found, try to create random account
            self.logger.info("No guest button found, trying to create random account...")
            return self._create_random_account()
            
        except Exception as e:
            self.logger.error(f"Error during guest login: {str(e)}")
            return False
    
    def _create_random_account(self) -> bool:
        """Create a random account if guest login is not available"""
        try:
            self.logger.info("Attempting to create random account...")
            
            # Generate random username
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            
            # Look for username input
            username_selectors = [
                "//input[@type='text']",
                "//input[@placeholder*='name']",
                "//input[@placeholder*='Name']",
                "//input[@placeholder*='username']",
                "//input[@placeholder*='Username']",
                "input[type='text']",
                "input[placeholder*='name']",
                ".username-input",
                "#username"
            ]
            
            username_input = None
            for selector in username_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        username_input = elements[0]
                        self.logger.info(f"Found username input with selector: {selector}")
                        break
                except Exception as e:
                    continue
            
            if username_input:
                username_input.clear()
                username_input.send_keys(username)
                time.sleep(2)
                
                # Look for create/register button
                create_button_selectors = [
                    "//button[contains(text(), 'Create')]",
                    "//button[contains(text(), 'Register')]",
                    "//button[contains(text(), 'Start')]",
                    "//button[contains(text(), 'Continue')]",
                    "//input[@type='submit']",
                    ".create-button",
                    "#create-button"
                ]
                
                for selector in create_button_selectors:
                    try:
                        if selector.startswith("//"):
                            elements = self.driver.find_elements(By.XPATH, selector)
                        else:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                        if elements:
                            create_button = elements[0]
                            self.driver.execute_script("arguments[0].click();", create_button)
                            time.sleep(5)
                            self.logger.info(f"Created account with username: {username}")
                            self.is_logged_in = True
                            return True
                    except Exception as e:
                        continue
            
            self.logger.warning("Could not create random account")
            return False
            
        except Exception as e:
            self.logger.error(f"Error creating random account: {str(e)}")
            return False
    
    def access_shop(self) -> bool:
        """Access the shop/store in the game and navigate to potions section"""
        try:
            self.logger.info("Attempting to access shop...")
            
            # Wait for game to load completely
            time.sleep(15)
            
            # Take screenshot before accessing shop
            self.driver.save_screenshot("screenshots/before_shop_access.png")
            
            # Look for shop/store buttons with enhanced selectors
            shop_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shop')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'store')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'market')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shop')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'store')]",
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shop')]",
                "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'shop')]",
                ".shop-button, .shop-btn, .store-button, .store-btn, .market-button, .market-btn",
                "#shop-button, #shop-btn, #store-button, #store-btn, #market-button, #market-btn",
                "[data-testid='shop-button'], [data-testid='store-button'], [data-testid='market-button']",
                "button[class*='shop'], button[class*='store'], button[class*='market']",
                "a[class*='shop'], a[class*='store'], a[class*='market']",
                "div[class*='shop'], div[class*='store'], div[class*='market']"
            ]
            
            shop_button = None
            for selector in shop_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        # Check if element is visible and clickable
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                shop_button = element
                                self.logger.info(f"Found shop button with selector: {selector}")
                                break
                        if shop_button:
                            break
                except Exception as e:
                    continue
            
            if shop_button:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", shop_button)
                time.sleep(3)
                self.driver.execute_script("arguments[0].click();", shop_button)
                time.sleep(8)
                self.logger.info("Clicked shop button")
                
                # Take screenshot after accessing shop
                self.driver.save_screenshot("screenshots/after_shop_access.png")
                
                # Now navigate to potions section
                if self._navigate_to_potions_section():
                    self.shop_accessible = True
                    return True
                else:
                    self.logger.warning("Could not navigate to potions section")
                    self.shop_accessible = True  # Still consider shop accessible
                    return True
            
            self.logger.warning("Could not find shop button")
            return False
            
        except Exception as e:
            self.logger.error(f"Error accessing shop: {str(e)}")
            return False
    
    def _navigate_to_potions_section(self) -> bool:
        """Navigate to the potions section of the shop where Ice Butterfly is located"""
        try:
            self.logger.info("Attempting to navigate to potions section...")
            
            # Wait for shop to load
            time.sleep(5)
            
            # Look for potions/pets section buttons
            potions_button_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'potion')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pet')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'animal')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'creature')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'butterfly')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'potion')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'pet')]",
                "//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'potion')]",
                "//span[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'potion')]",
                ".potion-button, .potion-btn, .pet-button, .pet-btn, .animal-button, .animal-btn",
                "#potion-button, #potion-btn, #pet-button, #pet-btn, #animal-button, #animal-btn",
                "[data-testid='potion-button'], [data-testid='pet-button'], [data-testid='animal-button']",
                "button[class*='potion'], button[class*='pet'], button[class*='animal']",
                "a[class*='potion'], a[class*='pet'], a[class*='animal']",
                "div[class*='potion'], div[class*='pet'], div[class*='animal']"
            ]
            
            potions_button = None
            for selector in potions_button_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        # Check if element is visible and clickable
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                potions_button = element
                                self.logger.info(f"Found potions button with selector: {selector}")
                                break
                        if potions_button:
                            break
                except Exception as e:
                    continue
            
            if potions_button:
                # Scroll to element and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", potions_button)
                time.sleep(3)
                self.driver.execute_script("arguments[0].click();", potions_button)
                time.sleep(8)
                self.logger.info("Clicked potions section button")
                
                # Take screenshot after accessing potions section
                self.driver.save_screenshot("screenshots/after_potions_access.png")
                
                return True
            else:
                self.logger.info("No specific potions section found, staying in main shop")
                return True
            
        except Exception as e:
            self.logger.error(f"Error navigating to potions section: {str(e)}")
            return False
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot of the current page"""
        try:
            if not self.driver:
                self.logger.error("Driver not initialized")
                return None
            
            screenshot_path = generate_screenshot_filename()
            ensure_directory_exists(screenshot_path)
            
            # Take screenshot
            self.driver.save_screenshot(screenshot_path)
            self.last_screenshot_path = screenshot_path
            
            self.logger.debug(f"Screenshot saved to {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    def monitor_for_ice_butterfly(self) -> bool:
        """Monitor the shop for Ice Butterfly with enhanced detection"""
        try:
            self.logger.info("Starting Ice Butterfly monitoring in potion store...")
            
            # Ensure we're in the potion store section
            if not self._navigate_to_potions_section():
                self.logger.warning("Could not navigate to potions section, monitoring main shop instead")
            
            # Wait for page to load completely
            time.sleep(5)
            
            # Take screenshot for analysis
            screenshot_path = self.take_screenshot()
            if not screenshot_path:
                self.logger.error("Failed to take screenshot for Ice Butterfly detection")
                return False
            
            # Check if Ice Butterfly is present
            from image_recognition import detect_ice_butterfly
            is_found = detect_ice_butterfly(screenshot_path)
            
            if is_found:
                self.logger.info("🦋 ICE BUTTERFLY DETECTED! 🦋")
                return True
            else:
                self.logger.debug("Ice Butterfly not found in current screenshot")
                return False
                
        except Exception as e:
            self.logger.error(f"Error monitoring for Ice Butterfly: {str(e)}")
            return False
    
    def get_shop_status(self) -> dict:
        """Get current shop status information"""
        return {
            "driver_active": self.driver is not None,
            "logged_in": self.is_logged_in,
            "shop_accessible": self.shop_accessible,
            "last_screenshot": self.last_screenshot_path
        }
    
    def restart_session(self) -> bool:
        """Restart the browser session"""
        try:
            self.logger.info("Restarting browser session...")
            
            # Close current driver
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error closing driver: {str(e)}")
            
            # Reset state
            self.driver = None
            self.is_logged_in = False
            self.shop_accessible = False
            
            # Setup new driver
            if not self.setup_driver():
                return False
            
            # Navigate and login
            if not self.navigate_to_game():
                return False
            
            if not self.login_as_guest():
                return False
            
            if not self.access_shop():
                return False
            
            self.logger.info("Browser session restarted successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restarting session: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.logger.info("Shop monitor cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
