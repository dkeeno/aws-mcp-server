#!/usr/bin/env python3
"""
AWS MCP Server
Provides tools for creating and managing AWS resources using boto3.
"""

import asyncio
import json
from typing import Any
import boto3
from botocore.exceptions import ClientError

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

server = Server("aws-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available AWS management tools."""
    return [
        Tool(
            name="create_ec2_instance",
            description="Create an EC2 instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "instance_type": {"type": "string", "description": "Instance type (e.g., t2.micro)", "default": "t2.micro"},
                    "ami_id": {"type": "string", "description": "AMI ID to use"},
                    "key_name": {"type": "string", "description": "SSH key pair name (optional)"},
                    "subnet_id": {"type": "string", "description": "Subnet ID (optional)"},
                    "security_group_ids": {"type": "array", "items": {"type": "string"}, "description": "Security group IDs"},
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "ami_id"]
            }
        ),
        Tool(
            name="create_s3_bucket",
            description="Create an S3 bucket",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "bucket_name": {"type": "string", "description": "Bucket name (must be globally unique)"},
                    "enable_versioning": {"type": "boolean", "description": "Enable versioning", "default": False},
                    "enable_encryption": {"type": "boolean", "description": "Enable default encryption", "default": True},
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "bucket_name"]
            }
        ),
        Tool(
            name="create_vpc",
            description="Create a VPC",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "cidr_block": {"type": "string", "description": "VPC CIDR block (e.g., 10.0.0.0/16)"},
                    "enable_dns_hostnames": {"type": "boolean", "description": "Enable DNS hostnames", "default": True},
                    "enable_dns_support": {"type": "boolean", "description": "Enable DNS support", "default": True},
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "cidr_block"]
            }
        ),
        Tool(
            name="create_subnet",
            description="Create a subnet in a VPC",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "vpc_id": {"type": "string", "description": "VPC ID"},
                    "cidr_block": {"type": "string", "description": "Subnet CIDR block"},
                    "availability_zone": {"type": "string", "description": "Availability zone"},
                    "map_public_ip": {"type": "boolean", "description": "Auto-assign public IP", "default": False},
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "vpc_id", "cidr_block", "availability_zone"]
            }
        ),
        Tool(
            name="create_security_group",
            description="Create a security group",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "group_name": {"type": "string", "description": "Security group name"},
                    "description": {"type": "string", "description": "Security group description"},
                    "vpc_id": {"type": "string", "description": "VPC ID"},
                    "ingress_rules": {
                        "type": "array",
                        "description": "Ingress rules",
                        "items": {
                            "type": "object",
                            "properties": {
                                "protocol": {"type": "string", "description": "Protocol (tcp, udp, icmp, -1 for all)"},
                                "from_port": {"type": "integer", "description": "From port"},
                                "to_port": {"type": "integer", "description": "To port"},
                                "cidr": {"type": "string", "description": "CIDR block"}
                            }
                        }
                    },
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "group_name", "description", "vpc_id"]
            }
        ),
        Tool(
            name="create_rds_instance",
            description="Create an RDS database instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "db_instance_identifier": {"type": "string", "description": "DB instance identifier"},
                    "db_instance_class": {"type": "string", "description": "Instance class (e.g., db.t3.micro)"},
                    "engine": {"type": "string", "description": "Database engine (mysql, postgres, etc.)"},
                    "master_username": {"type": "string", "description": "Master username"},
                    "master_password": {"type": "string", "description": "Master password"},
                    "allocated_storage": {"type": "integer", "description": "Storage in GB", "default": 20},
                    "vpc_security_group_ids": {"type": "array", "items": {"type": "string"}},
                    "db_subnet_group_name": {"type": "string", "description": "DB subnet group name"},
                    "tags": {"type": "object", "description": "Tags to apply"}
                },
                "required": ["region", "db_instance_identifier", "db_instance_class", "engine", "master_username", "master_password"]
            }
        ),
        Tool(
            name="list_resources",
            description="List AWS resources of a specific type",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "resource_type": {
                        "type": "string",
                        "description": "Resource type to list",
                        "enum": ["ec2", "s3", "vpc", "subnet", "rds", "security_groups"]
                    }
                },
                "required": ["region", "resource_type"]
            }
        ),
        Tool(
            name="describe_resource",
            description="Get detailed information about a specific AWS resource",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "resource_type": {"type": "string", "description": "Resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID"}
                },
                "required": ["region", "resource_type", "resource_id"]
            }
        ),
        Tool(
            name="delete_resource",
            description="Delete an AWS resource (use with caution!)",
            inputSchema={
                "type": "object",
                "properties": {
                    "region": {"type": "string", "description": "AWS region"},
                    "resource_type": {"type": "string", "description": "Resource type"},
                    "resource_id": {"type": "string", "description": "Resource ID"},
                    "force": {"type": "boolean", "description": "Force deletion", "default": False}
                },
                "required": ["region", "resource_type", "resource_id"]
            }
        )
    ]


def apply_tags(client, resource_id: str, tags: dict):
    """Apply tags to an AWS resource."""
    if tags:
        tag_list = [{"Key": k, "Value": v} for k, v in tags.items()]
        client.create_tags(Resources=[resource_id], Tags=tag_list)


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for AWS operations."""

    try:
        region = arguments.get("region", "us-east-1")

        if name == "create_ec2_instance":
            ec2 = boto3.client("ec2", region_name=region)

            params = {
                "ImageId": arguments["ami_id"],
                "InstanceType": arguments.get("instance_type", "t2.micro"),
                "MinCount": 1,
                "MaxCount": 1
            }

            if "key_name" in arguments:
                params["KeyName"] = arguments["key_name"]
            if "subnet_id" in arguments:
                params["SubnetId"] = arguments["subnet_id"]
            if "security_group_ids" in arguments:
                params["SecurityGroupIds"] = arguments["security_group_ids"]

            response = ec2.run_instances(**params)
            instance_id = response["Instances"][0]["InstanceId"]

            if "tags" in arguments:
                apply_tags(ec2, instance_id, arguments["tags"])

            return [TextContent(
                type="text",
                text=f"✓ EC2 instance created successfully\nInstance ID: {instance_id}\nState: {response['Instances'][0]['State']['Name']}"
            )]

        elif name == "create_s3_bucket":
            s3 = boto3.client("s3", region_name=region)
            bucket_name = arguments["bucket_name"]

            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region}
                )

            if arguments.get("enable_versioning", False):
                s3.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={"Status": "Enabled"}
                )

            if arguments.get("enable_encryption", True):
                s3.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
                    }
                )

            if "tags" in arguments:
                tag_set = [{"Key": k, "Value": v} for k, v in arguments["tags"].items()]
                s3.put_bucket_tagging(Bucket=bucket_name, Tagging={"TagSet": tag_set})

            return [TextContent(
                type="text",
                text=f"✓ S3 bucket created successfully\nBucket name: {bucket_name}\nRegion: {region}"
            )]

        elif name == "create_vpc":
            ec2 = boto3.client("ec2", region_name=region)

            response = ec2.create_vpc(CidrBlock=arguments["cidr_block"])
            vpc_id = response["Vpc"]["VpcId"]

            if arguments.get("enable_dns_hostnames", True):
                ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={"Value": True})
            if arguments.get("enable_dns_support", True):
                ec2.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={"Value": True})

            if "tags" in arguments:
                apply_tags(ec2, vpc_id, arguments["tags"])

            return [TextContent(
                type="text",
                text=f"✓ VPC created successfully\nVPC ID: {vpc_id}\nCIDR: {arguments['cidr_block']}"
            )]

        elif name == "create_subnet":
            ec2 = boto3.client("ec2", region_name=region)

            response = ec2.create_subnet(
                VpcId=arguments["vpc_id"],
                CidrBlock=arguments["cidr_block"],
                AvailabilityZone=arguments["availability_zone"]
            )
            subnet_id = response["Subnet"]["SubnetId"]

            if arguments.get("map_public_ip", False):
                ec2.modify_subnet_attribute(
                    SubnetId=subnet_id,
                    MapPublicIpOnLaunch={"Value": True}
                )

            if "tags" in arguments:
                apply_tags(ec2, subnet_id, arguments["tags"])

            return [TextContent(
                type="text",
                text=f"✓ Subnet created successfully\nSubnet ID: {subnet_id}\nCIDR: {arguments['cidr_block']}\nAZ: {arguments['availability_zone']}"
            )]

        elif name == "create_security_group":
            ec2 = boto3.client("ec2", region_name=region)

            response = ec2.create_security_group(
                GroupName=arguments["group_name"],
                Description=arguments["description"],
                VpcId=arguments["vpc_id"]
            )
            sg_id = response["GroupId"]

            if "ingress_rules" in arguments:
                for rule in arguments["ingress_rules"]:
                    ec2.authorize_security_group_ingress(
                        GroupId=sg_id,
                        IpProtocol=rule["protocol"],
                        FromPort=rule.get("from_port", 0),
                        ToPort=rule.get("to_port", 0),
                        CidrIp=rule.get("cidr", "0.0.0.0/0")
                    )

            if "tags" in arguments:
                apply_tags(ec2, sg_id, arguments["tags"])

            return [TextContent(
                type="text",
                text=f"✓ Security group created successfully\nSG ID: {sg_id}\nName: {arguments['group_name']}"
            )]

        elif name == "create_rds_instance":
            rds = boto3.client("rds", region_name=region)

            params = {
                "DBInstanceIdentifier": arguments["db_instance_identifier"],
                "DBInstanceClass": arguments["db_instance_class"],
                "Engine": arguments["engine"],
                "MasterUsername": arguments["master_username"],
                "MasterUserPassword": arguments["master_password"],
                "AllocatedStorage": arguments.get("allocated_storage", 20)
            }

            if "vpc_security_group_ids" in arguments:
                params["VpcSecurityGroupIds"] = arguments["vpc_security_group_ids"]
            if "db_subnet_group_name" in arguments:
                params["DBSubnetGroupName"] = arguments["db_subnet_group_name"]
            if "tags" in arguments:
                params["Tags"] = [{"Key": k, "Value": v} for k, v in arguments["tags"].items()]

            response = rds.create_db_instance(**params)
            db_id = response["DBInstance"]["DBInstanceIdentifier"]

            return [TextContent(
                type="text",
                text=f"✓ RDS instance created successfully\nDB ID: {db_id}\nEngine: {arguments['engine']}\nStatus: {response['DBInstance']['DBInstanceStatus']}"
            )]

        elif name == "list_resources":
            resource_type = arguments["resource_type"]

            if resource_type == "ec2":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_instances()
                instances = []
                for reservation in response["Reservations"]:
                    for instance in reservation["Instances"]:
                        instances.append(f"{instance['InstanceId']} - {instance['State']['Name']} - {instance.get('InstanceType', 'N/A')}")
                return [TextContent(type="text", text=f"EC2 Instances:\n" + "\n".join(instances) if instances else "No instances found")]

            elif resource_type == "s3":
                s3 = boto3.client("s3", region_name=region)
                response = s3.list_buckets()
                buckets = [b["Name"] for b in response["Buckets"]]
                return [TextContent(type="text", text=f"S3 Buckets:\n" + "\n".join(buckets) if buckets else "No buckets found")]

            elif resource_type == "vpc":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_vpcs()
                vpcs = [f"{vpc['VpcId']} - {vpc['CidrBlock']}" for vpc in response["Vpcs"]]
                return [TextContent(type="text", text=f"VPCs:\n" + "\n".join(vpcs) if vpcs else "No VPCs found")]

            elif resource_type == "subnet":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_subnets()
                subnets = [f"{s['SubnetId']} - {s['CidrBlock']} - {s['AvailabilityZone']}" for s in response["Subnets"]]
                return [TextContent(type="text", text=f"Subnets:\n" + "\n".join(subnets) if subnets else "No subnets found")]

            elif resource_type == "rds":
                rds = boto3.client("rds", region_name=region)
                response = rds.describe_db_instances()
                instances = [f"{db['DBInstanceIdentifier']} - {db['Engine']} - {db['DBInstanceStatus']}" for db in response["DBInstances"]]
                return [TextContent(type="text", text=f"RDS Instances:\n" + "\n".join(instances) if instances else "No RDS instances found")]

            elif resource_type == "security_groups":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_security_groups()
                sgs = [f"{sg['GroupId']} - {sg['GroupName']}" for sg in response["SecurityGroups"]]
                return [TextContent(type="text", text=f"Security Groups:\n" + "\n".join(sgs) if sgs else "No security groups found")]

        elif name == "describe_resource":
            resource_type = arguments["resource_type"]
            resource_id = arguments["resource_id"]

            if resource_type == "ec2":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_instances(InstanceIds=[resource_id])
                return [TextContent(type="text", text=json.dumps(response["Reservations"][0]["Instances"][0], indent=2, default=str))]

            elif resource_type == "vpc":
                ec2 = boto3.client("ec2", region_name=region)
                response = ec2.describe_vpcs(VpcIds=[resource_id])
                return [TextContent(type="text", text=json.dumps(response["Vpcs"][0], indent=2, default=str))]

            return [TextContent(type="text", text=f"Describe not yet implemented for {resource_type}")]

        elif name == "delete_resource":
            return [TextContent(type="text", text="Delete operations require careful implementation. Please use AWS Console or CLI for deletions.")]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except ClientError as e:
        return [TextContent(type="text", text=f"AWS Error: {e.response['Error']['Code']}: {e.response['Error']['Message']}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
