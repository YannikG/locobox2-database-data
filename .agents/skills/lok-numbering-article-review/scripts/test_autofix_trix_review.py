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
            ("Be 6/8III", "Be 6/8 III"),
            ("BR VT 08.5", "VT 08.5"),
            ("BR ICM-1", "ICM-1"),
            ("Re 4/4 II (Serie 420)", "Re 4/4 II"),
            ("Type GG-1", "GG-1"),
            ("BR F 140 AC 2", "F 140 AC 2"),
            ("BR 58.10-21 (ehemalige preussische G 12)", "BR 58.10-21"),
            ("preussische G 12", "G 12"),
            ("Gt 2 x 4/4 (spätere Baureihe 96)", "Gt 2x4/4"),
            ("Schienenbus VT 95.9 mit Einachs-Anhänger VB 141.2", "VT 95.9"),
            ("Schienenbus VT 98", "VT 98"),
            ("Dieseltriebzug RAm TEE", "RAm TEE"),
            ("Turmtriebwagen TVT", "TVT"),
            ("BR E10.3", "BR E 10.3"),
            ("BR EB 3200", "EB 3200"),
            ("BR 185", "BR 185"),
            ("BR E 41", "BR E 41"),
        ]:
            self.assertEqual(clean_type(raw), want, raw)


if __name__ == "__main__":
    unittest.main()
