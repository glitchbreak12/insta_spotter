import asyncio
import httpx
import os

async def self_ping():
    """Fa un ping a se stesso ogni 5 minuti per stare sveglio su Replit."""
    base_url = os.getenv("REPLIT_URL", "http://localhost:8000")
    
    while True:
        try:
            async with httpx.AsyncClient() as client:
                await client.get(f"{base_url}/health", timeout=5)
                print("✓ Self-ping done")
        except Exception as e:
            print(f"✗ Self-ping failed: {e}")
        
        # Attendi 5 minuti
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(self_ping())
