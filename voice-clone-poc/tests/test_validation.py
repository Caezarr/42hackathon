import unittest

from voice_clone_poc.validation import (
    InputError,
    WavMetadata,
    require_consent,
    validate_metadata,
    validate_text,
)


class ValidationTests(unittest.TestCase):
    def test_accepts_clean_thirty_second_reference(self):
        validate_metadata(WavMetadata(duration_seconds=30, channels=1, sample_rate=48_000))

    def test_rejects_short_reference(self):
        with self.assertRaises(InputError):
            validate_metadata(WavMetadata(duration_seconds=4, channels=1, sample_rate=48_000))

    def test_normalizes_text(self):
        self.assertEqual(validate_text("  Bonjour,   tout le monde.  "), "Bonjour, tout le monde.")

    def test_requires_voice_consent(self):
        with self.assertRaises(InputError):
            require_consent(False)


if __name__ == "__main__":
    unittest.main()
