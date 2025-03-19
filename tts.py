import asyncio
import re
import uuid
import tempfile
import os
import edge_tts


def text_to_speech(text, voice="en-GB-SoniaNeural", max_length=1000):
    """
    Convert text to speech using the Edge TTS service
    
    Args:
        text (str): The text to convert to speech
        voice (str): The voice to use (default: en-GB-SoniaNeural)
        max_length (int): Maximum length of text to process (default: 1000)
    
    Returns:
        str: Path to the generated audio file
    """
    # Create a temporary file with a unique name that will be automatically cleaned up
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, f"{uuid.uuid4()}.mp3")
    
    # Filter and clean the text
    cleaned_text = clean_text_for_speech(text)
    
    # Truncate if too long to avoid processing delays
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length] + "... (content truncated for speech)"
    
    # Skip if there's no content after cleaning
    if not cleaned_text.strip():
        return None
    
    async def amain():
        """Main async function to generate speech"""
        try:
            communicate = edge_tts.Communicate(cleaned_text, voice)
            with open(output_file, "wb") as file:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        file.write(chunk["data"])
        except Exception as e:
            print(f"TTS Error: {str(e)}")
            return None

    # Run the async function
    asyncio.run(amain())
    
    # Return the path to the generated file if it exists and has content
    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
        return output_file
    else:
        return None


def clean_text_for_speech(text):
    """
    Clean text by removing code snippets, markdown formatting, and other elements
    that don't work well in speech
    
    Args:
        text (str): The text to clean
    
    Returns:
        str: Cleaned text suitable for speech
    """
    # Remove code blocks (```code```)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    
    # Remove inline code (`code`)
    text = re.sub(r"`[^`]+`", " ", text)
    
    # Remove URLs and links
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # Replace [text](url) with just text
    text = re.sub(r"https?://\S+", " ", text)  # Remove http/https URLs
    
    # Remove markdown formatting characters
    text = re.sub(r"[*_~]", "", text)  # Remove *, _, and ~
    
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # Remove hashtags and formatting for headers
    text = re.sub(r"^#+\s", "", text, flags=re.MULTILINE)
    
    # Remove excessive whitespace, newlines and multiple spaces
    text = re.sub(r"\n+", " ", text)
    text = re.sub(r"\s+", " ", text)
    
    # Replace common abbreviations and symbols for better speech
    replacements = {
        "&": " and ",
        "@": " at ",
        "%": " percent ",
        "e.g.": "for example",
        "i.e.": "that is",
        "etc.": "etcetera",
        "vs.": "versus",
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text.strip()


def get_available_voices():
    """
    Get a list of available voices for Edge TTS
    
    Returns:
        list: List of available voice names
    """
    async def list_voices():
        voices = await edge_tts.list_voices()
        return [voice["ShortName"] for voice in voices]
    
    return asyncio.run(list_voices())
