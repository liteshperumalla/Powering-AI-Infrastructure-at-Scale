// Debug script to test frontend API client behavior
// Run this in the browser console at http://localhost:3000/reports

async function debugFrontendReports() {
    console.log('🔍 Starting Frontend Reports Debug');
    
    try {
        // Test 1: Direct API call
        console.log('\n1️⃣ Testing direct API call to backend...');
        const response = await fetch('http://localhost:8000/api/v1/assessments/');
        const data = await response.json();
        console.log('✅ Direct API Response:', data);
        console.log(`Found ${data.assessments?.length || 0} assessments`);
        
        // Test 2: Check Redux store state
        console.log('\n2️⃣ Checking Redux store state...');
        if (window.__REDUX_DEVTOOLS_EXTENSION__) {
            console.log('Redux DevTools available');
        }
        
        // Test 3: Check if apiClient is available globally
        console.log('\n3️⃣ Checking if apiClient is available...');
        if (typeof window !== 'undefined' && window.apiClient) {
            console.log('✅ apiClient available globally');
        } else {
            console.log('❌ apiClient not available globally');
        }
        
        // Test 4: Manual API client simulation
        console.log('\n4️⃣ Simulating frontend API client behavior...');
        
        // Get all assessments
        const assessmentsUrl = 'http://localhost:8000/api/v1/assessments/';
        const assessmentsResponse = await fetch(assessmentsUrl);
        const assessmentsData = await assessmentsResponse.json();
        console.log('Assessments data:', assessmentsData);
        
        // Get reports for each assessment
        const allReports = [];
        for (const assessment of assessmentsData.assessments || []) {
            const reportsUrl = `http://localhost:8000/api/v1/reports/${assessment.id}`;
            console.log(`Fetching reports from: ${reportsUrl}`);
            
            try {
                const reportsResponse = await fetch(reportsUrl);
                if (reportsResponse.ok) {
                    const reportsData = await reportsResponse.json();
                    console.log(`Reports for ${assessment.id}:`, reportsData);
                    allReports.push(...(reportsData.reports || []));
                } else {
                    console.error(`Failed to fetch reports for ${assessment.id}: ${reportsResponse.status}`);
                }
            } catch (error) {
                console.error(`Error fetching reports for ${assessment.id}:`, error);
            }
        }
        
        console.log(`\n✅ Total reports found: ${allReports.length}`);
        console.log('All reports:', allReports);
        
        // Test 5: Check CORS headers
        console.log('\n5️⃣ Checking CORS headers...');
        const corsTest = await fetch('http://localhost:8000/api/v1/assessments/', {
            method: 'HEAD',
            headers: {
                'Origin': 'http://localhost:3000'
            }
        });
        console.log('CORS headers:', [...corsTest.headers.entries()]);
        
    } catch (error) {
        console.error('❌ Debug failed:', error);
        console.error('Error details:', {
            message: error.message,
            stack: error.stack
        });
    }
}

// Run the debug
debugFrontendReports();