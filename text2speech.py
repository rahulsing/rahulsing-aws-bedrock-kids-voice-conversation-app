import boto3
from botocore.exceptions import BotoCoreError, ClientError

def text_to_speech(text, output_file, voice_id="Ivy", engine="neural"):
    """
    Convert text to speech using Amazon Polly and save it as an MP3 file.

    Args:
        text (str): The text to convert to speech.
        output_file (str): The path to save the output MP3 file.
        voice_id (str, optional): The voice ID to use. Defaults to "Ivy".
        engine (str, optional): The engine type. Defaults to "neural".

    Returns:
        bool: True if successful, False otherwise.
    """
    polly_client = boto3.client('polly')

    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine=engine
        )
    except (BotoCoreError, ClientError) as error:
        print(f"Error: {error}")
        return False

    if "AudioStream" in response:
        try:
            with open(output_file, 'wb') as file:
                file.write(response['AudioStream'].read())
            print(f"Speech saved to {output_file}")
            return True
        except IOError as error:
            print(f"Error saving audio file: {error}")
            return False
    else:
        print("Could not stream audio")
        return False
