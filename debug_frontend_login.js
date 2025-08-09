// Debug script to test the exact same login request the frontend makes
const fetch = require('node-fetch');

async function debugLogin() {
    console.log('🔧 Testing login request exactly like frontend...');
    
    const API_BASE_URL = 'http://localhost:8000';
    const credentials = {
        email: 'liteshperumalla@gmail.com',
        password: 'Litesh@#12345'
    };
    
    try {
        console.log('📡 Making request to:', `${API_BASE_URL}/api/v1/auth/login`);
        console.log('📦 Payload:', credentials);
        
        const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Client-Version': '2.0.0',
                'X-Request-ID': `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                'Origin': 'http://localhost:3000',
                'Referer': 'http://localhost:3000/auth/login'
            },
            body: JSON.stringify(credentials)
        });
        
        console.log('🚀 Response status:', response.status);
        console.log('📋 Response headers:');
        response.headers.forEach((value, key) => {
            console.log(`  ${key}: ${value}`);
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('✅ Login successful!');
            console.log('🎫 Token received:', data.access_token ? 'YES' : 'NO');
            console.log('👤 User info:', {
                user_id: data.user_id,
                email: data.email,
                full_name: data.full_name
            });
        } else {
            console.log('❌ Login failed');
            console.log('💥 Error:', data);
        }
        
    } catch (error) {
        console.log('💥 Request failed:', error.message);
        console.log('🔍 Error details:', error);
    }
}

// Test connection first
async function testConnection() {
    console.log('🏥 Testing basic connectivity...');
    
    try {
        const response = await fetch('http://localhost:8000/health', {
            headers: {
                'Origin': 'http://localhost:3000'
            }
        });
        
        console.log('✅ Health check:', response.status);
        
        if (response.ok) {
            await debugLogin();
        }
        
    } catch (error) {
        console.log('❌ Cannot connect to backend:', error.message);
        console.log('   Make sure backend is running on port 8000');
    }
}

testConnection();