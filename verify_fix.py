
import sys
import os
from pathlib import Path

# Add src to path
base_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(base_dir))

def verify():
    # Clear env var to simulate missing credentials
    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    print("Initial state: GOOGLE_APPLICATION_CREDENTIALS is", os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))

    try:
        from src.backend.services import pipeline_wrapper
        print("Imported pipeline_wrapper")
        
        # Trigger the credential loading
        pipeline_wrapper._ensure_pipeline_imports()
        
        val = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        print(f"Final state: GOOGLE_APPLICATION_CREDENTIALS is {val}")
        
        if val and "aegis-key.json" in val:
            print("SUCCESS: Credentials loaded automatically.")
        else:
            print("FAILURE: Credentials NOT loaded.")
            
    except Exception as e:
        print(f"FAILURE: Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify()
