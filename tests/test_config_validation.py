import unittest

from devroom.config import DevRoomConfig, validate_config
from devroom.provider_factory import ProviderSpec
from devroom.provider_router import RoleBinding


class ConfigValidationTests(unittest.TestCase):
    def test_rejects_unknown_provider_reference(self) -> None:
        config = DevRoomConfig(
            (ProviderSpec("worker", "fake"),),
            {"Lead": RoleBinding("missing", "Coordinate.")},
        )
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_rejects_invalid_sandbox(self) -> None:
        config = DevRoomConfig(
            (ProviderSpec("worker", "fake"),),
            {"Lead": RoleBinding("worker", "Coordinate.", "dangerous")},
        )
        with self.assertRaises(ValueError):
            validate_config(config)

    def test_accepts_valid_configuration(self) -> None:
        config = DevRoomConfig(
            (ProviderSpec("worker", "fake"),),
            {"Lead": RoleBinding("worker", "Coordinate.")},
        )
        validate_config(config)


if __name__ == "__main__":
    unittest.main()
