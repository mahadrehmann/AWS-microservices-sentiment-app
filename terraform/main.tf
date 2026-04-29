# =============================================================================
# Terraform — AWS EC2 Provisioning for Kubernetes Deployment
# =============================================================================
#
# This file provisions the single EC2 node that will host the microk8s cluster
# running the SentimentAI microservices (backend + frontend).
#
# Usage:
#   terraform init           # Download AWS provider plugin
#   terraform plan           # Preview what will be created
#   terraform apply          # Create the resources
#   terraform destroy        # Tear everything down
#
# Prerequisites:
#   - AWS CLI configured:  aws configure
#   - An SSH key pair created in AWS EC2 → Key Pairs console
#   - Set your key pair name in terraform.tfvars (see terraform.tfvars.example)
# =============================================================================

# ── Provider ──────────────────────────────────────────────────────────────────
provider "aws" {
  region = var.aws_region
}

# ── Variables ─────────────────────────────────────────────────────────────────
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "key_pair_name" {
  description = "Name of the existing AWS EC2 Key Pair for SSH access"
  type        = string
  # Set this in terraform.tfvars — never hardcode secrets in .tf files
}

variable "instance_type" {
  description = "EC2 instance type (t3.medium recommended for microk8s + HuggingFace)"
  type        = string
  default     = "t3.small"
}

# ── Security Group ────────────────────────────────────────────────────────────
resource "aws_security_group" "k8s_sg" {
  name        = "k8s_security_group"
  description = "Allow inbound SSH and HTTP"

  # SSH — required for Ansible to configure the node
  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP — frontend served by Nginx / K8s NodePort
  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # NodePort range — for Kubernetes NodePort services (30000-32767)
  ingress {
    description = "Kubernetes NodePort range"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Kubernetes API"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # All outbound traffic allowed (package installs, image pulls, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "CloudProject-K8s-SG"
    Project = "SentimentAI"
  }
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────
resource "aws_instance" "k8s_node" {
  # Ubuntu 24.04 LTS (HVM), SSD Volume Type — us-east-1
  # If deploying to a different region, look up the correct AMI at:
  # https://cloud-images.ubuntu.com/locator/ec2/
  ami           = "ami-04b70fa74e45c3917"
  instance_type = var.instance_type

  key_name               = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.k8s_sg.id]

  # Root volume: 20 GB is the minimum comfortable size for microk8s +
  # Docker images (DistilBERT image alone is ~1.5 GB).
  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name    = "CloudProject-K8s-Node"
    Project = "SentimentAI"
  }
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "instance_public_ip" {
  value       = aws_instance.k8s_node.public_ip
  description = "The public IP of the EC2 instance — use this in Ansible inventory"
}

output "instance_id" {
  value       = aws_instance.k8s_node.id
  description = "EC2 Instance ID"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_instance.k8s_node.public_ip}"
  description = "Ready-to-use SSH command to connect to the EC2 instance"
}
