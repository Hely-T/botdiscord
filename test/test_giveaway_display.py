import unittest

from cogs.administrator.giveaway_cog import AdministratorGiveawayCog


class GiveawayDisplayTest(unittest.TestCase):
    def test_custom_label_markdown_is_removed_before_default_bold(self):
        self.assertEqual(
            AdministratorGiveawayCog._clean_theme_label("**Tổ chức bởi:**"),
            "Tổ chức bởi",
        )
        self.assertEqual(
            AdministratorGiveawayCog._clean_theme_label("Người thắng:"),
            "Người thắng",
        )

    def test_end_delay_uses_absolute_timestamp(self):
        giveaway = {"ends_at": 103.0}

        self.assertEqual(
            AdministratorGiveawayCog._giveaway_delay_seconds(giveaway, now=100.5),
            2.5,
        )
        self.assertEqual(
            AdministratorGiveawayCog._giveaway_delay_seconds(giveaway, now=105),
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
