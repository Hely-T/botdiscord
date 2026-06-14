import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from cogs.bot.voice_cog import AudioItem, BotVoiceCog, GuildAudioState
from services.music_player_service import MusicPlayerService


class MusicPlayerPreferencesTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_dir = self.temp_dir.name
        patcher = patch("utils.DATABASE_DIR", database_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.service = MusicPlayerService()

    def tearDown(self):
        self.service.db.close()
        self.temp_dir.cleanup()

    def test_preferences_are_saved_per_user(self):
        self.service.set_user_preferences(
            123,
            volume=100,
        )

        first = self.service.get_user_preferences(123)
        second = self.service.get_user_preferences(456)

        self.assertEqual(first["volume"], 100)
        self.assertEqual(second["volume"], 65)
        self.assertNotIn("autoplay", first)
        self.assertNotIn("loop_current", first)

    def test_volume_is_limited_to_supported_range(self):
        self.assertEqual(
            self.service.set_user_preferences(123, volume=999)["volume"],
            200,
        )
        self.assertEqual(
            self.service.set_user_preferences(123, volume=-5)["volume"],
            0,
        )


class MusicPlayerAutoplayTest(unittest.IsolatedAsyncioTestCase):
    async def test_autoplay_uses_first_unseen_youtube_radio_item(self):
        previous = AudioItem(
            title="Bài hiện tại",
            query="https://www.youtube.com/watch?v=current",
            webpage_url="https://www.youtube.com/watch?v=current",
            video_id="current",
            requester_id=123,
            requester_name="Tester",
        )
        duplicate = AudioItem(
            title="Bài hiện tại",
            query=previous.query,
            webpage_url=previous.webpage_url,
            video_id="current",
            requester_id=123,
            requester_name="Tester",
        )
        recommended = AudioItem(
            title="YouTube đề xuất",
            query="https://www.youtube.com/watch?v=next",
            webpage_url="https://www.youtube.com/watch?v=next",
            video_id="next",
            requester_id=123,
            requester_name="Tester",
        )

        cog = BotVoiceCog.__new__(BotVoiceCog)
        cog.bot = MagicMock()
        cog.bot.get_user.return_value = SimpleNamespace(id=123, display_name="Tester")
        cog.states = {
            777: GuildAudioState(current=previous, autoplay=True),
        }
        cog._extract_music_items = AsyncMock(return_value=[duplicate, recommended])

        added = await cog._enqueue_autoplay(777)

        self.assertTrue(added)
        self.assertEqual(cog.states[777].queue, [recommended])
        query = cog._extract_music_items.await_args.args[0]
        self.assertIn("list=RDcurrent", query)


if __name__ == "__main__":
    unittest.main()
