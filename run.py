import subprocess
import sys
import os
from dotenv import load_dotenv
import time
import signal
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def run_fastapi():
    """Run the FastAPI server."""
    try:
        host = os.getenv("API_HOST", "0.0.0.0")
        port = os.getenv("API_PORT", "8000")
        
        cmd = [
            sys.executable,
            "-m", "uvicorn",
            "orchestrator.main:app",
            "--host", host,
            "--port", port,
            "--reload"
        ]
        
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {str(e)}")
        return None

def run_streamlit():
    """Run the Streamlit app."""
    try:
        host = os.getenv("STREAMLIT_HOST", "0.0.0.0")
        port = os.getenv("STREAMLIT_PORT", "8501")
        
        cmd = [
            sys.executable,
            "-m", "streamlit",
            "run", "streamlit_app/app.py",
            "--server.address", host,
            "--server.port", port
        ]
        
        return subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start Streamlit app: {str(e)}")
        return None

def main():
    """Run both servers and handle graceful shutdown."""
    try:
        # Start FastAPI server
        logger.info("Starting FastAPI server...")
        fastapi_process = run_fastapi()
        if not fastapi_process:
            logger.error("Failed to start FastAPI server")
            return
        
        # Wait a bit for FastAPI to start
        time.sleep(2)
        
        # Start Streamlit app
        logger.info("Starting Streamlit app...")
        streamlit_process = run_streamlit()
        if not streamlit_process:
            logger.error("Failed to start Streamlit app")
            fastapi_process.terminate()
            return
        
        def signal_handler(signum, frame):
            """Handle shutdown signals."""
            logger.info("Shutting down servers...")
            fastapi_process.terminate()
            streamlit_process.terminate()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Monitor processes
        while True:
            if fastapi_process.poll() is not None:
                logger.error("FastAPI server stopped unexpectedly")
                streamlit_process.terminate()
                break
                
            if streamlit_process.poll() is not None:
                logger.error("Streamlit app stopped unexpectedly")
                fastapi_process.terminate()
                break
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        if fastapi_process:
            fastapi_process.terminate()
        if streamlit_process:
            streamlit_process.terminate()
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        if fastapi_process:
            fastapi_process.terminate()
        if streamlit_process:
            streamlit_process.terminate()
        
    finally:
        logger.info("Servers stopped")

if __name__ == "__main__":
    main() 