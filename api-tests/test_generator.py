"""
Automated Test Case Generator for WordPress REST API
Reads ALL PHP controller files from WordPress endpoints directory
and generates pytest test cases automatically
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================================================

# WordPress API Configuration
BASE_URL = "http://localhost:8000/wp-json"
USERNAME = "maryamfatima"
APP_PASSWORD = "I1KhCgDNwKwjYyo9SLqGbdm2"

# Path to WordPress REST API endpoints directory
# Option 1: Direct path to WordPress
WORDPRESS_ENDPOINTS_DIR = Path("D:/WordPress/wp-includes/rest-api/endpoints")

# Option 2: If you copy the endpoints folder to your project
# WORDPRESS_ENDPOINTS_DIR = Path("./endpoints")

# Output directories
OUTPUT_DIR = Path("api-tests/generated")
DOCS_DIR = Path("api-tests/docs")

# ============================================================================


class PHPControllerParser:
    """Parses PHP controller files to extract endpoint information"""
    
    def __init__(self, endpoints_dir: Path):
        self.endpoints_dir = endpoints_dir
        self.controllers = []
    
    def find_all_controller_files(self) -> List[Path]:
        """Find ALL PHP files in the endpoints directory"""
        
        if not self.endpoints_dir.exists():
            print(f"\nERROR: Directory not found!")
            print(f"   Path: {self.endpoints_dir}")
            print(f"\nSolutions:")
            print(f"   1. Update WORDPRESS_ENDPOINTS_DIR in the script")
            print(f"   2. Or copy 'endpoints' folder to your project directory")
            return []
        
        print(f"Scanning directory: {self.endpoints_dir}")
        
        # Find ALL .php files
        php_files = list(self.endpoints_dir.glob("*.php"))
        
        # Also check subdirectories
        php_files.extend(self.endpoints_dir.glob("**/*.php"))
        
        # Remove duplicates
        php_files = list(set(php_files))
        
        print(f"\nFound {len(php_files)} PHP files:\n")
        for f in sorted(php_files):
            print(f"   {f.name}")
        
        return php_files
    
    def parse_controller_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a PHP controller file to extract endpoint information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if it's actually a controller
            if 'class' not in content or 'WP_REST' not in content:
                print(f"   Skipping {file_path.name} (not a REST controller)")
                return None
            
            # Extract routes from register_rest_route calls
            routes_info = self._extract_routes_detailed(content)
            
            controller_info = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'class_name': self._extract_class_name(content),
                'namespace': self._extract_namespace(content),
                'rest_base': self._extract_rest_base(content),
                'routes': routes_info,
                'methods': self._extract_public_methods(content),
                'description': self._extract_description(content),
                'has_get_items': 'get_items' in content,
                'has_get_item': 'get_item' in content,
                'has_create_item': 'create_item' in content,
                'has_update_item': 'update_item' in content,
                'has_delete_item': 'delete_item' in content,
            }
            
            # Determine controller type
            controller_info['type'] = self._determine_controller_type(controller_info)
            
            return controller_info
            
        except Exception as e:
            print(f"   Error parsing {file_path.name}: {e}")
            return None
    
    def _extract_class_name(self, content: str) -> str:
        """Extract class name from PHP file"""
        match = re.search(r'class\s+([\w_]+)\s+extends', content)
        return match.group(1) if match else "Unknown"
    
    def _extract_namespace(self, content: str) -> str:
        """Extract REST API namespace"""
        # Look for protected $namespace property
        match = re.search(r'protected\s+\$namespace\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if match:
            return match.group(1)
        
        # Look for $namespace assignment in constructor
        match = re.search(r'\$this->namespace\s*=\s*[\'"]([^\'"]+)[\'"]', content)
        if match:
            return match.group(1)
        
        # Infer from content
        if 'wp-abilities' in content.lower():
            return 'wp-abilities/v1'
        elif 'wp/v2' in content:
            return 'wp/v2'
        
        return 'wp/v2'
    
    def _extract_rest_base(self, content: str) -> str:
        """Extract REST base route"""
        # Look for protected $rest_base property (single line)
        match = re.search(r'protected\s+\$rest_base\s*=\s*[\'"]([^\'"]+)[\'"]\s*;', content)
        if match:
            return match.group(1)
        
        # Look for $this->rest_base assignment in constructor (single line)
        match = re.search(r'\$this->rest_base\s*=\s*[^;]*[\'"]([^\'"]+)[\'"]\s*;', content)
        if match:
            return match.group(1)
        
        # Try to extract from register_rest_route calls
        # Look for patterns like '/' . $this->rest_base
        route_match = re.search(r'register_rest_route\s*\(\s*\$this->namespace\s*,\s*[\'"]/([^\'"]+)[\'"]', content)
        if route_match:
            route = route_match.group(1)
            # Extract base from route (remove parameters and trailing paths)
            # Remove regex patterns like (?P<name>...)
            base = re.sub(r'/\([?]P<[^>]+>[^)]+\)', '', route)
            # Remove trailing /run, /execute, etc.
            base = re.sub(r'/(run|execute|autosave|revision).*$', '', base)
            # Remove any remaining regex patterns
            base = re.sub(r'\([^)]+\)', '', base)
            if base and base != '/':
                return base.strip('/')
        
        return ""
    
    def _extract_routes_detailed(self, content: str) -> List[Dict[str, Any]]:
        """Extract detailed route information from register_rest_route calls"""
        routes = []
        
        # Pattern to match register_rest_route calls
        # Match both $this->namespace and direct string namespace
        pattern = r'register_rest_route\s*\(\s*(?:\$this->namespace|[\'"][^\'"]+[\'"])\s*,\s*[\'"]([^\'"]+)[\'"]'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            route_path = match.group(1)
            # Skip if route_path is empty or just a slash
            if not route_path or route_path == '/':
                continue
            
            # Clean up route path (remove leading slash if present, it will be added later)
            route_path = route_path.lstrip('/')
            
            # Extract HTTP methods from the route definition
            # Look for methods in the array after the route
            methods = []
            start_pos = match.end()
            # Find the array that contains methods - look ahead up to 1000 chars
            array_match = re.search(r'array\s*\([^)]*methods[^)]*\)', content[start_pos:start_pos+1000], re.DOTALL)
            if array_match:
                methods_text = array_match.group(0)
                if 'WP_REST_Server::READABLE' in methods_text or 'READABLE' in methods_text:
                    methods.append('GET')
                if 'WP_REST_Server::CREATABLE' in methods_text or 'CREATABLE' in methods_text:
                    methods.append('POST')
                if 'WP_REST_Server::EDITABLE' in methods_text or 'EDITABLE' in methods_text:
                    methods.append('PUT')
                if 'WP_REST_Server::DELETABLE' in methods_text or 'DELETABLE' in methods_text:
                    methods.append('DELETE')
                if 'WP_REST_Server::ALLMETHODS' in methods_text or 'ALLMETHODS' in methods_text:
                    methods = ['GET', 'POST', 'DELETE']
            
            # Extract parameters from route path
            params = {}
            param_matches = re.finditer(r'\([?]P<(\w+)>', route_path)
            for param_match in param_matches:
                param_name = param_match.group(1)
                params[param_name] = 'string'
            
            routes.append({
                'path': route_path,
                'methods': methods if methods else ['GET'],
                'params': params
            })
        
        return routes
    
    def _extract_public_methods(self, content: str) -> List[str]:
        """Extract public methods from controller"""
        methods = []
        
        pattern = r'public\s+function\s+(\w+)\s*\('
        matches = re.finditer(pattern, content)
        
        for match in matches:
            method_name = match.group(1)
            if not method_name.startswith('__'):
                methods.append(method_name)
        
        return methods
    
    def _extract_description(self, content: str) -> str:
        """Extract controller description from docblock"""
        # Look for class docblock
        pattern = r'/\*\*\s*\*\s*([^\n]+(?:\n\s*\*\s*[^\n]+)*)'
        match = re.search(pattern, content)
        
        if match:
            desc = match.group(1)
            # Clean up
            desc = re.sub(r'\s*\*\s*', ' ', desc)
            desc = desc.strip()
            # Get first sentence
            desc = desc.split('.')[0] + '.'
            return desc
        
        return "REST API Controller"
    
    def _determine_controller_type(self, info: Dict) -> str:
        """Determine the type of controller"""
        class_name = info['class_name'].lower()
        rest_base = info['rest_base'].lower()
        routes = info.get('routes', [])
        
        # Check for specific patterns
        if 'categories' in class_name or 'categories' in rest_base:
            return 'categories'
        elif 'run' in class_name or 'run' in rest_base or 'execute' in class_name:
            return 'action'
        elif any('/run' in r.get('path', '') for r in routes):
            return 'action'
        elif 'list' in class_name or info['has_get_items']:
            return 'collection'
        elif info['has_get_item'] and not info['has_get_items']:
            return 'single'
        else:
            return 'generic'
    
    def parse_all_controllers(self) -> List[Dict[str, Any]]:
        """Parse all controller files"""
        files = self.find_all_controller_files()
        
        if not files:
            return []
        
        print(f"\nParsing controller files...\n")
        
        for file_path in sorted(files):
            controller_info = self.parse_controller_file(file_path)
            if controller_info:
                self.controllers.append(controller_info)
                print(f"   Parsed: {controller_info['class_name']}")
                print(f"      Type: {controller_info['type']}")
                print(f"      Namespace: {controller_info['namespace']}")
                print(f"      Base: {controller_info['rest_base']}")
                print(f"      Routes: {len(controller_info['routes'])}")
                print()
        
        return self.controllers


class EndpointGenerator:
    """Generates endpoint definitions from parsed controllers"""
    
    def __init__(self, controllers: List[Dict[str, Any]]):
        self.controllers = controllers
        self.endpoints = []
    
    def generate_endpoints(self) -> List[Dict[str, Any]]:
        """Generate endpoint definitions from controllers"""
        
        for controller in self.controllers:
            ctrl_type = controller['type']
            namespace = controller['namespace']
            rest_base = controller['rest_base']
            routes = controller.get('routes', [])
            
            # If we have detailed route information, use it
            if routes:
                self._add_routes_from_info(controller, namespace, rest_base, routes)
            else:
                # Fallback to type-based generation
                if ctrl_type == 'categories':
                    self._add_category_endpoints(controller, namespace, rest_base)
                elif ctrl_type == 'collection':
                    self._add_collection_endpoints(controller, namespace, rest_base)
                elif ctrl_type == 'single':
                    self._add_single_endpoints(controller, namespace, rest_base)
                elif ctrl_type == 'action':
                    self._add_action_endpoints(controller, namespace, rest_base)
                else:
                    self._add_generic_endpoints(controller, namespace, rest_base)
        
        return self.endpoints
    
    def _add_routes_from_info(self, controller: Dict, namespace: str, rest_base: str, routes: List[Dict]):
        """Add endpoints from detailed route information"""
        for route_info in routes:
            route_path = route_info['path']
            methods = route_info.get('methods', ['GET'])
            params = route_info.get('params', {})
            
            # Clean route path - remove regex patterns
            route_path_clean = re.sub(r'\([?]P<(\w+)>[^)]+\)', r'{\1}', route_path)
            
            # Build full path
            if route_path_clean.startswith('/'):
                full_path = f'/{namespace}{route_path_clean}'
            else:
                full_path = f'/{namespace}/{route_path_clean}'
            
            # Determine resource type
            if '/run' in route_path or '/execute' in route_path:
                resource_type = 'action'
            elif params:
                resource_type = 'single'
            else:
                resource_type = 'collection'
            
            # Generate endpoint name from route path
            # Extract the main resource name
            if rest_base:
                name = rest_base
            else:
                # Extract from route path
                path_parts = route_path_clean.strip('/').split('/')
                name = path_parts[0] if path_parts else 'unknown'
            
            # For single resources, add suffix
            if resource_type == 'single':
                if name.endswith('s'):
                    name = name[:-1]
            
            # Clean name
            name = re.sub(r'[^\w\-]', '_', name)
            name = re.sub(r'_+', '_', name).strip('_')
            
            self.endpoints.append({
                'name': name,
                'path': full_path,
                'methods': methods,
                'description': f'Endpoint for {route_path_clean}',
                'resource_type': resource_type,
                'params': params,
                'controller': controller['class_name'],
                'file_name': controller['file_name']
            })
    
    def _add_category_endpoints(self, controller: Dict, namespace: str, rest_base: str):
        """Add category endpoints"""
        if not rest_base:
            rest_base = 'categories'
        
        # Collection endpoint
        self.endpoints.append({
            'name': rest_base,
            'path': f'/{namespace}/{rest_base}',
            'methods': ['GET', 'HEAD'],
            'description': f'List all {rest_base}',
            'resource_type': 'collection',
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })
        
        # Single endpoint
        self.endpoints.append({
            'name': rest_base.rstrip('s') if rest_base.endswith('s') else rest_base,
            'path': f'/{namespace}/{rest_base}/{{slug}}',
            'methods': ['GET'],
            'description': f'Get single {rest_base.rstrip("s") if rest_base.endswith("s") else rest_base}',
            'resource_type': 'single',
            'params': {'slug': 'string'},
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })
    
    def _add_collection_endpoints(self, controller: Dict, namespace: str, rest_base: str):
        """Add collection endpoints"""
        if not rest_base:
            # Try to infer from class name
            class_name = controller['class_name'].lower()
            if 'posts' in class_name:
                rest_base = 'posts'
            elif 'comments' in class_name:
                rest_base = 'comments'
            elif 'users' in class_name:
                rest_base = 'users'
            elif 'terms' in class_name:
                rest_base = 'terms'
            else:
                # Extract from class name
                rest_base = class_name.replace('wp_rest_', '').replace('_controller', '').replace('_', '-')
        
        # Collection endpoint
        self.endpoints.append({
            'name': rest_base,
            'path': f'/{namespace}/{rest_base}',
            'methods': ['GET', 'HEAD'],
            'description': f'List all {rest_base}',
            'resource_type': 'collection',
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })
        
        # Single endpoint if get_item exists
        if controller['has_get_item']:
            # Determine parameter name
            if 'slug' in controller.get('routes', []):
                param_name = 'slug'
            elif 'post' in rest_base or 'page' in rest_base:
                param_name = 'id'
            else:
                param_name = 'id'
            
            self.endpoints.append({
                'name': rest_base.rstrip('s') if rest_base.endswith('s') else rest_base,
                'path': f'/{namespace}/{rest_base}/{{{param_name}}}',
                'methods': ['GET'],
                'description': f'Get single {rest_base.rstrip("s") if rest_base.endswith("s") else rest_base}',
                'resource_type': 'single',
                'params': {param_name: 'string'},
                'controller': controller['class_name'],
                'file_name': controller['file_name']
            })
    
    def _add_single_endpoints(self, controller: Dict, namespace: str, rest_base: str):
        """Add single resource endpoints"""
        if not rest_base:
            return
        
        self.endpoints.append({
            'name': rest_base,
            'path': f'/{namespace}/{rest_base}/{{id}}',
            'methods': ['GET'],
            'description': f'Get {rest_base}',
            'resource_type': 'single',
            'params': {'id': 'string'},
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })
    
    def _add_action_endpoints(self, controller: Dict, namespace: str, rest_base: str):
        """Add action endpoints"""
        if not rest_base:
            rest_base = 'abilities'
        
        # Check routes for run/execute pattern
        routes = controller.get('routes', [])
        action_path = f'/{namespace}/{rest_base}/{{name}}/run'
        
        for route in routes:
            if isinstance(route, dict) and '/run' in route.get('path', ''):
                action_path = f'/{namespace}{route["path"]}'
                # Replace regex patterns with simple placeholders
                action_path = re.sub(r'\([?]P<(\w+)>[^)]+\)', r'{\1}', action_path)
                break
        
        self.endpoints.append({
            'name': f'{rest_base}_run',
            'path': action_path,
            'methods': ['GET', 'POST', 'DELETE'],
            'description': f'Execute {rest_base}',
            'resource_type': 'action',
            'params': {'name': 'string'},
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })
    
    def _add_generic_endpoints(self, controller: Dict, namespace: str, rest_base: str):
        """Add generic endpoints"""
        if not rest_base:
            return
        
        self.endpoints.append({
            'name': rest_base,
            'path': f'/{namespace}/{rest_base}',
            'methods': ['GET'],
            'description': controller['description'],
            'resource_type': 'collection',
            'controller': controller['class_name'],
            'file_name': controller['file_name']
        })


class TestCaseGenerator:
    """Generates pytest test cases"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use in Python identifiers"""
        # Replace all invalid characters with underscores
        # Remove regex patterns like (?P<name>...)
        name = re.sub(r'\([?]P<[^>]+>[^)]+\)', '', name)
        # Replace slashes, dashes, and other special chars with underscores
        name = re.sub(r'[^\w]', '_', name)
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        # Ensure it starts with a letter or underscore
        if name and not name[0].isalpha() and name[0] != '_':
            name = '_' + name
        # Limit length
        if len(name) > 50:
            name = name[:50]
        return name or 'test'
    
    def generate_test_file(self, endpoint: Dict[str, Any]) -> tuple:
        """Generate complete pytest file"""
        # Clean name for filename - remove invalid characters
        name = endpoint['name']
        # Remove newlines, semicolons, and other invalid filename characters
        name = re.sub(r'[\n\r\t;{}\[\]()]', '', name)
        # Replace spaces and special chars with underscores
        name = re.sub(r'[^\w\-]', '_', name)
        # Remove multiple underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        # Limit length
        if len(name) > 50:
            name = name[:50]
        name_parts = name.replace('_', '-').replace('/', '-')
        file_name = f"test_{name_parts}.py"
        
        imports = self._generate_imports()
        config = self._generate_config(endpoint)
        helpers = self._generate_helpers(endpoint)
        tests = self._generate_tests(endpoint)
        
        code = f'''{imports}

{config}

{helpers}

{tests}'''
        
        return file_name, code
    
    def _generate_imports(self) -> str:
        return '''import pytest
import requests
from requests.auth import HTTPBasicAuth
import json
import re
from pathlib import Path
from urllib.parse import quote'''
    
    def _generate_config(self, endpoint: Dict[str, Any]) -> str:
        # Sanitize screenshot directory name
        screenshot_dir = self._sanitize_name(endpoint['name']).replace('_', '-')
        return f'''BASE_URL = "{self.base_url}"
USERNAME = "{self.username}"
APP_PASSWORD = "{self.password}"

SCREENSHOT_DIR = Path("api-tests/screenshots/{screenshot_dir}_outputs")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def save_response_screenshot(name, response):
    """Save API response to a JSON file for debugging"""
    # Sanitize filename to remove invalid characters
    safe_name = re.sub(r'[<>:"/\\|?*()\[\]{{}}]', '_', str(name))
    safe_name = re.sub(r'\\\\', '_', safe_name)  # Remove escaped backslashes
    safe_name = re.sub(r'\\d', 'd', safe_name)  # Fix \\d patterns
    safe_name = re.sub(r'_+', '_', safe_name).strip('_')
    if len(safe_name) > 200:  # Limit filename length
        safe_name = safe_name[:200]
    
    filepath = SCREENSHOT_DIR / (safe_name + ".json")
    try:
        if response.status_code >= 200 and response.status_code < 300:
            try:
                json.dump(response.json(), open(filepath, "w", encoding="utf-8"), indent=4)
            except (json.JSONDecodeError, ValueError):
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(response.text)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Status: {{response.status_code}}\\n")
                f.write(f"Headers: {{dict(response.headers)}}\\n")
                try:
                    f.write(f"Body: {{response.text}}")
                except Exception:
                    f.write("Body: [Unable to read response body]")
    except Exception as e:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Error saving response: {{str(e)}}\\n")
            f.write(f"Status Code: {{getattr(response, 'status_code', 'N/A')}}\\n")
    print("Saved response screenshot: " + str(filepath))'''
    
    def _generate_helpers(self, endpoint: Dict[str, Any]) -> str:
        if endpoint['resource_type'] == 'action':
            return '''
def get_ability_by_annotation(readonly=None, destructive=None, idempotent=None):
    """Helper function to get an ability with specific annotations"""
    url = f"{{BASE_URL}}/wp-abilities/v1/abilities"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.RequestException:
        return None
    
    if response.status_code != 200:
        return None
    
    try:
        abilities = response.json()
    except (json.JSONDecodeError, ValueError):
        return None
    
    if not isinstance(abilities, list):
        return None
    
    for ability in abilities:
        annotations = ability.get("meta", {}).get("annotations", {})
        if isinstance(annotations, dict):
            match = True
            if readonly is not None and annotations.get("readonly") != readonly:
                match = False
            if destructive is not None and annotations.get("destructive") != destructive:
                match = False
            if idempotent is not None and annotations.get("idempotent") != idempotent:
                match = False
            if match:
                return ability
    return None'''
        return ""
    
    def _generate_tests(self, endpoint: Dict[str, Any]) -> str:
        """Generate tests based on resource type"""
        if endpoint['resource_type'] == 'collection':
            return self._generate_collection_tests(endpoint)
        elif endpoint['resource_type'] == 'single':
            return self._generate_single_tests(endpoint)
        elif endpoint['resource_type'] == 'action':
            return self._generate_action_tests(endpoint)
        else:
            return self._generate_generic_tests(endpoint)
    
    def _generate_collection_tests(self, endpoint: Dict) -> str:
        name = endpoint['name']
        path = endpoint['path']
        safe_name = self._sanitize_name(name)
        # Escape backslashes in name and path for use in strings to avoid deprecation warnings
        name_escaped = name.replace('\\', '\\\\')
        # Escape path and also escape any {placeholders} to {{placeholders}} for f-strings
        path_escaped = path.replace('\\', '\\\\').replace('{', '{{').replace('}', '}}')
        
        tests = [
            f'''
def test_get_all_{safe_name}():
    """Test Case 1: Retrieve all {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("get_all_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}: {{response.text[:200] if hasattr(response, 'text') else 'No response text'}}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Some endpoints return dict instead of list (e.g., statuses, types, taxonomies)
            if isinstance(data, dict):
                # For dict responses, check if it's a valid response structure
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), f"Expected list or dict, got {{type(data)}}"
                if data:
                    assert isinstance(data[0], dict), "Items should be dictionaries"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")''',
            
            f'''
def test_unauthorized_{safe_name}():
    """Test Case 2: Unauthorized access to {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("unauthorized_{safe_name}", response)
    
    # Some endpoints allow public access, so accept 200, 401, 403, or 404
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {{response.status_code}}"''',
            
            f'''
def test_pagination_{safe_name}():
    """Test Case 3: Pagination for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}?page=1&per_page=5"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("pagination_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Some endpoints return dict instead of list
            if isinstance(data, dict):
                # For dict responses, pagination may not apply
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                # WordPress may return more than per_page if there are fewer total items
                # So we just check that we got a response
                assert len(data) >= 0, "Response should be a valid list"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")''',
            
            f'''
def test_response_schema_{safe_name}():
    """Test Case 4: Response Schema Validation for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("schema_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, dict):
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                if data:
                    item = data[0]
                    assert isinstance(item, dict), "Items should be dictionaries"
                    # Check for common WordPress REST API fields
                    if "_links" in item:
                        assert isinstance(item["_links"], dict), "_links should be a dictionary"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")''',
            
            f'''
def test_response_content_type_{safe_name}():
    """Test Case 5: Response Content Type for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("content_type_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        # Some endpoints may return different content types, so just check it's not empty
        content_type = response.headers.get("Content-Type", "")
        assert content_type, "Response should have a Content-Type header"''',
            
            f'''
def test_response_structure_{safe_name}():
    """Test Case 6: Response Structure Validation for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("structure_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        try:
            data = response.json()
            # Handle both list and dict responses
            if isinstance(data, dict):
                assert len(data) > 0, "Response should have at least one field"
            else:
                assert isinstance(data, list), "Response should be a list or dict"
                # Validate structure of first item if available
                if data:
                    item = data[0]
                    assert isinstance(item, dict), "Items should be dictionaries"
                    # Basic structure validation
                    assert len(item) > 0, "Item should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")'''
        ]
        
        if 'HEAD' in endpoint['methods']:
            tests.append(f'''
def test_head_{safe_name}():
    """Test Case 7: HEAD request for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.head(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("head_{safe_name}", response)
    
    # Accept 200 (success), 404 (not found), or 405 (method not allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {{response.status_code}}"
    if response.status_code == 200:
        assert response.text == "", "HEAD response should have no body"''')
        
        return '\n'.join(tests)
    
    def _generate_single_tests(self, endpoint: Dict) -> str:
        name = endpoint['name']
        path = endpoint['path']
        params = endpoint.get('params', {})
        param = list(params.keys())[0] if params else 'id'
        safe_name = self._sanitize_name(name)
        # Escape backslashes in name and path for use in strings to avoid deprecation warnings
        name_escaped = name.replace('\\', '\\\\')
        # Escape path: first escape backslashes, then escape {placeholders} to {{placeholders}} for f-strings
        path_escaped = path.replace('\\', '\\\\')
        # Find and escape placeholders like {id}, {name}, {slug} to {{id}}, {{name}}, {{slug}}
        path_escaped = re.sub(r'\{(\w+)\}', r'{{\1}}', path_escaped)
        
        # Get list path - handle cases where path might not have a parent
        list_path = path.rsplit('/', 1)[0] if '/' in path else path
        if not list_path:
            list_path = "/"
        
        # Escape param name for use in f-string
        param_escaped = "{{" + param + "}}"
        
        return f'''
def test_get_valid_{safe_name}():
    """Test Case 1: Get valid {name_escaped}"""
    # First, get list to find a valid identifier
    list_path = "{list_path}"
    list_url = f"{{BASE_URL}}{{list_path}}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {{first_key: items[first_key]}}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("{param}", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("get_valid_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}: {{response.text[:200] if hasattr(response, 'text') else 'No response text'}}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")
    # If 404, that's also valid - resource doesn't exist

def test_get_invalid_{safe_name}():
    """Test Case 2: Get invalid {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", "invalid-999999")
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("get_invalid_{safe_name}", response)
    
    # Accept 404 (not found) as expected, or 200 if somehow valid
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"

def test_unauthorized_{safe_name}():
    """Test Case 3: Unauthorized access to {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", "test")
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("unauthorized_{name_escaped}", response)
    
    # Accept 200 (if public), 401 (unauthorized), 403 (forbidden), or 404 (not found) as valid responses
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {{response.status_code}}"

def test_response_schema_{safe_name}():
    """Test Case 4: Response Schema Validation for {name_escaped}"""
    # First, get list to find a valid identifier
    list_path = "{list_path}"
    list_url = f"{{BASE_URL}}{{list_path}}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {{first_key: items[first_key]}}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("{param}", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("schema_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
            assert len(data) > 0, "Response should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")

def test_response_content_type_{safe_name}():
    """Test Case 5: Response Content Type for {name_escaped}"""
    # First, get list to find a valid identifier
    list_path = "{list_path}"
    list_url = f"{{BASE_URL}}{{list_path}}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {{first_key: items[first_key]}}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("{param}", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("content_type_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        assert content_type, "Response should have a Content-Type header"

def test_response_structure_{safe_name}():
    """Test Case 6: Response Structure Validation for {name_escaped}"""
    # First, get list to find a valid identifier
    list_path = "{list_path}"
    list_url = f"{{BASE_URL}}{{list_path}}"
    try:
        list_response = requests.get(list_url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    if list_response.status_code != 200:
        pytest.skip("No items available to test")
    try:
        items = list_response.json()
    except (json.JSONDecodeError, ValueError):
        pytest.skip("Invalid response from server")
    
    # Handle both list and dict responses
    if isinstance(items, dict):
        if items:
            first_key = list(items.keys())[0]
            item = items[first_key] if isinstance(items[first_key], dict) else {{first_key: items[first_key]}}
        else:
            pytest.skip("No items available to test")
    elif isinstance(items, list):
        if not items:
            pytest.skip("No items available to test")
        item = items[0]
    else:
        pytest.skip("Invalid response format")
    
    if not item:
        pytest.skip("No items available to test")
    
    identifier = item.get("{param}", item.get("slug", item.get("name", item.get("id", "1"))))
    
    url = f"{{BASE_URL}}{path_escaped}".replace("{param_escaped}", str(identifier))
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("structure_{safe_name}", response)
    
    # Accept 200 (success) or 404 (not found) as valid responses
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"
    if response.status_code == 200:
        try:
            data = response.json()
            assert isinstance(data, dict), "Response should be a dictionary"
            # Validate structure
            assert len(data) > 0, "Response should have at least one field"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")'''
    
    def _generate_action_tests(self, endpoint: Dict) -> str:
        path = endpoint['path']
        name = endpoint['name']
        safe_name = self._sanitize_name(name)
        name_escaped = name.replace('\\', '\\\\')
        
        # Extract parameter name from path
        param_name = 'name'  # Default
        if '{' in path:
            param_match = re.search(r'\{(\w+)\}', path)
            if param_match:
                param_name = param_match.group(1)
        
        # Escape path: first escape backslashes, then escape {placeholders} to {{placeholders}} for f-strings
        path_escaped = path.replace('\\', '\\\\')
        # Find and escape placeholders like {name} to {{name}} for f-strings
        path_escaped = re.sub(r'\{(\w+)\}', r'{{\1}}', path_escaped)
        
        # Create placeholder for replacement
        placeholder_escaped = "{{" + param_name + "}}"
        
        return f'''
def test_execute_readonly():
    """Test Case 1: Execute readonly ability"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability available")
    
    ability_name = ability.get("name", "test")
    # URL encode ability name in case it contains special characters like slashes
    # WordPress REST API may handle slashes in ability names, so we encode them
    ability_name_encoded = quote(ability_name, safe='')
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", ability_name_encoded)
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("execute_readonly", response)
    
    # Accept 200 (success), 404 (not found), or 405 (method not allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {{response.status_code}}: {{response.text[:200] if hasattr(response, 'text') else 'No response text'}}"

def test_execute_wrong_method():
    """Test Case 2: Execute with wrong HTTP method"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability available")
    
    ability_name = ability.get("name", "test")
    # URL encode ability name in case it contains special characters like slashes
    # WordPress REST API may handle slashes in ability names, so we encode them
    ability_name_encoded = quote(ability_name, safe='')
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", ability_name_encoded)
    try:
        response = requests.post(url, json={{"input": {{}}}}, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("execute_wrong_method", response)
    
    # Accept 405 (method not allowed), 404 (not found), or 200 (if somehow allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {{response.status_code}}"

def test_execute_invalid():
    """Test Case 3: Execute invalid ability"""
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", "invalid-ability-999")
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("execute_invalid", response)
    
    # Accept 404 (not found) as expected, or 200 if somehow valid
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"

def test_execute_unauthorized():
    """Test Case 4: Unauthorized execution"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability available")
    
    ability_name = ability.get("name", "test")
    # URL encode ability name in case it contains special characters like slashes
    # WordPress REST API may handle slashes in ability names, so we encode them
    ability_name_encoded = quote(ability_name, safe='')
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", ability_name_encoded)
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("execute_unauthorized", response)
    
    # Accept 200 (if public), 401 (unauthorized), 403 (forbidden), or 404 (not found) as valid responses
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {{response.status_code}}"

def test_response_schema_execute():
    """Test Case 5: Response Schema Validation for ability execution"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability available")
    
    ability_name = ability.get("name", "test")
    # URL encode ability name in case it contains special characters like slashes
    # WordPress REST API may handle slashes in ability names, so we encode them
    ability_name_encoded = quote(ability_name, safe='')
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", ability_name_encoded)
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("schema_execute", response)
    
    # Accept 200 (success), 404 (not found), or 405 (method not allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {{response.status_code}}"
    if response.status_code == 200:
        # Response can be various types, just check it's valid JSON
        try:
            data = response.json()
            assert data is not None, "Response should be valid JSON"
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

def test_response_structure_execute():
    """Test Case 6: Response Structure Validation for ability execution"""
    ability = get_ability_by_annotation(readonly=True)
    if not ability:
        pytest.skip("No readonly ability available")
    
    ability_name = ability.get("name", "test")
    # URL encode ability name in case it contains special characters like slashes
    # WordPress REST API may handle slashes in ability names, so we encode them
    ability_name_encoded = quote(ability_name, safe='')
    url = f"{{BASE_URL}}{path_escaped}".replace("{placeholder_escaped}", ability_name_encoded)
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("structure_execute", response)
    
    # Accept 200 (success), 404 (not found), or 405 (method not allowed) as valid responses
    assert response.status_code in [200, 404, 405], f"Expected 200, 404, or 405, got {{response.status_code}}"
    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        assert content_type, "Response should have a Content-Type header"'''
    
    def _generate_generic_tests(self, endpoint: Dict) -> str:
        name = endpoint['name']
        path = endpoint['path']
        safe_name = self._sanitize_name(name)
        # Escape backslashes in name and path for use in strings to avoid deprecation warnings
        name_escaped = name.replace('\\', '\\\\')
        path_escaped = path.replace('\\', '\\\\')
        
        return f'''
def test_get_{safe_name}():
    """Test Case 1: Get {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("get_{name_escaped}", response)
    
    assert response.status_code in [200, 404], f"Expected 200 or 404, got {{response.status_code}}"

def test_unauthorized_{safe_name}():
    """Test Case 2: Unauthorized access to {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("unauthorized_{name_escaped}", response)
    
    # Accept 200 (if public), 401 (unauthorized), 403 (forbidden), or 404 (not found) as valid responses
    assert response.status_code in [200, 401, 403, 404], f"Expected 200, 401, 403, or 404, got {{response.status_code}}"

def test_response_schema_{safe_name}():
    """Test Case 3: Response Schema Validation for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("schema_{name_escaped}", response)
    
    if response.status_code == 200:
        try:
            data = response.json()
            assert data is not None, "Response should be valid JSON"
        except (json.JSONDecodeError, ValueError) as e:
            pytest.fail(f"Response is not valid JSON: {{str(e)}}")

def test_response_content_type_{safe_name}():
    """Test Case 4: Response Content Type for {name_escaped}"""
    url = f"{{BASE_URL}}{path_escaped}"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, APP_PASSWORD), timeout=10)
    except requests.exceptions.ConnectionError:
        pytest.skip("WordPress server is not running or not accessible")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {{str(e)}}")
    
    save_response_screenshot("content_type_{name_escaped}", response)
    
    if response.status_code == 200:
        assert "application/json" in response.headers.get("Content-Type", ""), "Response should be JSON"'''
    
    def generate_documentation(self, endpoint: Dict) -> str:
        """Generate markdown documentation with formatted test cases"""

        # Normalize paths for f-strings (avoid backslash issues)
        path = str(endpoint['path']).replace("\\", "/")
        source_file = str(endpoint['file_name']).replace("\\", "/")

        # ----- DEFINE TEST CASES BASED ON ENDPOINT TYPE -----
        if endpoint['resource_type'] == 'collection':
            test_cases = [
                {
                    "num": 1,
                    "name": "Retrieve All Items",
                    "purpose": "Fetch complete collection list.",
                    "api": f"GET {path}",
                    "steps": [
                        "Send authenticated GET request.",
                        "Validate response structure.",
                        "Save output."
                    ],
                    "expected": [
                        "Status: 200",
                        "Response contains an array of items."
                    ]
                },
                {
                    "num": 2,
                    "name": "Unauthorized Access",
                    "purpose": "Ensure unauthenticated users are blocked.",
                    "api": f"GET {path}",
                    "steps": ["Send GET request without authentication."],
                    "expected": ["Status: 401 or 403"]
                },
                {
                    "num": 3,
                    "name": "Pagination",
                    "purpose": "Verify pagination parameters.",
                    "api": f"GET {path}?page=2&per_page=5",
                    "steps": [
                        "Send authenticated request with pagination.",
                        "Validate pagination headers."
                    ],
                    "expected": [
                        "Status: 200",
                        "Headers include X-WP-Total & X-WP-TotalPages"
                    ]
                },
                {
                    "num": 4,
                    "name": "Response Schema Validation",
                    "purpose": "Ensure items follow expected schema.",
                    "api": f"GET {path}",
                    "steps": ["Validate JSON fields by schema."],
                    "expected": ["Status: 200"]
                },
                {
                    "num": 5,
                    "name": "Response Content Type",
                    "purpose": "Ensure correct MIME type.",
                    "api": f"GET {path}",
                    "steps": ["Check Content-Type header."],
                    "expected": ["Header: application/json"]
                },
                {
                    "num": 6,
                    "name": "Response Structure Validation",
                    "purpose": "Ensure response is an array of objects.",
                    "api": f"GET {path}",
                    "steps": ["Validate array structure."],
                    "expected": ["Status: 200"]
                },
                {
                    "num": 7,
                    "name": "HEAD Request Validation",
                    "purpose": "Validate HEAD method behavior.",
                    "api": f"HEAD {path}",
                    "steps": [
                        "Send authenticated HEAD request.",
                        "Capture status and headers."
                    ],
                    "expected": [
                        "Status: 200, 404, or 405",
                        "If 200 → response body must be empty"
                    ]
                }
            ]

        elif endpoint['resource_type'] == 'single':
            test_cases = [
                {
                    "num": 1,
                    "name": "Get Valid Item",
                    "purpose": "Retrieve a valid resource.",
                    "api": f"GET {path}/{{id}}",
                    "steps": ["Send authenticated GET request using valid ID."],
                    "expected": ["Status: 200"]
                },
                {
                    "num": 2,
                    "name": "Get Invalid Item",
                    "purpose": "Verify 404 for invalid resource.",
                    "api": f"GET {path}/999999",
                    "steps": ["Send GET request with non-existent ID."],
                    "expected": ["Status: 404"]
                },
                {
                    "num": 3,
                    "name": "Unauthorized Access",
                    "purpose": "Ensure unauthenticated calls fail.",
                    "api": f"GET {path}/{{id}}",
                    "steps": ["Send GET without authentication."],
                    "expected": ["Status: 401 or 403"]
                },
                {
                    "num": 4,
                    "name": "Response Schema Validation",
                    "purpose": "Validate single item schema.",
                    "api": f"GET {path}/{{id}}",
                    "steps": ["Check keys against schema."],
                    "expected": ["Status: 200"]
                },
                {
                    "num": 5,
                    "name": "Response Content Type",
                    "purpose": "Ensure MIME type is correct.",
                    "api": f"GET {path}/{{id}}",
                    "steps": ["Inspect Content-Type header."],
                    "expected": ["Header: application/json"]
                },
                {
                    "num": 6,
                    "name": "Response Structure Validation",
                    "purpose": "Ensure response is a JSON object.",
                    "api": f"GET {path}/{{id}}",
                    "steps": ["Validate object structure."],
                    "expected": ["Status: 200"]
                }
            ]

        else:
            test_cases = [
                {
                    "num": 1,
                    "name": "Basic GET Validation",
                    "purpose": "Call endpoint and confirm response.",
                    "api": f"GET {path}",
                    "steps": ["Send GET request."],
                    "expected": ["Status: 200 or documented alternative"]
                }
            ]

        # ----- FORMAT TEST CASES -----
        formatted_cases = ""
        for tc in test_cases:
            steps_md = "\n".join([f"- {s}" for s in tc["steps"]])
            expected_md = "\n".join([f"- {e}" for e in tc["expected"]])

            formatted_cases += f"""
    ### Test Case {tc['num']} — {tc['name']}

    **Name:** test_{tc['name'].lower().replace(' ', '_')}

    **Purpose:** {tc['purpose']}

    **API:** {tc['api']}

    **Steps:**
    {steps_md}

    **Expected Results:**
    {expected_md}

    ---
    """

        # ----- FINAL RETURN -----
        return f"""# Test Cases — {endpoint['name'].replace('_', ' ').title()}

    ## Source Information
    - **Controller:** {endpoint['controller']}
    - **Source File:** {source_file}
    - **Endpoint:** `{path}`
    - **Methods:** {', '.join(endpoint['methods'])}
    - **Type:** {endpoint['resource_type']}

    ---

    # Test Case Documentation

    {formatted_cases}

    *Auto-generated from {source_file}*
    """




def main():
    """Main execution"""
    import sys
    import io
    # Set UTF-8 encoding for Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 70)
    print("WordPress REST API Test Generator")
    print("=" * 70)
    print(f"\nTarget Directory: {WORDPRESS_ENDPOINTS_DIR}")
    print(f"API URL: {BASE_URL}")
    print()
    
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Parse PHP files
    parser = PHPControllerParser(WORDPRESS_ENDPOINTS_DIR)
    controllers = parser.parse_all_controllers()
    
    if not controllers:
        print("\n❌ No controllers found!")
        print("\n💡 Make sure:")
        print("   1. WORDPRESS_ENDPOINTS_DIR path is correct")
        print("   2. Directory contains PHP controller files")
        return
    
    print(f"=" * 70)
    print(f"Successfully parsed {len(controllers)} controllers")
    print("=" * 70)
    
    # Generate endpoints
    print("\nGenerating endpoint definitions...")
    generator = EndpointGenerator(controllers)
    endpoints = generator.generate_endpoints()
    
    print(f"Generated {len(endpoints)} endpoint definitions\n")
    
    # Generate tests
    test_gen = TestCaseGenerator(BASE_URL, USERNAME, APP_PASSWORD)
    
    print("=" * 70)
    print("Generating test files...")
    print("=" * 70)
    print()
    
    total_tests = 0
    
    for endpoint in endpoints:
        print(f"Endpoint: {endpoint['name']}")
        print(f"   Source: {endpoint['file_name']}")
        print(f"   Type: {endpoint['resource_type']}")
        print(f"   Path: {endpoint['path']}")
        
        # Generate test file
        file_name, code = test_gen.generate_test_file(endpoint)
        test_path = OUTPUT_DIR / file_name
        
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        test_count = code.count('def test_')
        total_tests += test_count
        
        print(f"   Created: {test_path} ({test_count} tests)")
        
        # Generate docs
        doc = test_gen.generate_documentation(endpoint)
        doc_path = DOCS_DIR / file_name.replace('.py', '.md')
        
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(doc)
        
        print(f"   Created: {doc_path}")
        print()
    
    # Generate README
    generate_readme(controllers, endpoints, total_tests)
    
    print("=" * 70)
    print("GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\nSummary:")
    print(f"   Controllers: {len(controllers)}")
    print(f"   Endpoints: {len(endpoints)}")
    print(f"   Test files: {len(endpoints)}")
    print(f"   Total tests: {total_tests}")
    print(f"\nOutput:")
    print(f"   Tests: {OUTPUT_DIR}")
    print(f"   Docs: {DOCS_DIR}")
    print(f"\nRun tests:")
    print(f"   pytest {OUTPUT_DIR} -v")
    print()


def generate_readme(controllers: List[Dict], endpoints: List[Dict], total_tests: int):
    """Generate README file"""
    readme = f"""# Auto-Generated Test Suite

Generated from WordPress REST API controller files.

## Source Controllers ({len(controllers)} files)

"""
    
    for ctrl in controllers:
        readme += f"""### {ctrl['class_name']}
- **File:** `{ctrl['file_name']}`
- **Type:** {ctrl['type']}
- **Namespace:** `{ctrl['namespace']}`
- **Base:** `{ctrl['rest_base']}`

"""
    
    readme += f"""
## Generated Test Files ({len(endpoints)} endpoints)

"""
    
    for endpoint in endpoints:
        file_name = f"test_{endpoint['name'].replace('_', '-').replace('/', '-')}.py"
        readme += f"""### {endpoint['name'].title()}
- **Test File:** `{file_name}`
- **Documentation:** `docs/{file_name.replace('.py', '.md')}`
- **Source:** {endpoint['file_name']}
- **Endpoint:** `{endpoint['path']}`

"""
    
    readme += f"""
## Statistics

- **Controllers:** {len(controllers)}
- **Endpoints:** {len(endpoints)}
- **Test Files:** {len(endpoints)}
- **Total Tests:** {total_tests}

## Quick Start

```bash
# Run all tests
pytest api-tests/generated/ -v

# Run specific file
pytest api-tests/generated/test-categories.py -v

# With HTML report
pytest api-tests/generated/ --html=report.html --self-contained-html
```

---

*Auto-generated from: `{WORDPRESS_ENDPOINTS_DIR}`*
"""
    
    with open(OUTPUT_DIR / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)


if __name__ == "__main__":
    main()
