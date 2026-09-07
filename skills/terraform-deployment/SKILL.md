---
name: terraform-deployment
description: Use Terraform in kido-infra for deployments instead of manual configurations
---

# Terraform Deployment Strategy

Whenever the user requests deploying a new service, exposing a port to the web, or setting up monitoring/domains, you MUST use the existing Terraform configurations in `~/kido-infra/terraform`.

The user strongly prefers Infrastructure as Code. **DO NOT** suggest manual UI configurations for Nginx Proxy Manager, Cloudflare, Github, or Vercel. 

## Key Areas:

1. **Nginx Proxy Manager (`nginx_proxy_manager.tf`)**
   - Add new services to the `proxy_mappings` local variable.
   - **Crucial Rule:** ALWAYS map to the internal Docker `container_name` (e.g., `glitchtip-web`), NOT an IP address (`172.17.x.x`). 
   - Make sure the new Docker service is connected to the common bridge network (e.g., `ops_bridge`) so NPM can resolve it by name.
   - Example: `"sentry" = { host = "glitchtip-web", port = 8000 }`

2. **Cloudflare DNS (`cloudflare_dns.tf`)**
   - If adding a new subdomain that needs a DNS record, add it to the `dns_records` local variable.
   - Example: `"sentry" = { type = "A", value = "1.2.3.4", proxied = true }` (Check the existing file for the exact format).

3. **Cloudflare Zero Trust (`cloudflare_zero_trust.tf`)**
   - Used for internal access tunnels or secure routes.
   - **Crucial Rule:** BEFORE modifying or adding anything to Zero Trust, you MUST confirm with the user and explicitly explain the reasoning/security implications of why it is needed.

4. **Applying Changes & CI/CD Deployment Rules**
   - After updating the `.tf` files, explicitly inform the user that they just need to run `terraform apply` in `~/kido-infra/terraform` to deploy the infrastructure changes.
   - **Crucial Rule for Application Deployment:** ALL code and container deployments MUST be handled via an automated CI/CD pipeline (e.g., GitHub Actions). 
   - If there is no CI/CD pipeline set up for a project yet, you MUST proactively set one up (e.g., `.github/workflows/deploy.yml`) to automatically deploy on `push`.
   - **Database Migrations in CI/CD:** Default CI/CD pipelines MUST use safe migration commands (e.g., `npx prisma migrate deploy`). NEVER hardcode destructive commands like `migrate reset --force` into the automated pipeline. If a schema wipe/reset is needed due to massive refactoring, allow it to be run manually, but do not trigger it on every regular deployment.
   - **DO NOT** use SSH to manually pull code, `scp` files, or run `docker compose up` on the server for regular deployments. SSH access should ONLY be used for debugging, checking logs, and diagnosing critical issues, never as a replacement for automated deployments.

## General Rules:
- Never ask the user to "Go to the UI and click 'Add Proxy Host'". Update the `.tf` file instead.
- If the user adds a new Docker container (like Sentry/GlitchTip) that exposes a port, automatically add it to `nginx_proxy_manager.tf` and `cloudflare_dns.tf`.
