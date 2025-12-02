import boto3
from botocore.exceptions import ClientError
from openpyxl import Workbook

def list_s3_buckets_with_lifecycle_to_excel(output_file="s3_buckets.xlsx"):
    s3_client = boto3.client("s3")

    # Create Excel workbook and sheet
    wb = Workbook()
    ws = wb.active
    ws.title = "S3 Buckets"
    ws.append(["Bucket Name", "Region", "Lifecycle Rules", "Transition / Expiration Actions"])

    # Get all buckets (single API call)
    response = s3_client.list_buckets()
    buckets = response.get("Buckets", [])

    for bucket in buckets:
        bucket_name = bucket["Name"]

        # Default values
        region = "Unknown"
        rule_ids = "No Rules"
        actions = "No Rules"

        # Get region
        try:
            location = s3_client.get_bucket_location(Bucket=bucket_name)
            region = location.get("LocationConstraint") or "us-east-1"
        except Exception:
            region = "Error"

        # Get lifecycle rules
        try:
            lifecycle = s3_client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
            rules = lifecycle.get("Rules", [])
            if rules:
                rule_ids = ", ".join([rule.get("ID", "Unnamed Rule") for rule in rules])

                # Extract transition and expiration actions
                actions_list = []
                for rule in rules:
                    action_str = []
                    # Transition actions
                    transitions = rule.get("Transitions", [])
                    for t in transitions:
                        days = t.get("Days")
                        storage_class = t.get("StorageClass")
                        if days and storage_class:
                            action_str.append(f"Transition to {storage_class} after {days} days")
                    # Expiration action
                    expiration = rule.get("Expiration")
                    if expiration:
                        if "Days" in expiration:
                            action_str.append(f"Expire after {expiration['Days']} days")
                        elif "Date" in expiration:
                            action_str.append(f"Expire on {expiration['Date']}")
                    actions_list.append("; ".join(action_str))
                actions = " | ".join(actions_list)
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchLifecycleConfiguration":
                rule_ids = "Error"
                actions = "Error"

        # Append result to Excel
        ws.append([bucket_name, region, rule_ids, actions])

    # Save Excel
    wb.save(output_file)

if __name__ == "__main__":
    list_s3_buckets_with_lifecycle_to_excel("s3_buckets_life_cycle.xlsx")
    print("excel file saved successfully")
