import unittest

from devroom.config import DevRoomConfig, validate_config
from devroom.provider_factory import ProviderSpec
from devroom.provider_router import RoleBinding


class ConfigValidationTests(unittest.TestCase):
    def _valid(self):
        worker = ProviderSpec("worker", "fake")
        bindings = {
            role: RoleBinding(
                "worker",
                f"{role} instructions",
                "workspace-write" if role == "Implementer" else "read-only",
            )
            for role in ("Lead", "Architect", "Coder", "Implementer", "QA")
        }
        return DevRoomConfig((worker,), bindings)

    def test_rejects_unknown_provider_reference(self) -> None:
        config = self._valid()
        bindings = dict(config.bindings)
        bindings["Coder"] = RoleBinding("missing", "Code.")
        config = DevRoomConfig(config.providers, bindings)
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_rejects_invalid_sandbox(self) -> None:
        config = self._valid()
        bindings = dict(config.bindings)
        bindings["Coder"] = RoleBinding("worker", "Code.", "dangerous")
        config = DevRoomConfig(config.providers, bindings)
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_rejects_missing_production_role(self) -> None:
        config = DevRoomConfig(
            (ProviderSpec("worker", "fake"),),
            {"Lead": RoleBinding("worker", "Coordinate.")},
        )
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_rejects_writable_non_implementer(self) -> None:
        config = self._valid()
        bindings = dict(config.bindings)
        bindings["Coder"] = RoleBinding("worker", "Code.", "workspace-write")
        config = DevRoomConfig(config.providers, bindings)
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_rejects_read_only_implementer(self) -> None:
        config = self._valid()
        bindings = dict(config.bindings)
        bindings["Implementer"] = RoleBinding("worker", "Implement.", "read-only")
        config = DevRoomConfig(config.providers, bindings)
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_accepts_valid_configuration(self) -> None:
        validate_config(self._valid())


if __name__ == "__main__":
    unittest.main()
