import unittest

from autofix_trix_review import clean_type


class CleanType(unittest.TestCase):
    def test_cases(self) -> None:
        for raw, want in [
            ("BR 185 im Design für den Film", "BR 185"),
            ("Kleinlokomotive Bauart Köf II, zugelassen bei der Deutschen Bundesbahn (DB)", "Köf II"),
            ("Kleinlokomotive Bauart Köf II.", "Köf II"),
            ("Nassdampflokomotive Gattung D XI", "D XI"),
            ("Dampftriebwagen Bauart Kittel CidT", "Kittel CidT"),
            ("BR EP 3/6", "EP 3/6"),
            ("BR SVT 04", "SVT 04"),
            ("BR Köf II", "Köf II"),
            ("Reihe RAm TEE I 501", "RAm TEE I 501"),
            ("Serie RAe TEE II", "RAe TEE II"),
            ("Reihe DE 1001 bis 1003", "DE 1001-1003"),
            ("Bauart G", "G"),
            ("Reihe 2016", "Reihe 2016"),
            ("Serie 1200", "Serie 1200"),
            ("Serie 5600 (ex Baureihe 52)", "Serie 5600"),
            ("BR 094 (frühere BR 94.5-17)", "BR 094"),
            ("BR ET 91", "ET 91"),
            ("Reihe Dm3", "Dm3"),
            ("BR 185", "BR 185"),
            ("BR E 41", "BR E 41"),
        ]:
            self.assertEqual(clean_type(raw), want, raw)


if __name__ == "__main__":
    unittest.main()
