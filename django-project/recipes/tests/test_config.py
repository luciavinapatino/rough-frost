"""
Test configuration and utilities for the test suite.
"""
from django.test import TestCase, override_settings
from django.core.management import call_command
import tempfile
import os


class TestConfigMixin:
    """Mixin class for test configuration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class configuration."""
        super().setUpClass()
        # Use in-memory database for faster tests
        # This is handled by Django's TestCase by default
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after test class."""
        super().tearDownClass()


class MediaRootTestCase(TestCase):
    """TestCase that uses a temporary media root for file uploads."""
    
    def setUp(self):
        """Set up temporary media root."""
        super().setUp()
        self.temp_media_root = tempfile.mkdtemp()
        self.settings_override = override_settings(
            MEDIA_ROOT=self.temp_media_root
        )
        self.settings_override.enable()
    
    def tearDown(self):
        """Clean up temporary media root."""
        import shutil
        self.settings_override.disable()
        shutil.rmtree(self.temp_media_root, ignore_errors=True)
        super().tearDown()



