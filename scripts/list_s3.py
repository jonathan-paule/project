
import boto3
from openpyxl import Workbook
from concurrent.futures import ThreadPoolExecutor, as_completed

regions = ['us-east-1', 'us-west-2', 'us-east-2']
allowed_regions = set(regions)

wb = Workbook()
wb.remove(wb.active)

def format_tags(tags):
    if not tags:
        return ""
    return ", ".join([f"{tag['Key']}={tag['Value']}" for tag in tags])

def get_bucket_details(bucket_name):
    s3 = boto3.client('s3')
    try:
        location = s3.get_bucket_location(Bucket=bucket_name).get('LocationConstraint') or 'us-east-1'
        if location not in allowed_regions:
            return None

        # Get tags
        try:
            tagging = s3.get_bucket_tagging(Bucket=bucket_name)
            tags = format_tags(tagging.get('TagSet', []))
        except s3.exceptions.ClientError:
            tags = ""

        # Get storage class (sample)
        try:
            obj_list = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            contents = obj_list.get('Contents', [])
            storage_class = contents[0].get('StorageClass', 'STANDARD') if contents else 'N/A'
        except Exception:
            storage_class = "Error"

        return [bucket_name, location, storage_class, tags]
    except Exception:
        return [bucket_name, "Error", "Error", "Error"]

# Main function to fetch and write S3 data
def fetch_s3_buckets_multithreaded():
    s3 = boto3.client('s3')
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response['Buckets']]

    bucket_results = {region: [] for region in regions}

    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_bucket = {executor.submit(get_bucket_details, name): name for name in bucket_names}

        for future in as_completed(future_to_bucket):
            result = future.result()
            if result and result[1] in allowed_regions:
                bucket_results[result[1]].append(result)

    return bucket_results

# Fetch data and write to Excel
bucket_data_by_region = fetch_s3_buckets_multithreaded()

for region in regions:
    sheet = wb.create_sheet(title=f"S3-{region}")
    sheet.append(['Bucket Name', 'Region', 'Storage Class (Sample)', 'Tags'])
    for row in bucket_data_by_region.get(region, []):
        sheet.append(row)

filename = "s3_buckets_list.xlsx"
wb.save(filename)
print(f"Excel file '{filename}' created successfully.")
