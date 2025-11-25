import asyncio
from introlix.utils.title_gen import generate_title

print("Title generation module imported successfully.")
title = "Sample research prompt for testing."
print(asyncio.run(generate_title(title)))