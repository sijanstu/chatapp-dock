import asyncio
import uuid

import edge_tts


def text_to_speech(text):
    voice = "en-GB-SoniaNeural"
    outputfile = f"{uuid.uuid4()}.mp3"
    print(f"Generating audio file: {outputfile}")
    async def amain():
        """Main function"""
        communicate = edge_tts.Communicate(text, voice)
        with open(outputfile, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
    asyncio.run(amain())
    return outputfile
