import requests
import sys
import json
import base64
from datetime import datetime, timedelta

class EnhancedFeaturesAPITester:
    def __init__(self, base_url="https://contractor-ai-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.created_job_id = None
        self.created_photo_id = None

    def log_test(self, name, success, details="", error=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {error}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "error": error
        })

    def make_request(self, method, endpoint, data=None, expected_status=200, files=None):
        """Make API request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if files:
                # For multipart/form-data requests
                response = requests.post(url, data=data, files=files, headers=headers)
            else:
                headers['Content-Type'] = 'application/json'
                if method == 'GET':
                    response = requests.get(url, headers=headers)
                elif method == 'POST':
                    response = requests.post(url, json=data, headers=headers)
                elif method == 'PUT':
                    response = requests.put(url, json=data, headers=headers)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
            
            return success, response_data, response.status_code

        except Exception as e:
            return False, {}, f"Request error: {str(e)}"

    def setup_test_data(self):
        """Setup test user and job for enhanced features testing"""
        # Login with test credentials
        login_data = {
            "email": "test@restoration.com",
            "password": "Test123!"
        }
        
        success, data, status = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_id = data['user']['id']
            print(f"✅ Logged in successfully as {data['user']['email']}")
        else:
            print(f"❌ Login failed with status {status}")
            return False

        # Create a test job for enhanced features testing
        job_data = {
            "title": "Enhanced Features Test Job",
            "customer_name": "Jane Doe",
            "customer_phone": "(555) 987-6543",
            "customer_email": "jane@email.com",
            "address": "456 Oak St, Austin, TX 78702",
            "scope": "Water damage restoration with enhanced tracking",
            "priority": "medium",
            "status": "pending"
        }
        
        success, data, status = self.make_request('POST', 'jobs', job_data, 200)
        
        if success and 'id' in data:
            self.created_job_id = data['id']
            print(f"✅ Test job created with ID: {self.created_job_id}")
            return True
        else:
            print(f"❌ Job creation failed with status {status}")
            return False

    def test_job_details_endpoint(self):
        """Test GET /api/jobs/{job_id}/details - Should return job with related data"""
        if not self.created_job_id:
            self.log_test("Job Details Endpoint", False, "", "No job ID available")
            return False
        
        success, data, status = self.make_request('GET', f'jobs/{self.created_job_id}/details', expected_status=200)
        
        if success and 'job' in data and 'costing' in data:
            # Check if all expected sections are present
            expected_sections = ['job', 'crew', 'invoices', 'work_orders', 'expenses', 'logs', 'photos', 'costing']
            missing_sections = [section for section in expected_sections if section not in data]
            
            if not missing_sections:
                self.log_test("Job Details Endpoint", True, f"All sections present: {', '.join(expected_sections)}")
            else:
                self.log_test("Job Details Endpoint", False, "", f"Missing sections: {', '.join(missing_sections)}")
                success = False
        else:
            self.log_test("Job Details Endpoint", False, "", f"Invalid response structure, status: {status}")
        
        return success

    def test_add_line_item(self):
        """Test POST /api/jobs/{job_id}/line-items - Add line item"""
        if not self.created_job_id:
            self.log_test("Add Line Item", False, "", "No job ID available")
            return False
        
        line_item_data = {
            "description": "Water extraction labor",
            "quantity": 8,
            "unit": "hour",
            "unit_price": 75,
            "item_type": "labor",
            "is_taxable": True
        }
        
        success, data, status = self.make_request('POST', f'jobs/{self.created_job_id}/line-items', line_item_data, 200)
        
        if success and 'message' in data and 'total_amount' in data:
            self.log_test("Add Line Item", True, f"Line item added, new total: ${data['total_amount']}")
        else:
            self.log_test("Add Line Item", False, "", f"Line item addition failed with status {status}")
        
        return success

    def test_upload_photo(self):
        """Test POST /api/jobs/{job_id}/photos - Upload photo (with base64 data)"""
        if not self.created_job_id:
            self.log_test("Upload Photo", False, "", "No job ID available")
            return False
        
        # Create a simple test image as base64
        # This is a minimal 1x1 pixel PNG image
        test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        
        # Use form data for multipart/form-data
        url = f"{self.api_url}/jobs/{self.created_job_id}/photos"
        headers = {'Authorization': f'Bearer {self.token}'}
        
        form_data = {
            'photo_data': test_image_base64,
            'caption': 'Test photo for enhanced features'
        }
        
        try:
            response = requests.post(url, data=form_data, headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'id' in data:
                    self.created_photo_id = data['id']
                    self.log_test("Upload Photo", True, f"Photo uploaded with ID: {self.created_photo_id}")
                else:
                    self.log_test("Upload Photo", False, "", "No photo ID in response")
                    success = False
            else:
                self.log_test("Upload Photo", False, "", f"Photo upload failed with status {response.status_code}")
        except Exception as e:
            self.log_test("Upload Photo", False, "", f"Photo upload error: {str(e)}")
            success = False
        
        return success

    def test_get_job_photos(self):
        """Test GET /api/jobs/{job_id}/photos - Get job photos"""
        if not self.created_job_id:
            self.log_test("Get Job Photos", False, "", "No job ID available")
            return False
        
        success, data, status = self.make_request('GET', f'jobs/{self.created_job_id}/photos', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_test("Get Job Photos", True, f"Retrieved {len(data)} photos")
        else:
            self.log_test("Get Job Photos", False, "", f"Failed to get photos, status: {status}")
        
        return success

    def test_add_job_expense(self):
        """Test POST /api/jobs/{job_id}/expenses - Add linked expense"""
        if not self.created_job_id:
            self.log_test("Add Job Expense", False, "", "No job ID available")
            return False
        
        expense_data = {
            "description": "Equipment rental - Dehumidifier",
            "amount": 150,
            "category": "equipment",
            "vendor": "ABC Rentals",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "is_taxable": False
        }
        
        success, data, status = self.make_request('POST', f'jobs/{self.created_job_id}/expenses', expense_data, 200)
        
        if success and 'id' in data and data.get('job_id') == self.created_job_id:
            self.log_test("Add Job Expense", True, f"Job expense added with ID: {data['id']}")
        else:
            self.log_test("Add Job Expense", False, "", f"Job expense addition failed with status {status}")
        
        return success

    def test_delete_photo(self):
        """Test DELETE /api/photos/{photo_id} - Delete photo"""
        if not self.created_photo_id:
            self.log_test("Delete Photo", False, "", "No photo ID available")
            return False
        
        success, data, status = self.make_request('DELETE', f'photos/{self.created_photo_id}', expected_status=200)
        
        if success and 'message' in data:
            self.log_test("Delete Photo", True, "Photo deleted successfully")
        else:
            self.log_test("Delete Photo", False, "", f"Photo deletion failed with status {status}")
        
        return success

    def test_delete_line_item(self):
        """Test DELETE /api/jobs/{job_id}/line-items/{item_index} - Delete line item"""
        if not self.created_job_id:
            self.log_test("Delete Line Item", False, "", "No job ID available")
            return False
        
        # Try to delete the first line item (index 0)
        success, data, status = self.make_request('DELETE', f'jobs/{self.created_job_id}/line-items/0', expected_status=200)
        
        if success and 'message' in data:
            self.log_test("Delete Line Item", True, "Line item deleted successfully")
        else:
            self.log_test("Delete Line Item", False, "", f"Line item deletion failed with status {status}")
        
        return success

    def run_enhanced_tests(self):
        """Run all enhanced features tests"""
        print("🚀 Starting Enhanced Features API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data - stopping tests")
            return False
        
        # Test enhanced endpoints
        self.test_job_details_endpoint()
        self.test_add_line_item()
        self.test_upload_photo()
        self.test_get_job_photos()
        self.test_add_job_expense()
        self.test_delete_photo()
        self.test_delete_line_item()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Enhanced Features Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All enhanced features tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} enhanced features tests failed")
            return False

def main():
    tester = EnhancedFeaturesAPITester()
    success = tester.run_enhanced_tests()
    
    # Save detailed results
    with open('/app/enhanced_features_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
            },
            'test_results': tester.test_results,
            'created_resources': {
                'job_id': tester.created_job_id,
                'photo_id': tester.created_photo_id
            }
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())