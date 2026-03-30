# EC800MCNLE UI Emoji Assets

These PNG assets are the board-local emoji set used by:

- `boards/ec800mcnle-audio-board/code/board_ui.py`
- primary device target path `U:/media`
- runtime fallback path `/usr/media`
- runtime tool `qpy.ui.emotion.show`

Runtime fallback:

- prefer configured `media_prefix`
- fall back to `/usr/media`
- keep `U:/media` compatibility when present

Source:

- `C:\Users\kingd\Desktop\code\lcc-ai-team\embed\opensource\AIChatbot-Xiaozhi-Mqtt\src(UI)\media`

Deployment:

```powershell
python C:\Users\kingd\Desktop\code\lcc-ai-team\embed\project\qpyclaw\tools\host\qpy_board_media_sync.py --profile ec800mcnle-audio-board --port COM19 --json
```

Available emoji files:

- `angry.png`
- `confident.png`
- `confused.png`
- `cool.png`
- `crying.png`
- `delicious.png`
- `embarrassed.png`
- `funny.png`
- `happy.png`
- `kissy.png`
- `laughing.png`
- `loving.png`
- `neutral.png`
- `relaxed.png`
- `sad.png`
- `shocked.png`
- `sleepy.png`
- `surprised.png`
- `thinking.png`
- `winking.png`
