# Kiro Configuration for {{muppet_name}}

This directory contains Kiro IDE configuration for the {{muppet_name}} Node.js Express microservice.

## Configuration Files

### MCP Servers (`settings/mcp.json`)

Configured MCP servers for enhanced development experience:

- **muppet-platform**: Direct integration with the Muppet Platform API
  - List and manage muppets
  - View service status and metrics
  - Access logs and monitoring data

- **nodejs-development**: Node.js specific development tools
  - Node.js version management
  - npm package management
  - TypeScript compilation
  - Testing and linting

- **aws-integration**: AWS service integration
  - ECS service management
  - CloudWatch logs access
  - ECR image management
  - Service health monitoring

### Steering Documents (`steering/`)

Language-specific and shared development guidelines:

- **Node.js Specific**:
  - `express-patterns.md` - Express.js best practices
  - `typescript-best-practices.md` - TypeScript development guide
  - `nodejs-performance.md` - Performance optimization
  - `testing-patterns.md` - Testing strategies with Jest

- **Shared Platform Standards**:
  - `shared/security.md` - Security requirements
  - `shared/logging.md` - Logging standards
  - `shared/testing.md` - Testing principles
  - `shared/performance.md` - Performance targets
  - `shared/infrastructure.md` - Infrastructure patterns

## Usage

### MCP Tools

Access platform tools directly from Kiro:

```typescript
// Example: Check muppet status
const status = await mcp.muppetPlatform.getMuppetStatus('{{muppet_name}}');

// Example: View logs
const logs = await mcp.muppetPlatform.getMuppetLogs('{{muppet_name}}', {
  lines: 100,
  follow: true
});

// Example: Run tests
const testResults = await mcp.nodejsDevelopment.runTests({
  coverage: true,
  watch: false
});
```

### Development Workflow

1. **Setup**: MCP servers auto-connect when opening the project
2. **Development**: Use steering documents for guidance
3. **Testing**: Run tests through MCP tools or npm scripts
4. **Deployment**: Monitor through AWS integration tools

### Customization

To customize the configuration:

1. **Add MCP Servers**: Edit `settings/mcp.json`
2. **Update Auto-Approve**: Add tool names to `autoApprove` arrays
3. **Environment Variables**: Modify `env` sections for each server

### Troubleshooting

Common issues and solutions:

1. **MCP Server Connection Failed**
   - Check if the platform is running: `make run` in platform directory
   - Verify Python environment and dependencies
   - Check port availability (8001 for mcp_http_bridge)

2. **Node.js Tools Not Working**
   - Ensure Node.js 20 LTS is installed
   - Verify npm dependencies are installed: `npm ci`
   - Check TypeScript configuration

3. **AWS Integration Issues**
   - Verify AWS credentials are configured
   - Check AWS region settings
   - Ensure proper IAM permissions for ECS/CloudWatch access

### Resources

- [Kiro Documentation](https://docs.kiro.dev/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Muppet Platform Docs](../../../docs/)
- [Node.js Best Practices](./steering/nodejs-best-practices.md)