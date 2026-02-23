
import asyncio
from anyio import open_file
from pathlib import Path
import os

async def test_anyio_open_no_await():
    temp_path = Path("test_file_no_await.txt")
    try:
        print("Attempting: async with open_file(...)")
        async with open_file(temp_path, "wb") as f:
            await f.write(b"test")
        print("Success!")
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        if temp_path.exists():
            os.remove(temp_path)

if __name__ == "__main__":
    asyncio.run(test_anyio_open_no_await())
