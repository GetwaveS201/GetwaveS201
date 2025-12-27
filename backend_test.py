import requests
import sys
import json
from datetime import datetime, timedelta

class RestorationOSAPITester:
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
        self.created_crew_id = None
        self.created_invoice_id = None
        self.created_work_order_id = None
        self.created_expense_id = None

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

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with error handling"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            return success, response.json() if response.content else {}, response.status_code

        except Exception as e:
            return False, {}, f"Request error: {str(e)}"

    def test_health_check(self):
        """Test basic API health"""
        success, data, status = self.make_request('GET', '', expected_status=200)
        self.log_test("API Health Check", success, 
                     f"API responded with status {status}" if success else "",
                     f"API not responding, status: {status}" if not success else "")
        return success

    def test_register_user(self):
        """Test user registration"""
        user_data = {
            "email": "test@restoration.com",
            "password": "Test123!",
            "name": "Test User"
        }
        
        success, data, status = self.make_request('POST', 'auth/register', user_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_id = data['user']['id']
            self.log_test("User Registration", True, f"User created with ID: {self.user_id}")
        else:
            # Try login if user already exists
            login_success, login_data, login_status = self.make_request('POST', 'auth/login', 
                                                                       {"email": user_data["email"], "password": user_data["password"]}, 200)
            if login_success and 'access_token' in login_data:
                self.token = login_data['access_token']
                self.user_id = login_data['user']['id']
                self.log_test("User Registration", True, "User already exists, logged in successfully")
                success = True
            else:
                self.log_test("User Registration", False, "", f"Registration failed with status {status}, login also failed")
        
        return success

    def test_login(self):
        """Test user login"""
        login_data = {
            "email": "test@restoration.com",
            "password": "Test123!"
        }
        
        success, data, status = self.make_request('POST', 'auth/login', login_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_id = data['user']['id']
            self.log_test("User Login", True, f"Login successful, token received")
        else:
            self.log_test("User Login", False, "", f"Login failed with status {status}")
        
        return success

    def test_get_user_profile(self):
        """Test getting current user profile"""
        success, data, status = self.make_request('GET', 'auth/me', expected_status=200)
        
        if success and 'email' in data:
            self.log_test("Get User Profile", True, f"Profile retrieved for {data['email']}")
        else:
            self.log_test("Get User Profile", False, "", f"Failed to get profile, status: {status}")
        
        return success

    def test_create_job(self):
        """Test creating a job"""
        job_data = {
            "title": "Water Damage - Kitchen",
            "customer_name": "John Smith",
            "customer_phone": "(555) 123-4567",
            "customer_email": "john@email.com",
            "address": "123 Main St, Austin, TX 78701",
            "scope": "Water extraction and drying for kitchen flood",
            "priority": "high",
            "status": "scheduled"
        }
        
        success, data, status = self.make_request('POST', 'jobs', job_data, 200)
        
        if success and 'id' in data:
            self.created_job_id = data['id']
            self.log_test("Create Job", True, f"Job created with ID: {self.created_job_id}")
        else:
            self.log_test("Create Job", False, "", f"Job creation failed with status {status}")
        
        return success

    def test_get_jobs(self):
        """Test getting all jobs"""
        success, data, status = self.make_request('GET', 'jobs', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_test("Get Jobs", True, f"Retrieved {len(data)} jobs")
        else:
            self.log_test("Get Jobs", False, "", f"Failed to get jobs, status: {status}")
        
        return success

    def test_update_job(self):
        """Test updating a job"""
        if not self.created_job_id:
            self.log_test("Update Job", False, "", "No job ID available for update")
            return False
        
        update_data = {
            "status": "in_progress"
        }
        
        success, data, status = self.make_request('PUT', f'jobs/{self.created_job_id}', update_data, 200)
        
        if success and data.get('status') == 'in_progress':
            self.log_test("Update Job", True, "Job status updated to in_progress")
        else:
            self.log_test("Update Job", False, "", f"Job update failed with status {status}")
        
        return success

    def test_create_crew(self):
        """Test creating a crew"""
        crew_data = {
            "name": "Alpha Team",
            "specialty": "water",
            "status": "available",
            "members": [
                {
                    "name": "Mike Johnson",
                    "role": "Lead Technician",
                    "phone": "(555) 111-2222",
                    "hourly_rate": 35
                }
            ]
        }
        
        success, data, status = self.make_request('POST', 'crews', crew_data, 200)
        
        if success and 'id' in data:
            self.created_crew_id = data['id']
            self.log_test("Create Crew", True, f"Crew created with ID: {self.created_crew_id}")
        else:
            self.log_test("Create Crew", False, "", f"Crew creation failed with status {status}")
        
        return success

    def test_get_crews(self):
        """Test getting all crews"""
        success, data, status = self.make_request('GET', 'crews', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_test("Get Crews", True, f"Retrieved {len(data)} crews")
        else:
            self.log_test("Get Crews", False, "", f"Failed to get crews, status: {status}")
        
        return success

    def test_create_invoice(self):
        """Test creating an invoice"""
        if not self.created_job_id:
            self.log_test("Create Invoice", False, "", "No job ID available for invoice creation")
            return False
        
        # Set due date to 30 days from now
        due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        invoice_data = {
            "job_id": self.created_job_id,
            "due_date": due_date,
            "tax_rate": 8.25
        }
        
        success, data, status = self.make_request('POST', 'invoices', invoice_data, 200)
        
        if success and 'id' in data:
            self.created_invoice_id = data['id']
            self.log_test("Create Invoice", True, f"Invoice created with ID: {self.created_invoice_id}")
        else:
            self.log_test("Create Invoice", False, "", f"Invoice creation failed with status {status}")
        
        return success

    def test_get_invoices(self):
        """Test getting all invoices"""
        success, data, status = self.make_request('GET', 'invoices', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_test("Get Invoices", True, f"Retrieved {len(data)} invoices")
        else:
            self.log_test("Get Invoices", False, "", f"Failed to get invoices, status: {status}")
        
        return success

    def test_create_work_order(self):
        """Test creating a work order"""
        if not self.created_job_id:
            self.log_test("Create Work Order", False, "", "No job ID available for work order creation")
            return False
        
        work_order_data = {
            "job_id": self.created_job_id,
            "tasks": [
                {"description": "Set up dehumidifiers", "is_completed": False},
                {"description": "Extract standing water", "is_completed": False},
                {"description": "Document damage", "is_completed": False}
            ],
            "materials_needed": ["Dehumidifier", "Air mover", "Moisture meter"]
        }
        
        success, data, status = self.make_request('POST', 'work-orders', work_order_data, 201)
        
        if success and 'id' in data:
            self.created_work_order_id = data['id']
            self.log_test("Create Work Order", True, f"Work order created with ID: {self.created_work_order_id}")
        else:
            self.log_test("Create Work Order", False, "", f"Work order creation failed with status {status}")
        
        return success

    def test_update_work_order_tasks(self):
        """Test updating work order tasks"""
        if not self.created_work_order_id:
            self.log_test("Update Work Order Tasks", False, "", "No work order ID available")
            return False
        
        # Mark first task as completed
        updated_tasks = [
            {"description": "Set up dehumidifiers", "is_completed": True},
            {"description": "Extract standing water", "is_completed": False},
            {"description": "Document damage", "is_completed": False}
        ]
        
        success, data, status = self.make_request('PUT', f'work-orders/{self.created_work_order_id}/tasks', updated_tasks, 200)
        
        if success:
            self.log_test("Update Work Order Tasks", True, "Work order tasks updated successfully")
        else:
            self.log_test("Update Work Order Tasks", False, "", f"Task update failed with status {status}")
        
        return success

    def test_create_expense(self):
        """Test creating an expense"""
        expense_data = {
            "description": "Equipment rental",
            "amount": 250.00,
            "category": "equipment",
            "vendor": "ABC Rentals",
            "date": datetime.now().strftime('%Y-%m-%d'),
            "is_taxable": False
        }
        
        success, data, status = self.make_request('POST', 'expenses', expense_data, 201)
        
        if success and 'id' in data:
            self.created_expense_id = data['id']
            self.log_test("Create Expense", True, f"Expense created with ID: {self.created_expense_id}")
        else:
            self.log_test("Create Expense", False, "", f"Expense creation failed with status {status}")
        
        return success

    def test_get_expenses(self):
        """Test getting all expenses"""
        success, data, status = self.make_request('GET', 'expenses', expected_status=200)
        
        if success and isinstance(data, list):
            self.log_test("Get Expenses", True, f"Retrieved {len(data)} expenses")
        else:
            self.log_test("Get Expenses", False, "", f"Failed to get expenses, status: {status}")
        
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        success, data, status = self.make_request('GET', 'reports/dashboard', expected_status=200)
        
        if success and 'total_jobs' in data:
            self.log_test("Dashboard Stats", True, f"Dashboard loaded with {data.get('total_jobs', 0)} total jobs")
        else:
            self.log_test("Dashboard Stats", False, "", f"Dashboard stats failed with status {status}")
        
        return success

    def test_profit_loss_report(self):
        """Test profit & loss report"""
        success, data, status = self.make_request('GET', 'reports/profit-loss', expected_status=200)
        
        if success and 'total_revenue' in data:
            self.log_test("Profit & Loss Report", True, f"Report generated with revenue: ${data.get('total_revenue', 0)}")
        else:
            self.log_test("Profit & Loss Report", False, "", f"P&L report failed with status {status}")
        
        return success

    def test_tax_summary_report(self):
        """Test tax summary report"""
        success, data, status = self.make_request('GET', 'reports/tax-summary', expected_status=200)
        
        if success and 'sales_tax_collected' in data:
            self.log_test("Tax Summary Report", True, f"Tax report generated")
        else:
            self.log_test("Tax Summary Report", False, "", f"Tax summary failed with status {status}")
        
        return success

    def test_cash_flow_forecast(self):
        """Test cash flow forecast report"""
        success, data, status = self.make_request('GET', 'reports/cash-flow-forecast', expected_status=200)
        
        if success and 'forecasts' in data:
            self.log_test("Cash Flow Forecast", True, f"Forecast generated with {len(data['forecasts'])} periods")
        else:
            self.log_test("Cash Flow Forecast", False, "", f"Cash flow forecast failed with status {status}")
        
        return success

    def test_ai_message_generation(self):
        """Test AI message generation"""
        if not self.created_job_id:
            self.log_test("AI Message Generation", False, "", "No job ID available for AI message")
            return False
        
        ai_request = {
            "message_type": "scheduling",
            "job_id": self.created_job_id,
            "customer_name": "John Smith"
        }
        
        success, data, status = self.make_request('POST', 'ai/generate-message', ai_request, 200)
        
        if success and 'message' in data:
            self.log_test("AI Message Generation", True, f"AI message generated: {data['message'][:50]}...")
        else:
            self.log_test("AI Message Generation", False, "", f"AI message generation failed with status {status}")
        
        return success

    def test_ai_compliance_check(self):
        """Test AI compliance analysis"""
        success, data, status = self.make_request('POST', 'ai/analyze-compliance', {}, 200)
        
        if success and 'analysis' in data:
            self.log_test("AI Compliance Check", True, "Compliance analysis completed")
        else:
            self.log_test("AI Compliance Check", False, "", f"Compliance check failed with status {status}")
        
        return success

    def test_ai_cash_flow_forecast(self):
        """Test AI cash flow forecast"""
        success, data, status = self.make_request('POST', 'ai/forecast-cashflow', {}, 200)
        
        if success and 'ai_analysis' in data:
            self.log_test("AI Cash Flow Forecast", True, "AI cash flow analysis completed")
        else:
            self.log_test("AI Cash Flow Forecast", False, "", f"AI cash flow forecast failed with status {status}")
        
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting RestorationOS API Tests...")
        print(f"Testing against: {self.base_url}")
        print("=" * 60)
        
        # Basic connectivity
        if not self.test_health_check():
            print("❌ API health check failed - stopping tests")
            return False
        
        # Authentication tests
        if not self.test_register_user():
            print("❌ User registration/login failed - stopping tests")
            return False
        
        self.test_get_user_profile()
        
        # Core functionality tests
        self.test_create_job()
        self.test_get_jobs()
        self.test_update_job()
        
        self.test_create_crew()
        self.test_get_crews()
        
        self.test_create_invoice()
        self.test_get_invoices()
        
        self.test_create_work_order()
        self.test_update_work_order_tasks()
        
        self.test_create_expense()
        self.test_get_expenses()
        
        # Reports tests
        self.test_dashboard_stats()
        self.test_profit_loss_report()
        self.test_tax_summary_report()
        self.test_cash_flow_forecast()
        
        # AI features tests
        self.test_ai_message_generation()
        self.test_ai_compliance_check()
        self.test_ai_cash_flow_forecast()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    tester = RestorationOSAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
            },
            'test_results': tester.test_results,
            'created_resources': {
                'job_id': tester.created_job_id,
                'crew_id': tester.created_crew_id,
                'invoice_id': tester.created_invoice_id,
                'work_order_id': tester.created_work_order_id,
                'expense_id': tester.created_expense_id
            }
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())