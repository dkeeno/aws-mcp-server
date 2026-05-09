# AWS MCP Server

An MCP server that provides tools for creating and managing AWS resources using boto3.

## Features

### Resource Creation
- **create_ec2_instance**: Launch EC2 instances
- **create_s3_bucket**: Create S3 buckets with versioning and encryption
- **create_vpc**: Create VPCs with DNS settings
- **create_subnet**: Create subnets in VPCs
- **create_security_group**: Create security groups with ingress rules
- **create_rds_instance**: Create RDS database instances

### Resource Management
- **list_resources**: List resources by type (EC2, S3, VPC, subnets, RDS, security groups)
- **describe_resource**: Get detailed information about specific resources
- **delete_resource**: Delete resources (with safety checks)

## Prerequisites

- Python 3.10+
- AWS CLI configured with credentials
- Appropriate AWS IAM permissions

## Installation

```bash
cd aws-mcp-server
pip install -r requirements.txt
```

## AWS Credentials

Configure AWS credentials using one of these methods:

1. **AWS CLI**: `aws configure`
2. **Environment variables**:
   ```bash
   export AWS_ACCESS_KEY_ID=your_key
   export AWS_SECRET_ACCESS_KEY=your_secret
   export AWS_DEFAULT_REGION=us-east-1
   ```
3. **IAM role** (if running on EC2)

## Configuration

Add to your Claude Code settings (~/.claude/settings.json):

```json
{
  "mcpServers": {
    "aws": {
      "command": "python",
      "args": ["/Users/youruser/Documents/Base/DevOps-ClaudeAi/test-cases/SM1/my-first-vpc/aws-mcp-server/server.py"]
    }
  }
}
```

## Usage Examples

```
User: "Create a VPC with CIDR 10.0.0.0/16 in us-east-1"
Claude: [calls create_vpc]

User: "List all EC2 instances in us-west-2"
Claude: [calls list_resources with resource_type=ec2, region=us-west-2]

User: "Create an S3 bucket named my-app-bucket with versioning enabled"
Claude: [calls create_s3_bucket with enable_versioning=true]

User: "Create a t2.micro EC2 instance using ami-12345"
Claude: [calls create_ec2_instance]
```

## Security Notes

⚠️ **IMPORTANT**:
- This server can create real AWS resources that incur costs
- Always review actions before confirming
- Use IAM policies to limit permissions (principle of least privilege)
- Consider using AWS Budget Alerts
- The delete_resource tool is intentionally restricted - use AWS Console for deletions

## Recommended IAM Policy

Create a restricted IAM user/role with only the permissions you need:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "ec2:RunInstances",
        "ec2:CreateVpc",
        "ec2:CreateSubnet",
        "ec2:CreateSecurityGroup",
        "s3:CreateBucket",
        "s3:ListBucket",
        "s3:PutBucketVersioning",
        "rds:CreateDBInstance",
        "rds:DescribeDBInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

## Error Handling

The server provides detailed error messages from AWS API responses, including:
- Permission errors (Access Denied)
- Resource conflicts (already exists)
- Quota limits exceeded
- Invalid parameters
