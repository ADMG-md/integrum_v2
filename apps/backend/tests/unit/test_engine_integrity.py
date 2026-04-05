import sys
import os
import importlib
import unittest

class TestEngineIntegrity(unittest.TestCase):
    """
    Critical SaMD Infrastructure Check (IEC 62304).
    Ensures ALL engines in the src/engines directory can be imported 
    without NameErrors or missing typing references (Dict, Any, List).
    """

    def test_all_engines_importable(self):
        # Set sys.path to include current backend root
        backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if backend_root not in sys.path:
            sys.path.append(backend_root)

        engines_dir = os.path.join(backend_root, 'src', 'engines')
        self.assertTrue(os.path.exists(engines_dir), f"Engines directory not found at {engines_dir}")

        failures = []
        
        # Scan src/engines and src/engines/specialty
        for root, dirs, files in os.walk(engines_dir):
            for f in files:
                if f.endswith('.py') and not f.startswith('__'):
                    # Convert file path to module path (e.g. src.engines.acosta)
                    relative_path = os.path.relpath(os.path.join(root, f), backend_root)
                    module_path = relative_path.replace(os.sep, '.').replace('.py', '')
                    
                    try:
                        importlib.import_module(module_path)
                    except Exception as e:
                        failures.append(f"{module_path}: {type(e).__name__} - {str(e)}")

        if failures:
            error_msg = "FAILED to import the following modules (Potential NameErrors/Missing Imports):\n"
            error_msg += "\n".join(failures)
            self.fail(error_msg)

if __name__ == "__main__":
    unittest.main()
