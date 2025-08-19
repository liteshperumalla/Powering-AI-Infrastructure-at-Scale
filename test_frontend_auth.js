// Test script to manually set auth token in browser localStorage
// This simulates a successful login and allows testing the dashboard data loading

console.log('🔐 Testing Frontend Authentication...');

// First, let's get a fresh token from the API
fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        email: 'liteshperumalla@gmail.com',
        password: 'Litesh@#12345'
    })
})
.then(response => response.json())
.then(data => {
    if (data.access_token) {
        console.log('✅ Got auth token:', data.access_token.substring(0, 50) + '...');
        
        // Store the token in localStorage (simulating successful login)
        localStorage.setItem('auth_token', data.access_token);
        console.log('✅ Token stored in localStorage');
        
        // Force page reload to trigger auth initialization
        console.log('🔄 Reloading page to trigger auth state update...');
        window.location.reload();
    } else {
        console.error('❌ Failed to get token:', data);
    }
})
.catch(error => {
    console.error('❌ Login failed:', error);
});