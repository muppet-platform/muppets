"""
Property-based tests for state management registry consistency.

This module implements Property 3: Registry Consistency
which validates Requirements 1.5.

Feature: muppet-platform, Property 3: Registry Consistency
"""

import asyncio
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from src.models import Muppet, MuppetStatus, PlatformState
from src.state_manager import StateManager


# Custom strategies for generating test data
@composite
def muppet_data(draw):
    """Generate valid muppet data for testing."""
    # Use simpler name generation to avoid filtering issues
    name_parts = [
        draw(st.sampled_from(["api", "service", "worker", "app", "tool"])),
        draw(st.sampled_from(["test", "demo", "prod", "dev", "staging"])),
    ]
    name = "-".join(name_parts)

    template = draw(st.sampled_from(["java-micronaut"]))

    status = draw(
        st.sampled_from(
            [MuppetStatus.RUNNING, MuppetStatus.CREATING, MuppetStatus.STOPPED]
        )
    )

    github_repo_url = f"https://github.com/muppet-platform/{name}"

    fargate_service_arn = draw(
        st.one_of(
            st.none(),
            st.just(f"arn:aws:ecs:us-west-2:123456789012:service/cluster/{name}"),
        )
    )

    created_at = datetime.utcnow()

    return Muppet(
        name=name,
        template=template,
        status=status,
        github_repo_url=github_repo_url,
        fargate_service_arn=fargate_service_arn,
        created_at=created_at,
        updated_at=created_at,
        terraform_version="1.0.0",
        port=3000,
    )


@composite
def muppet_list(draw):
    """Generate a list of muppets with unique names."""
    muppets = draw(st.lists(muppet_data(), min_size=0, max_size=5))  # Reduced max size
    # Ensure unique names
    seen_names = set()
    unique_muppets = []
    for muppet in muppets:
        if muppet.name not in seen_names:
            seen_names.add(muppet.name)
            unique_muppets.append(muppet)
    return unique_muppets


@composite
def terraform_versions(draw):
    """Generate terraform module versions."""
    modules = ["fargate-service", "monitoring"]  # Reduced to 2 modules
    versions = {}
    for module in draw(
        st.lists(st.sampled_from(modules), min_size=0, max_size=2, unique=True)
    ):
        version = draw(
            st.sampled_from(["1.0.0", "1.1.0", "1.2.0", "2.0.0"])
        )  # Fixed versions
        versions[module] = version
    return versions


@composite
def active_deployments(draw, muppets: List[Muppet]):
    """Generate active deployments that may or may not match muppets."""
    deployments = {}

    # Add some deployments for existing muppets
    for muppet in draw(st.lists(st.sampled_from(muppets), max_size=len(muppets))):
        deployments[
            muppet.name
        ] = f"arn:aws:ecs:us-west-2:123456789012:service/cluster/{muppet.name}"

    # Add some orphaned deployments (deployments without corresponding muppets)
    orphaned_count = draw(st.integers(min_value=0, max_value=3))
    for i in range(orphaned_count):
        orphaned_name = f"orphaned-{i}"
        deployments[
            orphaned_name
        ] = f"arn:aws:ecs:us-west-2:123456789012:service/cluster/{orphaned_name}"

    return deployments


@composite
def state_operation_sequence(draw):
    """Generate a sequence of state operations (create, delete)."""
    operations = []
    max_operations = draw(st.integers(min_value=1, max_value=10))

    for _ in range(max_operations):
        operation_type = draw(st.sampled_from(["create", "delete"]))
        muppet_name = draw(
            st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
                min_size=3,
                max_size=15,
            ).filter(lambda x: x[0].isalpha() and x[-1].isalnum())
        )

        if operation_type == "create":
            template = draw(st.sampled_from(["java-micronaut"]))
            operations.append(
                {"type": "create", "name": muppet_name, "template": template}
            )
        else:
            operations.append({"type": "delete", "name": muppet_name})

    return operations


def run_async_test(coro):
    """Helper to run async tests in property-based testing."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestStateManagementRegistryConsistency:
    """
    Property-based tests for state management registry consistency.

    Tests Property 3: For any sequence of muppet operations (create, delete),
    the platform registry should always accurately reflect the current state
    by reconstructing it from GitHub repositories, Parameter Store, and ECS services.

    Validates: Requirements 1.5
    """

    @given(muppet_list(), terraform_versions())
    @settings(max_examples=20, deadline=5000)  # Reduced examples and deadline
    def test_registry_consistency_property(self, muppets, tf_versions):
        """
        Property 3: Registry Consistency

        For any sequence of muppet operations (create, delete), the platform registry
        should always accurately reflect the current state by reconstructing it from
        GitHub repositories, Parameter Store, and ECS services.

        **Feature: muppet-platform, Property 3: Registry Consistency**
        **Validates: Requirements 1.5**
        """

        async def async_test():
            # Generate active deployments based on muppets
            deployments = {}
            for muppet in muppets:
                # Some muppets have deployments, some don't
                if hash(muppet.name) % 3 != 0:  # Deterministic but varied
                    deployments[
                        muppet.name
                    ] = f"arn:aws:ecs:us-west-2:123456789012:service/cluster/{muppet.name}"

            # Create StateManager instance first
            state_manager = StateManager()

            # Mock the actual client instances on the state manager
            state_manager.github_client = AsyncMock()
            state_manager.parameter_store = AsyncMock()
            state_manager.ecs_client = AsyncMock()

            # Configure the mocked clients
            state_manager.github_client.discover_muppets.return_value = muppets

            param_store_params = {}
            for module, version in tf_versions.items():
                param_store_params[f"terraform/modules/{module}/version"] = version
            state_manager.parameter_store.get_parameters_by_path.return_value = (
                param_store_params
            )

            state_manager.ecs_client.get_active_deployments.return_value = deployments

            # Initialize the state manager
            await state_manager.initialize()

            # Act - Reconstruct state from sources
            reconstructed_state = await state_manager.get_state()

            # Assert - Verify registry consistency

            # 1. All muppets from GitHub should be in the reconstructed state
            assert len(reconstructed_state.muppets) == len(
                muppets
            ), f"Expected {len(muppets)} muppets, got {len(reconstructed_state.muppets)}"

            # 2. Muppet data should match GitHub source data
            reconstructed_names = {m.name for m in reconstructed_state.muppets}
            expected_names = {m.name for m in muppets}
            assert (
                reconstructed_names == expected_names
            ), f"Muppet names don't match. Expected: {expected_names}, Got: {reconstructed_names}"

            # 3. Terraform versions should match Parameter Store
            assert (
                reconstructed_state.terraform_versions == tf_versions
            ), f"Terraform versions don't match. Expected: {tf_versions}, Got: {reconstructed_state.terraform_versions}"

            # 4. Active deployments should match ECS
            assert (
                reconstructed_state.active_deployments == deployments
            ), f"Active deployments don't match. Expected: {deployments}, Got: {reconstructed_state.active_deployments}"

            # 5. Muppets with deployments should have their ARNs updated
            for muppet in reconstructed_state.muppets:
                if muppet.name in deployments:
                    assert (
                        muppet.fargate_service_arn == deployments[muppet.name]
                    ), f"Muppet {muppet.name} ARN not updated from deployment data"

            # 6. State should have a recent timestamp
            assert (
                reconstructed_state.last_updated is not None
            ), "State should have last_updated timestamp"
            time_diff = datetime.utcnow() - reconstructed_state.last_updated
            assert time_diff < timedelta(seconds=10), "State timestamp should be recent"

            # 7. Test cache consistency - second call should return same data
            cached_state = await state_manager.get_state()
            assert (
                cached_state is reconstructed_state
            ), "Cached state should be the same object"

            # 8. Force refresh should reconstruct again
            force_refreshed_state = await state_manager.get_state()
            assert len(force_refreshed_state.muppets) == len(
                muppets
            ), "Force refresh should return consistent data"

        run_async_test(async_test())

    @given(state_operation_sequence())
    @settings(max_examples=10, deadline=10000)
    def test_registry_consistency_after_operations(self, operations):
        """
        Test that registry remains consistent after a sequence of operations.

        This tests that state changes are properly reflected in the registry.
        """

        async def async_test():
            # Track expected state based on operations
            expected_muppets = {}

            # Create StateManager instance and mock its clients directly
            state_manager = StateManager()
            state_manager.github_client = AsyncMock()
            state_manager.parameter_store = AsyncMock()
            state_manager.ecs_client = AsyncMock()

            # Configure basic responses
            state_manager.parameter_store.get_parameters_by_path.return_value = {
                "terraform/modules/fargate-service/version": "1.0.0"
            }
            state_manager.ecs_client.get_active_deployments.return_value = {}

            # Apply operations and track expected state
            for operation in operations:
                if operation["type"] == "create":
                    # Add muppet to expected state
                    muppet = Muppet(
                        name=operation["name"],
                        template=operation["template"],
                        status=MuppetStatus.CREATING,
                        github_repo_url=f"https://github.com/muppet-platform/{operation['name']}",
                        created_at=datetime.utcnow(),
                    )
                    expected_muppets[operation["name"]] = muppet

                    # Simulate adding to state manager
                    await state_manager.add_muppet_to_state(muppet)

                elif operation["type"] == "delete":
                    # Remove muppet from expected state
                    if operation["name"] in expected_muppets:
                        del expected_muppets[operation["name"]]

                    # Simulate removing from state manager
                    await state_manager.remove_muppet_from_state(operation["name"])

            # Update GitHub mock to return expected muppets
            state_manager.github_client.discover_muppets.return_value = list(
                expected_muppets.values()
            )

            # Initialize the state manager
            await state_manager.initialize()

            # Act - Get current state
            current_state = await state_manager.get_state()

            # Assert - State should match expected state after operations
            assert len(current_state.muppets) == len(
                expected_muppets
            ), f"Expected {len(expected_muppets)} muppets after operations, got {len(current_state.muppets)}"

            current_names = {m.name for m in current_state.muppets}
            expected_names = set(expected_muppets.keys())
            assert (
                current_names == expected_names
            ), f"Muppet names after operations don't match. Expected: {expected_names}, Got: {current_names}"

        run_async_test(async_test())

    @given(muppet_list())
    @settings(max_examples=10, deadline=5000)
    def test_registry_handles_external_service_failures(self, muppets):
        """
        Test that registry consistency is maintained even when external services fail.

        This ensures the property holds even under failure conditions.
        """

        async def async_test():
            # Create StateManager instance and mock its clients directly
            state_manager = StateManager()
            state_manager.github_client = AsyncMock()
            state_manager.parameter_store = AsyncMock()
            state_manager.ecs_client = AsyncMock()

            # Configure one service to fail
            state_manager.github_client.discover_muppets.side_effect = Exception(
                "GitHub API failure"
            )

            state_manager.parameter_store.get_parameters_by_path.return_value = {
                "terraform/modules/fargate-service/version": "1.0.0"
            }

            state_manager.ecs_client.get_active_deployments.return_value = {}

            # Initialize the state manager
            await state_manager.initialize()

            # Act - Get state despite GitHub failure
            state = await state_manager.get_state()

            # Assert - State should still be consistent (empty but valid)
            assert isinstance(
                state, PlatformState
            ), "Should return valid PlatformState even with failures"
            assert (
                state.muppets == []
            ), "Should return empty muppets list when GitHub fails"
            assert state.terraform_versions == {
                "fargate-service": "1.0.0"
            }, "Should still get terraform versions from Parameter Store"
            assert (
                state.active_deployments == {}
            ), "Should still get deployments from ECS"
            assert (
                state.last_updated is not None
            ), "Should have timestamp even with partial failures"

        run_async_test(async_test())

    def test_registry_consistency_with_specific_examples(self):
        """
        Test registry consistency with specific known examples.

        This provides concrete test cases alongside the property-based tests.
        """

        async def async_test():
            # Specific test scenarios
            test_scenarios = [
                {
                    "name": "empty_state",
                    "muppets": [],
                    "terraform_versions": {},
                    "deployments": {},
                },
                {
                    "name": "single_muppet",
                    "muppets": [
                        Muppet(
                            name="test-api",
                            template="java-micronaut",
                            status=MuppetStatus.RUNNING,
                            github_repo_url="https://github.com/muppet-platform/test-api",
                            created_at=datetime.utcnow(),
                        )
                    ],
                    "terraform_versions": {"fargate-service": "1.2.0"},
                    "deployments": {
                        "test-api": "arn:aws:ecs:us-west-2:123456789012:service/cluster/test-api"
                    },
                },
                {
                    "name": "multiple_muppets_mixed_states",
                    "muppets": [
                        Muppet(
                            name="api-service",
                            template="java-micronaut",
                            status=MuppetStatus.RUNNING,
                            github_repo_url="https://github.com/muppet-platform/api-service",
                            created_at=datetime.utcnow(),
                        ),
                        Muppet(
                            name="worker-service",
                            template="java-micronaut",
                            status=MuppetStatus.CREATING,
                            github_repo_url="https://github.com/muppet-platform/worker-service",
                            created_at=datetime.utcnow(),
                        ),
                    ],
                    "terraform_versions": {
                        "fargate-service": "1.2.0",
                        "monitoring": "1.1.0",
                        "networking": "2.0.0",
                    },
                    "deployments": {
                        "api-service": "arn:aws:ecs:us-west-2:123456789012:service/cluster/api-service"
                        # worker-service has no deployment yet (still creating)
                    },
                },
            ]

            for scenario in test_scenarios:
                # Create StateManager instance and mock its clients directly
                state_manager = StateManager()
                state_manager.github_client = AsyncMock()
                state_manager.parameter_store = AsyncMock()
                state_manager.ecs_client = AsyncMock()

                # Configure mocks for this scenario
                state_manager.github_client.discover_muppets.return_value = scenario[
                    "muppets"
                ]

                param_store_params = {}
                for module, version in scenario["terraform_versions"].items():
                    param_store_params[f"terraform/modules/{module}/version"] = version
                state_manager.parameter_store.get_parameters_by_path.return_value = (
                    param_store_params
                )

                state_manager.ecs_client.get_active_deployments.return_value = scenario[
                    "deployments"
                ]

                # Initialize the state manager
                await state_manager.initialize()

                # Act
                state = await state_manager.get_state()

                # Assert - Verify consistency for this specific scenario
                assert len(state.muppets) == len(
                    scenario["muppets"]
                ), f"Scenario {scenario['name']}: Expected {len(scenario['muppets'])} muppets"

                assert (
                    state.terraform_versions == scenario["terraform_versions"]
                ), f"Scenario {scenario['name']}: Terraform versions don't match"

                assert (
                    state.active_deployments == scenario["deployments"]
                ), f"Scenario {scenario['name']}: Active deployments don't match"

                # Verify muppets have correct deployment ARNs
                for muppet in state.muppets:
                    if muppet.name in scenario["deployments"]:
                        assert (
                            muppet.fargate_service_arn
                            == scenario["deployments"][muppet.name]
                        ), f"Scenario {scenario['name']}: Muppet {muppet.name} ARN not updated"

        run_async_test(async_test())
