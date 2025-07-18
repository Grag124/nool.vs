import cv2
import numpy as np
import os
from typing import Tuple, Optional
import logging

class ImageRecognition:
    """Handles image recognition for detecting Ice Butterfly in shop screenshots"""
    
    def __init__(self, reference_image_path: str, threshold: float = 0.8, logger: Optional[logging.Logger] = None):
        self.reference_image_path = reference_image_path
        self.threshold = threshold
        self.logger = logger or logging.getLogger(__name__)
        self.reference_image = None
        
        self._load_reference_image()
    
    def _load_reference_image(self) -> None:
        """Load the reference image for Ice Butterfly"""
        try:
            if not os.path.exists(self.reference_image_path):
                self.logger.error(f"Reference image not found: {self.reference_image_path}")
                return
            
            self.reference_image = cv2.imread(self.reference_image_path)
            if self.reference_image is None:
                self.logger.error(f"Failed to load reference image: {self.reference_image_path}")
                return
            
            self.logger.info(f"Reference image loaded successfully: {self.reference_image.shape}")
            
        except Exception as e:
            self.logger.error(f"Error loading reference image: {str(e)}")
    
    def detect_ice_butterfly(self, screenshot_path: str) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
        """
        Detect Ice Butterfly in the given screenshot
        
        Returns:
            Tuple of (found, confidence, position)
        """
        try:
            if self.reference_image is None:
                self.logger.warning("Reference image not loaded")
                return False, 0.0, None
            
            if not os.path.exists(screenshot_path):
                self.logger.error(f"Screenshot not found: {screenshot_path}")
                return False, 0.0, None
            
            # Load screenshot
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                self.logger.error(f"Failed to load screenshot: {screenshot_path}")
                return False, 0.0, None
            
            # Perform template matching
            result = cv2.matchTemplate(screenshot, self.reference_image, cv2.TM_CCOEFF_NORMED)
            
            # Find the best match
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Check if match exceeds threshold
            if max_val >= self.threshold:
                self.logger.info(f"Ice Butterfly detected! Confidence: {max_val:.3f} at position {max_loc}")
                return True, max_val, max_loc
            else:
                self.logger.debug(f"Ice Butterfly not found. Best match: {max_val:.3f} (threshold: {self.threshold})")
                return False, max_val, max_loc
            
        except Exception as e:
            self.logger.error(f"Error during image recognition: {str(e)}")
            return False, 0.0, None
    
    def detect_multiple_scales(self, screenshot_path: str) -> Tuple[bool, float, Optional[Tuple[int, int]]]:
        """
        Detect Ice Butterfly using multiple scales for better accuracy
        """
        try:
            if self.reference_image is None or not os.path.exists(screenshot_path):
                return False, 0.0, None
            
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return False, 0.0, None
            
            best_confidence = 0.0
            best_position = None
            
            # Try different scales
            scales = [0.5, 0.75, 1.0, 1.25, 1.5]
            
            for scale in scales:
                # Resize reference image
                width = int(self.reference_image.shape[1] * scale)
                height = int(self.reference_image.shape[0] * scale)
                
                if width <= 0 or height <= 0:
                    continue
                
                resized_ref = cv2.resize(self.reference_image, (width, height))
                
                # Skip if resized image is larger than screenshot
                if resized_ref.shape[0] > screenshot.shape[0] or resized_ref.shape[1] > screenshot.shape[1]:
                    continue
                
                # Perform template matching
                result = cv2.matchTemplate(screenshot, resized_ref, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_position = max_loc
            
            if best_confidence >= self.threshold:
                self.logger.info(f"Ice Butterfly detected (multi-scale)! Best confidence: {best_confidence:.3f}")
                return True, best_confidence, best_position
            else:
                self.logger.debug(f"Ice Butterfly not found (multi-scale). Best confidence: {best_confidence:.3f}")
                return False, best_confidence, best_position
            
        except Exception as e:
            self.logger.error(f"Error during multi-scale detection: {str(e)}")
            return False, 0.0, None
    
    def create_detection_visualization(self, screenshot_path: str, position: Tuple[int, int], output_path: str) -> bool:
        """
        Create a visualization of the detection with bounding box
        """
        try:
            if not os.path.exists(screenshot_path) or self.reference_image is None:
                return False
            
            screenshot = cv2.imread(screenshot_path)
            if screenshot is None:
                return False
            
            # Draw bounding box
            top_left = position
            bottom_right = (
                top_left[0] + self.reference_image.shape[1],
                top_left[1] + self.reference_image.shape[0]
            )
            
            cv2.rectangle(screenshot, top_left, bottom_right, (0, 255, 0), 2)
            
            # Add text
            cv2.putText(screenshot, "Ice Butterfly Found!", 
                       (top_left[0], top_left[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Save visualization
            cv2.imwrite(output_path, screenshot)
            self.logger.info(f"Detection visualization saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating detection visualization: {str(e)}")
            return False
