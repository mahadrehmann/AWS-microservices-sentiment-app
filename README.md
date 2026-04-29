# Cloud Project Deployment Guide

This project deploys a frontend and a lightweight mock backend on a single-node K3s cluster running on AWS EC2.

## Components

- Terraform: provisions the EC2 instance and security group
- Ansible: installs K3s, creates swap, and fetches kubeconfig
- Kubernetes manifests: deploy frontend, backend, and services
- GitHub Actions: builds and pushes Docker images to Docker Hub
- ArgoCD: syncs the `k8s/` folder to the cluster

## Deployment Steps

### 1. Provision the AWS instance

From the `terraform/` directory:

```bash
terraform init
terraform apply
```

This creates the EC2 instance and prints its public IP.

### 2. Update the Ansible inventory

Edit `ansible/inventory.ini` and replace the old IP with the new EC2 public IP.

### 3. Configure the K3s node

From the `ansible/` directory:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

This installs K3s, sets up swap, and copies kubeconfig back to the project root.

### 4. Point local kubectl to the new cluster

From the project root:

```bash
export KUBECONFIG="$PWD/kubeconfig.yaml"
kubectl config set-cluster default --server=https://<EC2_PUBLIC_IP>:6443
kubectl config set clusters.default.insecure-skip-tls-verify true
kubectl config unset clusters.default.certificate-authority-data
kubectl get nodes -o wide
```

### 5. Deploy the application

Apply the Kubernetes manifests:

```bash
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml
```

Check rollout status:

```bash
kubectl rollout status deployment/sentiment-backend --timeout=180s
kubectl rollout status deployment/sentiment-frontend --timeout=180s
kubectl get pods -o wide
kubectl get svc
```

### 6. Access the application

- Frontend: `http://<EC2_PUBLIC_IP>:30080`
- Backend: exposed inside the cluster on port `8000`

## GitHub Actions CI

The workflow at `.github/workflows/main.yml` runs on pushes to `main` and:

1. Builds backend and frontend images
2. Pushes them to Docker Hub under the `mahad4` account
3. Updates the image tags in `k8s/backend.yaml` and `k8s/frontend.yaml`
4. Commits the updated manifests back to the repository

## ArgoCD CD

The ArgoCD application manifest at `argocd/argocd-app.yaml` watches the `k8s/` directory and auto-syncs changes to the cluster.

To install ArgoCD manually:

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd patch svc argocd-server -p '{"spec":{"type":"NodePort"}}'
kubectl apply -f argocd/argocd-app.yaml
```

## Notes

- Do not commit `kubeconfig.yaml` if it contains cluster credentials.
- The backend is intentionally lightweight and returns a fixed mock sentiment response.
- If the EC2 instance is recreated, update the IP in `ansible/inventory.ini` and `kubeconfig.yaml`.
