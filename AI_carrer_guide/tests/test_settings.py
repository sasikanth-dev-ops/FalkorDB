import unittest

from pydantic import ValidationError

from backend.config.env import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_accept_valid_graph_connection_values(self) -> None:
        settings = Settings(
            falkordb_host="graph.local",
            falkordb_port=6380,
            falkordb_graph_name="career_test",
        )

        self.assertEqual(settings.falkordb_host, "graph.local")
        self.assertEqual(settings.falkordb_port, 6380)
        self.assertEqual(settings.falkordb_graph_name, "career_test")

    def test_settings_reject_invalid_graph_port(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(falkordb_port=70000)


if __name__ == "__main__":
    unittest.main()
