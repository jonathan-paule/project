
import boto3
from openpyxl import Workbook

# Regions to check
REGIONS = ["us-east-1", "us-east-2", "us-west-2"]

def list_unused_ebs_to_excel(output_file="unused_ebs_volumes.xlsx"):
    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Unused EBS Volumes"

    # Add header row
    ws.append(["Volume ID", "Size (GiB)", "State", "Volume Type", "Region", "Created On"])

    for region in REGIONS:
        ec2_client = boto3.client("ec2", region_name=region)

        # Fetch all volumes in the region
        response = ec2_client.describe_volumes()
        volumes = response.get("Volumes", [])

        for vol in volumes:
            # Unused volumes => no attachments
            if len(vol.get("Attachments", [])) == 0:
                volume_id = vol["VolumeId"]
                size = vol["Size"]
                state = vol["State"]
                vol_type = vol["VolumeType"]
                created_on = str(vol["CreateTime"])

                # Add row to Excel
                ws.append([volume_id, size, state, vol_type, region, created_on])

    # Save Excel file
    wb.save(output_file)


if __name__ == "__main__":
    list_unused_ebs_to_excel("unused_ebs_volumes.xlsx")
    print("excel file saved successfully")
