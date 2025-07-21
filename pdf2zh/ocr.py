"""OCR module for extracting text from images in PDF documents."""

import logging
import io
from typing import Optional, Tuple, List
import numpy as np
from PIL import Image
import cv2

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("pytesseract not available. OCR functionality will be disabled.")

log = logging.getLogger(__name__)


class OCRProcessor:
    """OCR processor for extracting text from images."""
    
    def __init__(self, lang_in: str = "eng"):
        """
        Initialize OCR processor.
        
        Args:
            lang_in: Source language code for OCR (e.g., 'eng', 'chi_sim', 'jpn')
        """
        self.lang_in = lang_in
        self.available = TESSERACT_AVAILABLE
        
        if not self.available:
            log.warning("OCR not available. Install pytesseract to enable OCR functionality.")
    
    def extract_text_from_image_data(self, image_data: bytes, bbox: Tuple[float, float, float, float]) -> Optional[str]:
        """
        Extract text from image data using OCR.
        
        Args:
            image_data: Raw image data bytes
            bbox: Bounding box of the image (x0, y0, x1, y1)
            
        Returns:
            Extracted text or None if extraction fails
        """
        if not self.available:
            return None
            
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL Image to OpenCV format
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR results
            processed_image = self._preprocess_image(cv_image)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                processed_image, 
                lang=self._get_tesseract_lang(),
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Clean up extracted text
            cleaned_text = self._clean_text(text)
            
            if cleaned_text.strip():
                log.debug(f"OCR extracted text from image at {bbox}: {cleaned_text[:50]}...")
                return cleaned_text
            else:
                log.debug(f"No text extracted from image at {bbox}")
                return None
                
        except Exception as e:
            log.warning(f"OCR failed for image at {bbox}: {e}")
            return None
    
    def extract_text_from_page_region(self, page_image: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[str]:
        """
        Extract text from a specific region of a page image.
        
        Args:
            page_image: Full page image as numpy array
            bbox: Bounding box of the region (x0, y0, x1, y1)
            
        Returns:
            Extracted text or None if extraction fails
        """
        if not self.available:
            return None
            
        try:
            x0, y0, x1, y1 = bbox
            h, w = page_image.shape[:2]
            
            # Ensure bbox is within image bounds
            x0 = max(0, min(x0, w-1))
            y0 = max(0, min(y0, h-1))
            x1 = max(x0+1, min(x1, w))
            y1 = max(y0+1, min(y1, h))
            
            # Extract region of interest
            roi = page_image[y0:y1, x0:x1]
            
            if roi.size == 0:
                return None
            
            # Preprocess the region
            processed_roi = self._preprocess_image(roi)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                processed_roi,
                lang=self._get_tesseract_lang(),
                config='--psm 6'  # Assume uniform block of text
            )
            
            # Clean up extracted text
            cleaned_text = self._clean_text(text)
            
            if cleaned_text.strip():
                log.debug(f"OCR extracted text from region {bbox}: {cleaned_text[:50]}...")
                return cleaned_text
            else:
                log.debug(f"No text extracted from region {bbox}")
                return None
                
        except Exception as e:
            log.warning(f"OCR failed for region {bbox}: {e}")
            return None
    
    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Apply denoising
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Apply adaptive thresholding for better text recognition
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        return thresh
    
    def _get_tesseract_lang(self) -> str:
        """
        Convert language code to Tesseract format.
        
        Returns:
            Tesseract language code
        """
        lang_map = {
            'en': 'eng',
            'zh': 'chi_sim',
            'zh-cn': 'chi_sim',
            'zh-tw': 'chi_tra',
            'ja': 'jpn',
            'ko': 'kor',
            'de': 'deu',
            'fr': 'fra',
            'es': 'spa',
            'it': 'ita',
            'ru': 'rus',
            'ar': 'ara',
        }
        return lang_map.get(self.lang_in, 'eng')
    
    def _clean_text(self, text: str) -> str:
        """
        Clean up extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = ' '.join(lines)
        
        return cleaned


# Global OCR processor instance
_ocr_processor: Optional[OCRProcessor] = None


def get_ocr_processor(lang_in: str = "eng") -> OCRProcessor:
    """
    Get or create OCR processor instance.
    
    Args:
        lang_in: Source language code for OCR
        
    Returns:
        OCR processor instance
    """
    global _ocr_processor
    if _ocr_processor is None or _ocr_processor.lang_in != lang_in:
        _ocr_processor = OCRProcessor(lang_in)
    return _ocr_processor