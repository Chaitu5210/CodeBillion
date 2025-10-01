import os
from dotenv import load_dotenv
from Production.production_orchestrator import ProductionOrchestrator
from Sandbox.sandbox_orchestrator import SandboxOrchestrator

load_dotenv()


sandbox = os.getenv("sandbox", "False").lower() == "true"


if sandbox:
    SandboxOrchestrator()
else:
    ProductionOrchestrator()
