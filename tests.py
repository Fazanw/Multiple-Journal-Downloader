import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from core.parser import extract_doi, extract_all_dois_from_text
from core.downloader import UnpaywallDownloader

class TestAppComponents(unittest.TestCase):
    
    # --- PARSER TESTS ---
    def test_extract_doi_clean(self):
        """Test extraction of a clean, standard DOI"""
        text = "10.1038/s41586-020-2649-2"
        self.assertEqual(extract_doi([text]), "10.1038/s41586-020-2649-2")

    def test_extract_doi_messy_url(self):
        """Test extraction of a DOI embedded in a messy URL string"""
        text = "https://dx.doi.org/10.1109/CVPR.2016.90?query=true"
        self.assertEqual(extract_doi([text]), "10.1109/CVPR.2016.90")

    def test_extract_doi_not_found(self):
        """Test extraction when no DOI exists"""
        text = "Just a normal title without a DOI"
        self.assertIsNone(extract_doi([text]))

    def test_extract_all_dois_from_raw_text(self):
        """Test extracting multiple DOIs from raw text"""
        text = "Here is one 10.1234/abc and another https://doi.org/10.5678/xyz."
        dois = extract_all_dois_from_text(text)
        self.assertEqual(len(dois), 2)
        self.assertIn("10.1234/abc", dois)
        self.assertIn("10.5678/xyz", dois)

    # --- DOWNLOADER TESTS ---
    def test_filename_sanitization(self):
        """Test that forbidden OS characters are stripped from filenames"""
        downloader = UnpaywallDownloader()
        messy_title = 'A Paper: "Analysis" / Review <2023> | Part *1?'
        clean_title = downloader.sanitize_filename(messy_title)
        self.assertEqual(clean_title, "A Paper Analysis  Review 2023  Part 1.pdf")
        
        # Test length truncation
        long_title = "A" * 200
        clean_long = downloader.sanitize_filename(long_title)
        self.assertEqual(len(clean_long), 154)  # 150 chars + ".pdf"

    @patch('core.downloader.asyncio.sleep', new_callable=AsyncMock)
    def test_downloader_retry_logic(self, mock_sleep):
        """Test that the downloader properly retries on 500 errors"""
        downloader = UnpaywallDownloader()
        
        # Create a mock session that returns 500 twice, then 200
        mock_session = MagicMock()
        mock_response_500 = AsyncMock()
        mock_response_500.status = 500
        
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={"success": True})
        
        # Define the side effect for the session.get context manager
        mock_session.get.return_value.__aenter__.side_effect = [
            mock_response_500, 
            mock_response_500, 
            mock_response_200
        ]
        
        async def run_test():
            result = await downloader._get_with_retry(mock_session, "http://fake-api.com", retries=3)
            # Should ultimately succeed and return the json
            self.assertEqual(result, {"success": True})
            # Should have slept twice due to the two 500 errors
            self.assertEqual(mock_sleep.call_count, 2)
            
        asyncio.run(run_test())

    def test_cancellation_token(self):
        """Test that the cancel event immediately stops execution"""
        downloader = UnpaywallDownloader()
        downloader.cancel_event.set()
        
        async def run_test():
            # fetch_pdf_url should return None instantly if cancelled
            result = await downloader.fetch_pdf_url(MagicMock(), "10.1234/test")
            self.assertIsNone(result)
            
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main(verbosity=2)
