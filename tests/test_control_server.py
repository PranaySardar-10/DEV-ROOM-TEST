import unittest

from devroom.control_server import main


class ControlServerTests(unittest.TestCase):
    def test_control_server_module_exposes_main(self) -> None:
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
