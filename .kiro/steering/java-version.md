---
inclusion: always
---

# Java Version Requirements

## Mandatory: Amazon Corretto 21 (LTS)

All Java components MUST use **Amazon Corretto 21 LTS**.

### LTS Only Policy
- ✅ **Java 21 LTS** (September 2023) - USE THIS
- ❌ **Java 22, 23, 24, 25** - Non-LTS versions prohibited
- ⚠️ **Java 17 LTS** - Legacy systems only

### Why Java 21 LTS?
- Extended support until September 2031
- Full ecosystem compatibility (Gradle, Micronaut, libraries)
- Performance improvements over Java 17
- Modern features: virtual threads, pattern matching, records
- AWS optimization and regular security patches

### Implementation
```gradle
java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}
```

```dockerfile
FROM amazoncorretto:21-alpine
```

### Installation
```bash
# macOS
brew install --cask corretto@21

# Verify
java -version  # Should show "21.x.x" and "LTS"
```

#### 3. Docker Configuration
```dockerfile
FROM amazoncorretto:21-alpine AS builder
# ... build stage

FROM amazoncorretto:21-alpine
# ... runtime stage
```

#### 4. CI/CD Pipeline
```yaml
- name: Set up Amazon Corretto JDK 21
  uses: actions/setup-java@v4
  with:
    java-version: '21'
    distribution: 'corretto'
```

#### 5. Local Development
Update init scripts to check for Java 21 LTS specifically:
```bash
JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
if [ "$JAVA_VERSION" -ne 21 ]; then
    echo "❌ Java 21 LTS required, found Java $JAVA_VERSION"
    if [ "$JAVA_VERSION" -gt 21 ]; then
        echo "⚠️  Java $JAVA_VERSION is newer than Java 21 LTS and may cause compatibility issues"
        echo "   Non-LTS Java versions are not supported in production environments"
    fi
    echo "Please install Amazon Corretto 21 LTS: https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html"
    exit 1
fi
```

#### 6. Version Validation
Enforce LTS-only policy:
```bash
# Check for non-LTS versions and warn
if [ "$JAVA_VERSION" -eq 22 ] || [ "$JAVA_VERSION" -eq 23 ] || [ "$JAVA_VERSION" -eq 24 ] || [ "$JAVA_VERSION" -ge 25 ]; then
    echo "🚨 WARNING: Java $JAVA_VERSION detected"
    echo "   This is a non-LTS version and may cause build failures"
    echo "   Gradle plugins and Micronaut may not support this version"
    echo "   Please downgrade to Java 21 LTS for stability"
fi
```

### Migration Strategy

#### For New Muppets
- All new muppets created must use Java 21 LTS exactly
- Template generation automatically uses Java 21 LTS configuration
- Build scripts validate Java version and reject non-LTS versions

#### For Existing Muppets
- Existing muppets should be migrated to Java 21 LTS during their next major update cycle
- Migration should be tested thoroughly in staging environments
- Update documentation and README files to reflect Java 21 LTS requirements
- **Do not upgrade to non-LTS versions** (Java 22, 23, 24, etc.)

#### When Java 25 LTS is Released (September 2025)
- Wait 6 months after release for ecosystem maturity
- Validate Gradle, Micronaut, and all plugins support Java 25 LTS
- Create migration plan and test thoroughly
- Update this steering document with Java 25 LTS requirements

### Compatibility Considerations

#### Dependencies
- Ensure all Micronaut dependencies are compatible with Java 21 LTS
- Update any third-party libraries that may have Java 21 compatibility issues
- Test thoroughly with Java 21 LTS before deployment

#### Runtime Behavior
- Virtual threads can be enabled for improved concurrency performance
- Monitor memory usage patterns which may differ from Java 17
- Validate that all existing functionality works correctly with Java 21 LTS

#### Build Tool Compatibility
- **Gradle**: Use versions 8.5+ for full Java 21 LTS support
- **Micronaut Plugin**: Use version 4.0.4+ for Java 21 LTS compatibility
- **JaCoCo**: Use version 0.8.11+ for Java 21 LTS compatibility
- **Maven**: Use version 3.9.0+ if using Maven instead of Gradle

### Common Issues with Non-LTS Versions

#### Java 22-25 (Non-LTS) Problems:
- **Gradle Plugin Incompatibility**: Many plugins don't support non-LTS versions
- **Micronaut Issues**: Framework may not be tested with bleeding-edge Java
- **Library Conflicts**: Third-party libraries often lag behind Java releases
- **Build Failures**: Cryptic errors like "Unsupported class file major version"
- **Production Risk**: Untested combinations in production environments

### Installation Links

- **Amazon Corretto 21 Downloads**: https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/downloads-list.html
- **macOS**: `brew install --cask corretto21`
- **Linux**: Download from AWS or use package managers
- **Windows**: Download MSI installer from AWS

### Verification

To verify Java version in your environment:
```bash
java -version
# Should show EXACTLY: openjdk version "21.x.x" 2024-xx-xx LTS
# OpenJDK Runtime Environment Corretto-21.x.x.x (build 21.x.x+xx-LTS)

# Verify it's LTS
java -version 2>&1 | grep -q "21.*LTS" && echo "✅ Java 21 LTS detected" || echo "❌ Non-LTS Java version detected"
```

### Troubleshooting Non-LTS Issues

If you encounter build failures with Java 22+:

1. **Check Java Version**: `java -version`
2. **Install Java 21 LTS**: `brew install --cask corretto21`
3. **Set JAVA_HOME**: `export JAVA_HOME=/Library/Java/JavaVirtualMachines/amazon-corretto-21.jdk/Contents/Home`
4. **Verify Gradle Uses Correct Java**: `./gradlew --version`
5. **Clean and Rebuild**: `./gradlew clean build`

### Enforcement

This LTS-only requirement is enforced through:
- Template validation during muppet creation (rejects non-LTS Java)
- CI/CD pipeline checks that fail on incorrect Java versions
- Local development script validation with LTS-specific checks
- Code review requirements for Java version consistency
- Build script warnings for non-LTS Java versions

### Support and Resources

- [Amazon Corretto 21 User Guide](https://docs.aws.amazon.com/corretto/latest/corretto-21-ug/)
- [Java 21 Release Notes](https://openjdk.org/projects/jdk/21/)
- [Migration Guide from Java 17 to 21](https://docs.oracle.com/en/java/javase/21/migrate/getting-started.html)
- [Java LTS Release Schedule](https://www.oracle.com/java/technologies/java-se-support-roadmap.html)

### Policy Summary

✅ **ALLOWED**: Java 21 LTS (Amazon Corretto 21)  
⚠️ **LEGACY**: Java 17 LTS (for existing systems only)  
❌ **FORBIDDEN**: Java 22, 23, 24, 25 (non-LTS versions)  
🔮 **FUTURE**: Java 25 LTS (when ecosystem is ready, ~March 2026)