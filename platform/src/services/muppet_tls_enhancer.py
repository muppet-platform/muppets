"""
Muppet TLS Enhancer Service

Automatically enhances existing muppets with TLS without requiring configuration changes.
Implements the "Zero Breaking Changes" principle from the TLS-by-default design.
"""

from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..config import get_settings
from ..logging_config import get_logger
from .tls_auto_generator import TLSAutoGenerator

logger = get_logger(__name__)


class MuppetTLSEnhancer:
    """Automatically enhances existing muppets with TLS configuration."""

    def __init__(self):
        """Initialize the TLS enhancer with AWS clients."""
        try:
            settings = get_settings()
            self.elbv2_client = boto3.client("elbv2", region_name=settings.aws.region)
            self.route53_client = boto3.client(
                "route53", region_name=settings.aws.region
            )
            self.ec2_client = boto3.client("ec2", region_name=settings.aws.region)
            self.tls_generator = TLSAutoGenerator()
            logger.info("Muppet TLS enhancer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize muppet TLS enhancer: {e}")
            raise

    async def enhance_muppet_with_tls(self, muppet_name: str) -> Dict[str, Any]:
        """
        Enhance an existing muppet with TLS configuration.

        This method implements the "Zero Breaking Changes" principle by:
        1. Discovering the existing ALB for the muppet
        2. Adding HTTPS listener with wildcard certificate
        3. Adding HTTPS security group rules if needed
        4. Creating DNS record pointing to the ALB
        5. Configuring HTTP→HTTPS redirect

        No changes required to the muppet's configuration.

        Args:
            muppet_name: Name of the muppet to enhance

        Returns:
            Dictionary with enhancement results
        """
        try:
            logger.info(f"Starting TLS enhancement for muppet: {muppet_name}")

            # Step 1: Discover existing ALB
            alb_info = await self._discover_muppet_alb(muppet_name)
            if not alb_info:
                return {
                    "success": False,
                    "error": f"No ALB found for muppet: {muppet_name}",
                    "muppet_name": muppet_name,
                }

            # Step 2: Generate TLS configuration
            tls_config = self.tls_generator.generate_muppet_tls_config(muppet_name)

            # Step 3: Add HTTPS listener to existing ALB
            https_listener = await self._add_https_listener(alb_info, tls_config)

            # Step 4: Create DNS record
            dns_record = await self._create_dns_record(
                muppet_name, alb_info, tls_config
            )

            # Step 5: Configure HTTP→HTTPS redirect
            redirect_result = await self._configure_http_redirect(alb_info)

            logger.info(
                f"TLS enhancement completed successfully for muppet: {muppet_name}"
            )

            return {
                "success": True,
                "muppet_name": muppet_name,
                "https_endpoint": f"https://{muppet_name}.s3u.dev",
                "http_endpoint": f"http://{alb_info['dns_name']}",
                "alb_arn": alb_info["arn"],
                "https_listener_arn": https_listener.get("arn"),
                "dns_record_created": dns_record.get("success", False),
                "redirect_configured": redirect_result.get("success", False),
                "security_group_updated": https_listener.get(
                    "security_group_updated", False
                ),
                "tls_config": tls_config,
            }

        except Exception as e:
            logger.error(f"Failed to enhance muppet {muppet_name} with TLS: {e}")
            return {"success": False, "error": str(e), "muppet_name": muppet_name}

    async def _discover_muppet_alb(self, muppet_name: str) -> Optional[Dict[str, Any]]:
        """Discover the existing ALB for a muppet."""
        try:
            logger.info(f"Discovering ALB for muppet: {muppet_name}")

            # Look for ALB with the expected naming pattern
            alb_name = f"{muppet_name}-alb"

            response = self.elbv2_client.describe_load_balancers(Names=[alb_name])

            if not response.get("LoadBalancers"):
                logger.warning(f"No ALB found with name: {alb_name}")
                return None

            alb = response["LoadBalancers"][0]

            alb_info = {
                "arn": alb["LoadBalancerArn"],
                "name": alb["LoadBalancerName"],
                "dns_name": alb["DNSName"],
                "zone_id": alb["CanonicalHostedZoneId"],
                "scheme": alb["Scheme"],
                "type": alb["Type"],
            }

            logger.info(f"Found ALB for muppet {muppet_name}: {alb_info['dns_name']}")
            return alb_info

        except ClientError as e:
            if e.response["Error"]["Code"] == "LoadBalancerNotFound":
                logger.warning(f"ALB not found for muppet: {muppet_name}")
                return None
            else:
                logger.error(f"Error discovering ALB for muppet {muppet_name}: {e}")
                raise
        except Exception as e:
            logger.error(
                f"Unexpected error discovering ALB for muppet {muppet_name}: {e}"
            )
            raise

    async def _add_https_listener(
        self, alb_info: Dict[str, Any], tls_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add HTTPS listener to existing ALB."""
        try:
            logger.info(f"Adding HTTPS listener to ALB: {alb_info['name']}")

            # First, get the existing target group
            target_groups = self.elbv2_client.describe_target_groups(
                LoadBalancerArn=alb_info["arn"]
            )

            if not target_groups.get("TargetGroups"):
                raise ValueError(f"No target groups found for ALB: {alb_info['name']}")

            target_group_arn = target_groups["TargetGroups"][0]["TargetGroupArn"]

            # Check if security group allows HTTPS traffic
            https_allowed = await self._check_https_security_group(alb_info)
            if not https_allowed:
                logger.info(
                    f"Adding HTTPS security group rule to ALB: {alb_info['name']}"
                )
                logger.info(
                    "Following zero-breaking-changes principle: automatically enhancing existing muppet"
                )
                await self._add_https_security_group_rule(alb_info)

            # Create HTTPS listener
            response = self.elbv2_client.create_listener(
                LoadBalancerArn=alb_info["arn"],
                Protocol="HTTPS",
                Port=443,
                SslPolicy=tls_config["ssl_policy"],
                Certificates=[{"CertificateArn": tls_config["certificate_arn"]}],
                DefaultActions=[
                    {"Type": "forward", "TargetGroupArn": target_group_arn}
                ],
            )

            listener_arn = response["Listeners"][0]["ListenerArn"]

            logger.info(f"HTTPS listener created successfully: {listener_arn}")

            return {
                "success": True,
                "arn": listener_arn,
                "protocol": "HTTPS",
                "port": 443,
                "security_group_updated": not https_allowed,
            }

        except ClientError as e:
            if e.response["Error"]["Code"] == "DuplicateListener":
                logger.info(
                    f"HTTPS listener already exists for ALB: {alb_info['name']}"
                )
                return {"success": True, "already_exists": True}
            else:
                logger.error(
                    f"Error creating HTTPS listener for ALB {alb_info['name']}: {e}"
                )
                raise
        except Exception as e:
            logger.error(
                f"Unexpected error creating HTTPS listener for ALB {alb_info['name']}: {e}"
            )
            raise

    async def _check_https_security_group(self, alb_info: Dict[str, Any]) -> bool:
        """Check if ALB security group allows HTTPS traffic on port 443."""
        try:
            # Get ALB security groups
            alb_details = self.elbv2_client.describe_load_balancers(
                LoadBalancerArns=[alb_info["arn"]]
            )

            security_groups = alb_details["LoadBalancers"][0]["SecurityGroups"]

            for sg_id in security_groups:
                # Check security group rules
                sg_details = self.ec2_client.describe_security_groups(GroupIds=[sg_id])

                for rule in sg_details["SecurityGroups"][0]["IpPermissions"]:
                    if (
                        rule.get("IpProtocol") == "tcp"
                        and rule.get("FromPort") == 443
                        and rule.get("ToPort") == 443
                    ):
                        return True

            return False

        except Exception as e:
            logger.warning(f"Failed to check HTTPS security group rules: {e}")
            return False

    async def _add_https_security_group_rule(self, alb_info: Dict[str, Any]) -> None:
        """Add HTTPS rule to security group for zero-breaking-changes enhancement."""
        try:
            logger.info(f"Adding HTTPS security group rule for ALB: {alb_info['name']}")
            logger.info(
                "Zero-breaking-changes: Automatically enhancing existing muppet with TLS"
            )

            # Get ALB security groups
            alb_details = self.elbv2_client.describe_load_balancers(
                LoadBalancerArns=[alb_info["arn"]]
            )

            security_groups = alb_details["LoadBalancers"][0]["SecurityGroups"]

            for sg_id in security_groups:
                try:
                    # Add HTTPS rule (port 443) if it doesn't exist
                    self.ec2_client.authorize_security_group_ingress(
                        GroupId=sg_id,
                        IpPermissions=[
                            {
                                "IpProtocol": "tcp",
                                "FromPort": 443,
                                "ToPort": 443,
                                "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                            }
                        ],
                    )
                    logger.info(f"Added HTTPS rule to security group: {sg_id}")

                except ClientError as e:
                    if e.response["Error"]["Code"] == "InvalidPermission.Duplicate":
                        logger.info(
                            f"HTTPS rule already exists in security group: {sg_id}"
                        )
                    else:
                        logger.warning(
                            f"Failed to add HTTPS rule to security group {sg_id}: {e}"
                        )

        except Exception as e:
            logger.warning(f"Failed to add HTTPS security group rule: {e}")
            # Don't fail the entire enhancement if security group update fails

    async def _create_dns_record(
        self, muppet_name: str, alb_info: Dict[str, Any], tls_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create DNS record pointing to the ALB."""
        try:
            domain_name = tls_config["domain_name"]
            zone_id = tls_config["zone_id"]

            logger.info(f"Creating DNS record: {domain_name} -> {alb_info['dns_name']}")

            # Create A record with alias to ALB
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=zone_id,
                ChangeBatch={
                    "Comment": f"Auto-generated DNS record for muppet: {muppet_name}",
                    "Changes": [
                        {
                            "Action": "UPSERT",
                            "ResourceRecordSet": {
                                "Name": domain_name,
                                "Type": "A",
                                "AliasTarget": {
                                    "DNSName": alb_info["dns_name"],
                                    "EvaluateTargetHealth": True,
                                    "HostedZoneId": alb_info["zone_id"],
                                },
                            },
                        }
                    ],
                },
            )

            change_id = response["ChangeInfo"]["Id"]

            logger.info(
                f"DNS record created successfully: {domain_name} (Change ID: {change_id})"
            )

            return {
                "success": True,
                "domain_name": domain_name,
                "change_id": change_id,
                "target": alb_info["dns_name"],
            }

        except ClientError as e:
            logger.error(f"Error creating DNS record for {domain_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating DNS record for {domain_name}: {e}")
            raise

    async def _configure_http_redirect(
        self, alb_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure HTTP→HTTPS redirect on existing HTTP listener."""
        try:
            logger.info(f"Configuring HTTP→HTTPS redirect for ALB: {alb_info['name']}")

            # Find existing HTTP listener
            listeners = self.elbv2_client.describe_listeners(
                LoadBalancerArn=alb_info["arn"]
            )

            http_listener = None
            for listener in listeners.get("Listeners", []):
                if listener["Protocol"] == "HTTP" and listener["Port"] == 80:
                    http_listener = listener
                    break

            if not http_listener:
                logger.warning(f"No HTTP listener found for ALB: {alb_info['name']}")
                return {"success": False, "reason": "No HTTP listener found"}

            # Modify HTTP listener to redirect to HTTPS
            self.elbv2_client.modify_listener(
                ListenerArn=http_listener["ListenerArn"],
                DefaultActions=[
                    {
                        "Type": "redirect",
                        "RedirectConfig": {
                            "Protocol": "HTTPS",
                            "Port": "443",
                            "StatusCode": "HTTP_301",
                        },
                    }
                ],
            )

            logger.info(
                f"HTTP→HTTPS redirect configured successfully for ALB: {alb_info['name']}"
            )

            return {
                "success": True,
                "listener_arn": http_listener["ListenerArn"],
                "redirect_type": "HTTP_301",
            }

        except ClientError as e:
            logger.error(
                f"Error configuring HTTP redirect for ALB {alb_info['name']}: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error configuring HTTP redirect for ALB {alb_info['name']}: {e}"
            )
            raise

    async def list_muppets_needing_tls_enhancement(self) -> List[Dict[str, Any]]:
        """List all muppets that could benefit from TLS enhancement."""
        try:
            logger.info("Discovering muppets that need TLS enhancement...")

            # Get all ALBs that look like muppet ALBs
            response = self.elbv2_client.describe_load_balancers()

            muppet_albs = []
            for alb in response.get("LoadBalancers", []):
                alb_name = alb["LoadBalancerName"]

                # Check if this looks like a muppet ALB (ends with -alb)
                if alb_name.endswith("-alb"):
                    muppet_name = alb_name[:-4]  # Remove "-alb" suffix

                    # Check if it already has HTTPS listener
                    listeners = self.elbv2_client.describe_listeners(
                        LoadBalancerArn=alb["LoadBalancerArn"]
                    )

                    has_https = any(
                        listener["Protocol"] == "HTTPS"
                        for listener in listeners.get("Listeners", [])
                    )

                    # Check terraform approach
                    terraform_approach = await self._detect_terraform_approach(alb)

                    muppet_albs.append(
                        {
                            "muppet_name": muppet_name,
                            "alb_name": alb_name,
                            "alb_dns": alb["DNSName"],
                            "has_https": has_https,
                            "needs_enhancement": not has_https,
                            "terraform_approach": terraform_approach,
                            "can_auto_enhance": terraform_approach == "new"
                            or has_https,
                        }
                    )

            logger.info(
                f"Found {len(muppet_albs)} potential muppets, {sum(1 for m in muppet_albs if m['needs_enhancement'])} need TLS enhancement"
            )

            return muppet_albs

        except Exception as e:
            logger.error(f"Error listing muppets needing TLS enhancement: {e}")
            raise

    async def _detect_terraform_approach(self, alb_info: Dict[str, Any]) -> str:
        """Detect whether a muppet uses the old or new terraform approach."""
        try:
            # Check if security group allows HTTPS traffic
            alb_details = self.elbv2_client.describe_load_balancers(
                LoadBalancerArns=[alb_info["LoadBalancerArn"]]
            )

            security_groups = alb_details["LoadBalancers"][0]["SecurityGroups"]

            for sg_id in security_groups:
                # Check security group rules
                sg_details = self.ec2_client.describe_security_groups(GroupIds=[sg_id])

                for rule in sg_details["SecurityGroups"][0]["IpPermissions"]:
                    if (
                        rule.get("IpProtocol") == "tcp"
                        and rule.get("FromPort") == 443
                        and rule.get("ToPort") == 443
                    ):
                        return "new"  # Has HTTPS security group rule

            return "old"  # No HTTPS security group rule

        except Exception as e:
            logger.warning(
                f"Failed to detect terraform approach for ALB {alb_info.get('LoadBalancerName', 'unknown')}: {e}"
            )
            return "unknown"

    async def enhance_all_muppets(self) -> Dict[str, Any]:
        """Enhance all discovered muppets with TLS."""
        try:
            logger.info("Starting bulk TLS enhancement for all muppets...")

            muppets = await self.list_muppets_needing_tls_enhancement()
            muppets_needing_enhancement = [m for m in muppets if m["needs_enhancement"]]

            if not muppets_needing_enhancement:
                logger.info("No muppets need TLS enhancement")
                return {
                    "success": True,
                    "message": "All muppets already have TLS configured",
                    "total_muppets": len(muppets),
                    "enhanced_count": 0,
                }

            results = []
            migration_required = []

            for muppet in muppets_needing_enhancement:
                logger.info(f"Enhancing muppet: {muppet['muppet_name']}")
                result = await self.enhance_muppet_with_tls(muppet["muppet_name"])
                results.append(result)

                # Track muppets that need terraform migration
                if result.get("migration_required"):
                    migration_required.append(
                        {
                            "muppet_name": muppet["muppet_name"],
                            "terraform_approach": result.get("terraform_approach"),
                            "migration_instructions": result.get(
                                "migration_instructions", []
                            ),
                        }
                    )

            successful_enhancements = sum(1 for r in results if r.get("success"))

            logger.info(
                f"Bulk TLS enhancement completed: {successful_enhancements}/{len(results)} successful"
            )

            return {
                "success": True,
                "total_muppets": len(muppets),
                "muppets_needing_enhancement": len(muppets_needing_enhancement),
                "enhanced_count": successful_enhancements,
                "failed_count": len(results) - successful_enhancements,
                "migration_required_count": len(migration_required),
                "results": results,
                "migration_required": migration_required,
                "summary": {
                    "auto_enhanced": successful_enhancements,
                    "require_migration": len(migration_required),
                    "migration_guidance": "Muppets requiring migration need to be updated to use the new terraform module approach",
                },
            }

        except Exception as e:
            logger.error(f"Error during bulk TLS enhancement: {e}")
            return {"success": False, "error": str(e)}
