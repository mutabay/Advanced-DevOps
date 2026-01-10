# Terraform

A module = reusable infrastructure component.
Every serious Terraform setup is built on modules, not ad-hoc files.

**Core concepts in Terraform.**

## 1. Advanced Modules  
- Modules make Terraform reusable and clean.
- A module should only solve one responsibility (VPC, IAM, EKS, Monitoring).
- Inputs = configuration.  
- Outputs = values for other modules.  
- Avoid hardcoded environment logic.

**Key idea:** Good Terraform = well-designed modules.

---

## 2. Dependency Graph
Terraform builds a **graph** of resources and applies them in the correct order.

- Dependencies come from references.  
- Parallel execution is automatic.  
- Use `depends_on` only when necessary.  
- Avoid dependency cycles.

**Key idea:** The graph determines execution, not file order.

---

## 3. Workspaces
- Each workspace has its own **state**.  
- Useful for dev/staging/prod separation.  
- Not ideal for large enterprises (they prefer separate env folders).

**Key idea:** Workspaces = isolated state environments.

---

## 4. Remote State + Locking
Use:
- **S3 bucket** for state storage  
- **DynamoDB** for state locking  

S3 stores the Terraform state because it handles large, versioned files.
DynamoDB provides locking because S3 cannot lock.

Benefits:
- Collaboration  
- Prevent state corruption  
- Shared source of truth  

**Key idea:** Never use local state in real systems.

---

## 5. Drift Detection
Drift = Infra changed outside Terraform.

Detect with:
terraform plan
terraform plan -detailed-exitcode

yaml
Copy code

Tools:
- driftctl (concept)  
- AWS Config for cloud-based drift alerts  

**Key idea:** Terraform must remain the source of truth.

---

## 6. Policy Validation (Sentinel / OPA)
Policies enforce rules before apply.

Examples:
- No public S3 buckets  
- No wildcard IAM permissions  
- Only approved instance types  
- Monitoring required for all services  

**Tools:**
- **Sentinel** → Terraform Cloud  
- **OPA/Rego** → flexible, vendor-neutral  

**Key idea:** Policy = safety net for IaC.

---

## 7. Practice Work
Write modules for:
- VPC (subnets, routing, IGW, NAT)
- Kubernetes cluster (EKS/GKE/K3s)
- IAM roles and policies
- Monitoring & logging stack

Then build a reusable **platform module** combining them.

**Goal:** A clean Terraform structure used across environments.

---

# Summary
- Modules = reusable infrastructure building blocks.
- State must be remote and locked.
- Terraform follows a dependency graph, not file order.
- Drift detection ensures cloud and code stay in sync.
- Policies make IaC safe and compliant.