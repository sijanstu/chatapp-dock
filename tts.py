import asyncio
import re
import uuid

import edge_tts


def text_to_speech(text):
    voice = "en-GB-SoniaNeural"
    outputfile = f"{uuid.uuid4()}.mp3"
    print(f"Generating audio file: {outputfile}")
    # filter and skip whole snippets and remove them, also remove code blocks, links, and backticks
    text = remove_code_snippets(text)

    async def amain():
        """Main function"""
        communicate = edge_tts.Communicate(text, voice)
        with open(outputfile, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])

    asyncio.run(amain())
    return outputfile


def remove_code_snippets(text):
    # remove code snippets
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # remove links
    text = re.sub(r"\[.*?\]\(.*?\)", "", text)
    # remove backticks
    text = re.sub(r"`.*?`", "", text)
    # remove asterisks
    text = re.sub(r"\*.*?\*", "", text)
    text = re.sub(r"[*_]", "", text)
    return text
