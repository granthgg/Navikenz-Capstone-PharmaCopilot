#!/usr/bin/env node

/**
 * Test script to verify local report generation API at localhost:8001
 */

const axios = require('axios');

async function testReportAPI() {
  const LOCAL_REPORT_API = 'http://localhost:8001';
  
  console.log('='.repeat(60));
  console.log('Testing Local Report Generation API');
  console.log('='.repeat(60));
  console.log(`Target API: ${LOCAL_REPORT_API}`);
  console.log('');

  // Test 1: Health Check
  console.log('1. Testing Health Check...');
  try {
    const healthResponse = await axios.get(`${LOCAL_REPORT_API}/api/reports/health`, {
      timeout: 10000
    });
    console.log('✅ Health Check: SUCCESS');
    console.log('   Status:', healthResponse.status);
    console.log('   Response:', JSON.stringify(healthResponse.data, null, 2));
  } catch (error) {
    console.log('❌ Health Check: FAILED');
    console.log('   Error:', error.message);
    if (error.response) {
      console.log('   Status:', error.response.status);
      console.log('   Response:', error.response.data);
    }
  }
  console.log('');

  // Test 2: Report Types
  console.log('2. Testing Report Types...');
  try {
    const typesResponse = await axios.get(`${LOCAL_REPORT_API}/api/reports/types`, {
      timeout: 10000
    });
    console.log('✅ Report Types: SUCCESS');
    console.log('   Status:', typesResponse.status);
    console.log('   Available Types:', typesResponse.data.available_report_types?.length || 'Unknown');
  } catch (error) {
    console.log('❌ Report Types: FAILED');
    console.log('   Error:', error.message);
    if (error.response) {
      console.log('   Status:', error.response.status);
    }
  }
  console.log('');

  // Test 3: Report Generation
  console.log('3. Testing Report Generation...');
  try {
    const generateResponse = await axios.post(`${LOCAL_REPORT_API}/api/reports/generate`, {
      report_type: 'quality_control',
      query: 'Generate a test quality control report',
      additional_context: {
        timestamp: new Date().toISOString(),
        source: 'test_script',
        test_mode: true
      }
    }, {
      timeout: 60000, // 1 minute timeout for report generation
      headers: {
        'Content-Type': 'application/json'
      }
    });
    console.log('✅ Report Generation: SUCCESS');
    console.log('   Status:', generateResponse.status);
    console.log('   Report ID:', generateResponse.data.report?.report_id || 'N/A');
    console.log('   Processing Time:', generateResponse.data.processing_time || 'N/A');
  } catch (error) {
    console.log('❌ Report Generation: FAILED');
    console.log('   Error:', error.message);
    if (error.code === 'ECONNABORTED') {
      console.log('   Issue: Request timeout - API may be slow or unavailable');
    } else if (error.response) {
      console.log('   Status:', error.response.status);
      console.log('   Response:', error.response.data);
    } else if (error.code === 'ECONNREFUSED') {
      console.log('   Issue: Connection refused - API server may not be running on port 8001');
    }
  }
  console.log('');

  // Summary
  console.log('='.repeat(60));
  console.log('Test Summary');
  console.log('='.repeat(60));
  console.log('If all tests passed, the local report API is working correctly.');
  console.log('If tests failed:');
  console.log('1. Make sure the Report Generation API is running on port 8001');
  console.log('2. Check if the API server logs show any errors');
  console.log('3. Verify firewall/network settings allow localhost:8001 connections');
  console.log('');
  console.log('To start the Report Generation API, run:');
  console.log('   cd "Report Generation"');
  console.log('   python run_report_system.py');
}

// Run the test
testReportAPI().catch(console.error);
