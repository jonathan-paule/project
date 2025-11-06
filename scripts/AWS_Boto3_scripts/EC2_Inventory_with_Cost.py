import boto3
import csv

# Define region-specific EC2 pricing (on-demand, per hour)
EC2_PRICING = {
    "us-east-1": {
        "t2.micro": 0.0116,
        "t2.large": 0.0928,
        "t3.micro": 0.0104,
        "t3.medium": 0.0416,
        "t3a.medium": 0.0376,
        "t3a.large": 0.0752,
        "t3a.xlarge": 0.1504,
        "t3a.2xlarge": 0.3008,
        "t2.xlarge": 0.1856,
        "t2.2xlarge": 0.3712,
        "t4g.xlarge": 0.1344,
        "c5a.4xlarge": 0.6880
    },
    "us-west-2": {
        "t2.micro": 0.0128,
        "t2.large": 0.0960,
        "t3.micro": 0.0110,
        "t3.medium": 0.0432,
        "t3a.medium": 0.0390,
        "t3a.large": 0.0780,
        "t3a.xlarge": 0.1560,
        "t3a.2xlarge": 0.3120,
        "t2.xlarge": 0.1920,
        "t2.2xlarge": 0.3840,
        "t4g.xlarge": 0.1380,
        "c5a.4xlarge": 0.7040
    }
}

# EBS pricing per GiB-month (approximate)
EBS_PRICING = {
    "gp2": 0.10,
    "gp3": 0.08
}

def get_instance_cost(region, instance_type):
    return EC2_PRICING.get(region, {}).get(instance_type, 0.0)

def get_volume_cost(volume_type, size):
    price_per_gib = EBS_PRICING.get(volume_type, 0.0)
    return price_per_gib * size

def fetch_ec2_data(region, writer, max_volumes=5):
    ec2 = boto3.client('ec2', region_name=region)
    response = ec2.describe_instances()

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instance_id = instance.get("InstanceId", "")
            instance_type = instance.get("InstanceType", "")
            ami_id = instance.get("ImageId", "")
            key_name = instance.get("KeyName", "")
            private_ip = instance.get("PrivateIpAddress", "")
            public_ip = instance.get("PublicIpAddress", "")
            state = instance.get("State", {}).get("Name", "")
            launch_time = str(instance.get("LaunchTime", ""))
            az = instance.get("Placement", {}).get("AvailabilityZone", "")
            vpc_id = instance.get("VpcId", "")
            subnet_id = instance.get("SubnetId", "")
            sg_names = ', '.join([sg['GroupName'] for sg in instance.get('SecurityGroups', [])])
            tags = ', '.join([f"{tag['Key']}={tag['Value']}" for tag in instance.get('Tags', [])])

            # Calculate instance cost per hour
            instance_cost = get_instance_cost(region, instance_type)

            # Get volumes
            volume_info = []
            volume_total_cost = 0.0
            block_devices = instance.get("BlockDeviceMappings", [])
            for bd in block_devices:
                if len(volume_info) >= max_volumes:
                    break

                volume_id = bd.get("Ebs", {}).get("VolumeId", "")
                volume_name = ""
                volume_size = ""
                volume_type = ""

                if volume_id:
                    vol_data = ec2.describe_volumes(VolumeIds=[volume_id])
                    if vol_data["Volumes"]:
                        volume = vol_data["Volumes"][0]
                        volume_size = volume.get("Size", 0)
                        volume_type = volume.get("VolumeType", "")
                        for tag in volume.get("Tags", []):
                            if tag["Key"] == "Name":
                                volume_name = tag["Value"]
                        # Calculate cost
                        vol_cost = get_volume_cost(volume_type, volume_size)
                        volume_total_cost += vol_cost
                        volume_info.append((volume_id, volume_name, volume_size, volume_type))

            # Pad volume info to fixed number of columns
            while len(volume_info) < max_volumes:
                volume_info.append(("", "", "", ""))

            row = [
                region,
                instance_id,
                instance_type,
                ami_id,
                key_name,
                private_ip,
                public_ip,
                state,
                launch_time,
                az,
                vpc_id,
                subnet_id,
                sg_names,
                tags,
                f"${instance_cost:.4f}/hr",
                f"${volume_total_cost:.2f}/mo"
            ]

            # Append volume details
            for vol_id, vol_name, vol_size, vol_type in volume_info:
                row.append(vol_id)
                row.append(vol_name)
                row.append(vol_size)
                row.append(vol_type)

            writer.writerow(row)

def main():
    regions = ["us-east-1", "us-west-2"]
    max_volumes = 8

    with open("EC2_inventory_costs.csv", mode='w', newline='') as file:
        writer = csv.writer(file)

        header = [
            "Region", "Instance ID", "Instance Type", "AMI ID", "Key Name", "Private IP", "Public IP",
            "State", "Launch Time", "Availability Zone", "VPC ID", "Subnet ID", "Security Groups",
            "Tags", "Instance Cost/hr", "Total Volume Cost/mo"
        ]

        for i in range(1, max_volumes + 1):
            header += [f"Volume{i}_ID", f"Volume{i}_Name", f"Volume{i}_Size", f"Volume{i}_Type"]

        writer.writerow(header)

        for region in regions:
            fetch_ec2_data(region, writer, max_volumes)

    print(" CSV file generated")

if __name__ == "__main__":
    main()
