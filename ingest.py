from dotenv import load_dotenv
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Forbidden
import time

load_dotenv()
# Change this to your bucket name
BUCKET_NAME = os.getenv("BUCKET_NAME")

client = storage.Client.from_service_account_json(os.getenv("CREDENTIALS_FILE"))
# client = storage.Client(project='zoomcamp-mod3-datawarehouse')

# https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-"
MONTHS = [f"{i:02d}" for i in range(1, 12)] # THIS SHOULD BE 1,13
# MONTHS = [f"{i:02d}" for i in range(1, 2)]


CHUNK_SIZE = 8 * 1024 * 1024

DOWNLOAD_DIR = "./tempdir"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bucket = client.bucket(BUCKET_NAME)


def download_file(month):
    url = f"{BASE_URL}{month}.parquet"
    file_path = os.path.join(DOWNLOAD_DIR, f"yellow_tripdata_2024-{month}.parquet")

    try:
        print(f"Downloading {url}...")
        urllib.request.urlretrieve(url, file_path)
        print(f"Downloaded: {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None


def create_bucket(bucket_name):
    try:
        # Get bucket details
        bucket = client.get_bucket(bucket_name)

        # Check if the bucket belongs to the current project
        project_bucket_ids = [bckt.id for bckt in client.list_buckets()]
        if bucket_name in project_bucket_ids:
            print(
                f"Bucket '{bucket_name}' exists and belongs to your project. Proceeding..."
            )
        else:
            print(
                f"A bucket with the name '{bucket_name}' already exists, but it does not belong to your project."
            )
            sys.exit(1)

    except NotFound:
        # If the bucket doesn't exist, create it
        bucket = client.create_bucket(bucket_name)
        print(f"Created bucket '{bucket_name}'")
    except Forbidden:
        # If the request is forbidden, it means the bucket exists but you don't have access to see details
        print(
            f"A bucket with the name '{bucket_name}' exists, but it is not accessible. Bucket name is taken. Please try a different bucket name."
        )
        sys.exit(1)


def verify_gcs_upload(blob_name):
    return storage.Blob(bucket=bucket, name=blob_name).exists(client)


def upload_to_gcs(file_path, max_retries=1):
    blob_name = os.path.basename(file_path)
    blob = bucket.blob(blob_name)
    blob.chunk_size = CHUNK_SIZE

    create_bucket(BUCKET_NAME)

    for attempt in range(max_retries):
        try:
            print(f"Uploading {file_path} to {BUCKET_NAME} (Attempt {attempt + 1})...")
            blob.upload_from_filename(file_path)
            print(f"Uploaded: gs://{BUCKET_NAME}/{blob_name}")

            if verify_gcs_upload(blob_name):
                print(f"Verification successful for {blob_name}")
                print(f"making a dataset table in BigQuery: {blob_name}")
                bigquery_load_gcs_to_bq(blob_name, "taxi_dataset")
                return
            else:
                print(f"Verification failed for {blob_name}, retrying...")
        except Exception as e:
            print(f"Failed to upload {file_path} to GCS: {e}")

        time.sleep(5)

    print(f"Giving up on {file_path} after {max_retries} attempts.")


def bigquery_load_gcs_to_bq(blob_name, dataset_id):

    bq_client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)
    
    # Ensure the dataset exists
    dataset_ref = bq_client.dataset(dataset_id)
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    bq_client.create_dataset(dataset, exists_ok=True)

    table_name = blob_name.replace(".parquet", "")
    uri = f"gs://{BUCKET_NAME}/{blob_name}"
    table_id = f"{bq_client.project}.{dataset_id}.{table_name}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = bq_client.load_table_from_uri(
        uri, table_id, job_config=job_config
    )
    
    load_job.result()  # Wait for the job to complete
    print(f"Loaded {uri} into {table_id}")


if __name__ == "__main__":
    create_bucket(BUCKET_NAME)

    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     file_paths = list(executor.map(download_file, MONTHS))

    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     executor.map(upload_to_gcs, filter(None, file_paths))  # Remove None values

    print("All files processed and verified.")
