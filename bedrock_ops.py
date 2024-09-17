import boto3
import json
from botocore.exceptions import ClientError
from urllib.parse import urlparse

def extract_s3_bucket_and_key(transcript_uri):
    """
    Extract S3 bucket and key from a given S3 URI.

    Args:
        transcript_uri (str): The S3 URI to parse.

    Returns:
        tuple: A tuple containing the bucket name and key.

    Raises:
        ValueError: If the URI is not a valid S3 URL or cannot be parsed.
    """
    parsed_url = urlparse(transcript_uri)
    
    if parsed_url.scheme != 'https' or '.amazonaws.com' not in parsed_url.netloc:
        raise ValueError("Invalid S3 URL format")
    
    path_parts = parsed_url.path.lstrip('/').split('/', 1)
    if len(path_parts) != 2:
        raise ValueError("Unable to extract bucket and key from the URL")
    
    return path_parts[0], path_parts[1]

def read_transcribe_output(bucket, key):
    """
    Read and parse the transcription output from an S3 object.

    Args:
        bucket (str): The S3 bucket name.
        key (str): The S3 object key.

    Returns:
        str: The transcription text, or None if an error occurs.
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        transcription = json.loads(content)
        return transcription['results']['transcripts'][0]['transcript']
    except ClientError as e:
        print(f"Error reading S3 object: {e}")
        return None

def invoke_bedrock_model(transcript):
    """
    Invoke the Bedrock model with the given transcript.

    Args:
        transcript (str): The transcript to process.

    Returns:
        str: The generated text from the model, or an empty string if an error occurs.
    """
    print(f"Inside invoke_bedrock_model for prompt: {transcript}")
    
    bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-west-2')
    model_id = 'anthropic.claude-3-haiku-20240307-v1:0'

    system_prompt = """
    You are a friendly, imaginative AI storyteller named Storytime Buddy. Your purpose is to entertain and educate children with fun stories, whimsical poems, and silly jokes. Always keep your content appropriate for children aged 5-12. Your responses should be:

    1. Engaging and age-appropriate
    2. Positive and encouraging
    3. Educational when possible, but always fun
    4. Free from any scary, violent, or inappropriate content

    For stories:
    - Keep them short and simple, usually under 5 minutes of reading time
    - Include colorful descriptions and memorable characters
    - End with a gentle moral or lesson when appropriate

    For poems:
    - Use simple rhymes and rhythms
    - Focus on topics kids enjoy like animals, nature, or everyday objects
    - Keep them short, usually 4-8 lines

    For jokes:
    - Use clean, silly humor appropriate for children
    - Avoid complex wordplay that might be too difficult for younger kids
    - Explain the joke if it might not be immediately clear

    Always be patient and willing to explain things in simpler terms if asked. If a child asks about a topic that might be too mature or complex, gently redirect to a more appropriate subject.

    Remember, your goal is to spark joy, creativity, and a love for storytelling in children!
    """

    request_payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": transcript}]
            }
        ]
    }

    try:
        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(request_payload)
        )

        response_body = json.loads(response['body'].read())
        generated_text = response_body['content'][0]['text']
        print("Generated text:")
        print(generated_text)
        return generated_text
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return ""
