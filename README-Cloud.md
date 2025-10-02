# Cloud Deployment Guide

All servers in this repository are containerized and can be deployed to cloud platforms for scalable, production-ready deployments. The servers support HTTP transport mode specifically designed for cloud deployments.

## AWS ECS Fargate Deployment

Amazon ECS Fargate provides serverless container hosting ideal for MCP servers. Below are generic instructions applicable to all servers in this repository.

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. An existing ECS cluster or create one using AWS Console/CLI
3. Docker image pushed to Amazon ECR (Elastic Container Registry)

### Step 1: Build and Push Docker Image

```bash
# Navigate to your chosen server directory
cd servers/mcp-neo4j-cypher  # or any other server

# Build the Docker image
docker build -t mcp-neo4j-server .

# Tag for ECR (replace with your region and account ID)
docker tag mcp-neo4j-server:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-neo4j-server:latest

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-neo4j-server:latest
```

### Step 2: Create ECS Task Definition

Create a task definition JSON file (`task-definition.json`):

```json
{
  "family": "mcp-neo4j-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "mcp-neo4j-server",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/mcp-neo4j-server:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "NEO4J_TRANSPORT",
          "value": "http"
        },
        {
          "name": "NEO4J_MCP_SERVER_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "NEO4J_MCP_SERVER_PORT",
          "value": "8000"
        }
      ],
      "secrets": [
        {
          "name": "NEO4J_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:neo4j-password-AbCdEf"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mcp-neo4j-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Step 3: Create ECS Service with Load Balancer

```bash
# Register the task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create an Application Load Balancer (ALB) through AWS Console or CLI
# Create target group for port 8000

# Create the ECS service
aws ecs create-service \
  --cluster your-ecs-cluster \
  --service-name mcp-neo4j-service \
  --task-definition mcp-neo4j-server:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345,subnet-67890],securityGroups=[sg-12345678],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/mcp-targets/1234567890123456,containerName=mcp-neo4j-server,containerPort=8000
```

### Step 4: Configure Auto Scaling

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/your-ecs-cluster/mcp-neo4j-service \
  --min-capacity 1 \
  --max-capacity 10

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/your-ecs-cluster/mcp-neo4j-service \
  --policy-name mcp-neo4j-scaling-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

Where `scaling-policy.json`:

```json
{
  "TargetValue": 70.0,
  "PredefinedMetricSpecification": {
    "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
  },
  "ScaleOutCooldown": 300,
  "ScaleInCooldown": 300
}
```

## Azure Container Apps Deployment

Azure Container Apps provides a serverless container platform perfect for MCP server deployments with built-in scaling and load balancing.

### Prerequisites

1. Azure CLI installed and logged in
2. Resource group and Container Apps environment
3. Container image pushed to Azure Container Registry (ACR)

### Step 1: Build and Push Docker Image

```bash
# Navigate to your chosen server directory
cd servers/mcp-neo4j-memory  # or any other server

# Build the Docker image
docker build -t mcp-neo4j-server .

# Create Azure Container Registry (if not exists)
az acr create --resource-group myResourceGroup --name myacrregistry --sku Basic

# Login to ACR
az acr login --name myacrregistry

# Tag and push image
docker tag mcp-neo4j-server:latest myacrregistry.azurecr.io/mcp-neo4j-server:latest
docker push myacrregistry.azurecr.io/mcp-neo4j-server:latest
```

### Step 2: Create Container Apps Environment

```bash
# Install the Container Apps extension
az extension add --name containerapp

# Create resource group
az group create --name myResourceGroup --location eastus

# Create Container Apps environment
az containerapp env create \
  --name myenvironment \
  --resource-group myResourceGroup \
  --location eastus
```

### Step 3: Deploy Container App

```bash
# Create the container app
az containerapp create \
  --name mcp-neo4j-app \
  --resource-group myResourceGroup \
  --environment myenvironment \
  --image myacrregistry.azurecr.io/mcp-neo4j-server:latest \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --secrets \
    neo4j-password=your-secret-password \
  --env-vars \
    NEO4J_TRANSPORT=http \
    NEO4J_MCP_SERVER_HOST=0.0.0.0 \
    NEO4J_MCP_SERVER_PORT=8000 \
    NEO4J_URI=bolt://your-neo4j-instance:7687 \
    NEO4J_USERNAME=neo4j \
    NEO4J_PASSWORD=secretref:neo4j-password
```

### Step 4: Configure Auto Scaling Rules

```bash
# Create HTTP scaling rule
az containerapp revision set-scaling-rule \
  --name mcp-neo4j-app \
  --resource-group myResourceGroup \
  --rule-name http-rule \
  --rule-type http \
  --http-concurrent-requests 10

# Create CPU scaling rule
az containerapp revision set-scaling-rule \
  --name mcp-neo4j-app \
  --resource-group myResourceGroup \
  --rule-name cpu-rule \
  --rule-type cpu \
  --cpu-utilization 70
```

### Step 5: Configure Load Balancing and Traffic Distribution

```bash
# Create additional revision for blue-green deployment
az containerapp revision copy \
  --name mcp-neo4j-app \
  --resource-group myResourceGroup \
  --from-revision mcp-neo4j-app--abc123 \
  --image myacrregistry.azurecr.io/mcp-neo4j-server:v2

# Configure traffic splitting
az containerapp ingress traffic set \
  --name mcp-neo4j-app \
  --resource-group myResourceGroup \
  --revision-weight mcp-neo4j-app--abc123=50 mcp-neo4j-app--def456=50
```

## Configuration Best Practices

### Environment Variables for Cloud Deployment

All servers support these common environment variables for cloud deployment:

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_TRANSPORT` | Set to `http` for cloud deployments | `stdio` |
| `NEO4J_MCP_SERVER_HOST` | Bind address (use `0.0.0.0` for containers) | `127.0.0.1` |
| `NEO4J_MCP_SERVER_PORT` | Port for HTTP server | `8000` |
| `NEO4J_MCP_SERVER_PATH` | URL path for MCP endpoint | `/api/mcp/` |
| `NEO4J_MCP_SERVER_ALLOWED_HOSTS` | Comma-separated allowed hosts | `localhost,127.0.0.1` |
| `NEO4J_MCP_SERVER_ALLOW_ORIGINS` | CORS allowed origins | (empty - secure by default) |

### Security Configuration

For production deployments, configure security settings:

```bash
# Environment variables for security
NEO4J_MCP_SERVER_ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
NEO4J_MCP_SERVER_ALLOW_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

### Health Checks

Configure health checks in your container orchestration platform:

- **Health Check Endpoint**: `GET /health` (if available) or `GET /api/mcp/`
- **Port**: `8000`
- **Protocol**: `HTTP`

### Resource Recommendations

Based on server type and expected load:

- **CPU**: 0.25-0.5 vCPU per instance (scale up for heavy workloads)
- **Memory**: 512MB-1GB per instance
- **Replicas**: Start with 2 for high availability, scale based on traffic

### Monitoring and Logging

- Enable container logs aggregation (CloudWatch Logs, Azure Monitor)
- Set up application performance monitoring
- Monitor HTTP response times and error rates
- Track container resource utilization

## Integration with MCP Clients

After deploying to cloud platforms, integrate with MCP clients using HTTP endpoints:

```json
{
  "mcpServers": {
    "neo4j-cloud": {
      "command": "npx",
      "args": ["-y", "mcp-remote@latest", "https://your-deployment-url/api/mcp/"]
    }
  }
}
```

This approach allows Claude Desktop and other MCP clients to connect to your cloud-deployed servers through HTTP proxy tools like `mcp-remote`.

## Troubleshooting

### Common Issues

1. **Container not starting**: Check environment variables and secrets configuration
2. **Health check failures**: Verify the container is listening on the correct port (8000) and host (0.0.0.0)
3. **Connection timeouts**: Ensure security groups/firewall rules allow traffic on port 8000
4. **CORS errors**: Configure `NEO4J_MCP_SERVER_ALLOW_ORIGINS` for your client domains
5. **Auto-scaling not working**: Verify scaling policies and metrics are properly configured

### Logging and Debugging

Enable debug logging by setting environment variables:

```bash
LOG_LEVEL=DEBUG
NEO4J_MCP_DEBUG=true
```

Monitor container logs through your cloud platform's logging service to troubleshoot deployment issues.