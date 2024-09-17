import boto3
import os
import time
from botocore.exceptions import ClientError
import streamlit as st

def upload_file(file_name, bucket, object_name=None):
    """
    Upload a file to an S3 bucket
    
    Args:
        file_name (str): File to upload
        bucket (str): Bucket to upload to
        object_name (str, optional): S3 object name. If not specified, file_name is used
    
    Returns:
        bool: True if file was uploaded, else False
    """
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client('s3')

    try:
        s3_client.upload_file(file_name, bucket, object_name)
        return True
    except ClientError as e:
        print(f"Error uploading file: {e}")
        return False

def delete_transcribe_job(job_name):
    """
    Delete a Transcribe job
    
    Args:
        job_name (str): Name of the Transcribe job to delete
    """
    transcribe = boto3.client('transcribe')
    try:
        transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        print(f"Deleted Transcribe job: {job_name}")
    except ClientError as e:
        print(f"Error deleting Transcribe job {job_name}: {e}")

def transcribe_text_to_voice(st, job_name, job_uri, output_bucket, output_key, language_code):
    """
    Start a transcription job and wait for it to complete
    
    Args:
        st: Streamlit object
        job_name (str): Name of the transcription job
        job_uri (str): URI of the media file to transcribe
        output_bucket (str): S3 bucket for output
        output_key (str): S3 key for output file
        language_code (str): Language code for transcription
    
    Returns:
        str: URI of the transcript file if successful, None otherwise
    """
    transcribe = boto3.client('transcribe')
    
    try:
        response = transcribe.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': job_uri},
            MediaFormat='wav',  # Make sure this matches your audio file format
            LanguageCode=language_code,
            OutputBucketName=output_bucket,
            OutputKey=output_key
        )
        
        print(f"Transcription job '{job_name}' started successfully.")
        print(f"Initial job status: {response['TranscriptionJob']['TranscriptionJobStatus']}")

        while True:
            st.snow()
            status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            
            if job_status == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                print(f"Job {job_name} completed. Transcript URI: {transcript_uri}")
                delete_transcribe_job(job_name)
                return transcript_uri
            elif job_status == 'FAILED':
                print(f"Job {job_name} failed.")
                break
            
            print(f"Job status: {job_status}. Waiting...")
            time.sleep(5)

    except ClientError as e:
        print(f"Error with transcription job: {e}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    
    delete_transcribe_job(job_name)
    return None