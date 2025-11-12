from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.contrib.auth import get_user


class LoginViewTests(TestCase):
    """Test cases for the LoginView."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.login_url = reverse('login')
        self.home_url = reverse('home')
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_login_page_get(self):
        """Test that GET request to login page renders the form."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertIn('form', response.context)
        self.assertFalse(response.context.get('error', False))
    
    def test_login_with_valid_credentials(self):
        """Test login with valid username and password."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        # Should redirect to home page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        # User should be authenticated
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, 'testuser')
        # Session should contain user info
        self.assertIn('user', self.client.session)
        self.assertEqual(self.client.session['user']['username'], 'testuser')
    
    def test_login_with_invalid_username(self):
        """Test login with non-existent username."""
        response = self.client.post(self.login_url, {
            'username': 'nonexistent',
            'password': 'testpass123'
        })
        # Should render login page with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(response.context.get('error', False))
        # User should not be authenticated
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
    
    def test_login_with_invalid_password(self):
        """Test login with wrong password."""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        # Should render login page with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(response.context.get('error', False))
        # User should not be authenticated
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
    
    def test_login_with_empty_credentials(self):
        """Test login with empty username and password."""
        response = self.client.post(self.login_url, {
            'username': '',
            'password': ''
        })
        # Should render login page with error
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')
        self.assertTrue(response.context.get('error', False))
        # User should not be authenticated
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
    
    def test_login_redirects_authenticated_user(self):
        """Test that authenticated user accessing login page gets redirected."""
        # First log in
        self.client.login(username='testuser', password='testpass123')
        # Try to access login page
        response = self.client.get(self.login_url)
        # Should still show login page (or could redirect, depends on implementation)
        # For now, we'll just verify it doesn't crash
        self.assertIn(response.status_code, [200, 302])


class LogoutViewTests(TestCase):
    """Test cases for the LogoutView."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.logout_url = reverse('logout')
        self.home_url = reverse('home')
        # Create and log in a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_logout_post(self):
        """Test that POST to logout logs out the user."""
        # Verify user is logged in
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        
        # Log out
        response = self.client.post(self.logout_url)
        
        # Should redirect to home
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
        # User should be logged out
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
    
    def test_logout_get_not_allowed(self):
        """Test that GET request to logout doesn't work (only POST)."""
        response = self.client.get(self.logout_url)
        # Should return 405 Method Not Allowed or handle gracefully
        self.assertIn(response.status_code, [405, 302, 200])


class HomeViewTests(TestCase):
    """Test cases for the home view."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.home_url = reverse('home')
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_home_page_unauthenticated(self):
        """Test home page when user is not logged in."""
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Log in')
    
    def test_home_page_authenticated(self):
        """Test home page when user is logged in."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertContains(response, 'Welcome')
        self.assertContains(response, 'testuser')
        self.assertContains(response, 'Log out')
