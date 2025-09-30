import os
from dotenv import load_dotenv
from production.prod_orchestrator import prod_orchestrator
from sandbox.sandbox_orchestrator import sandbox_orchestrator

load_dotenv()


sandbox = os.getenv("sandbox", "False").lower() == "true"


if sandbox:
    print("--- Coming Here Sandbox")
    sandbox_orchestrator()
else:
    print("--- Coming Here Production")
    prod_orchestrator()
