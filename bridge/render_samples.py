"""Generate representative UI images without a calculator."""
from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from . import imagecodec
from .commands import Commands
from .render import RenderConfig, Renderer


SAMPLE = r"""# 二次方程

方程 $ax^2+bx+c=0$ 的解：

$$x=\frac{-b\pm\sqrt{b^2-4ac}}{2a}$$

- 若 $\Delta>0$：两个实根
- 若 $\Delta=0$：一个重根
- 若 $\Delta<0$：两个复根

```python
for k in range(3):
    print(k, k*k)
```

| 量 | 公式 |
|---|---|
| 面积 | $A=\pi r^2$ |
| 能量 | $E=mc^2$ |

English words wrap at spaces; 中文可在任意汉字之间换行。
"""

INPUT = r"Solve $\int_0^1 x^2\,dx$ and explain 判别式."


def _save(image: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def _screen(renderer: Renderer, blocks: list[Image.Image], path: Path,
            title: str = "Nspire AI   chat 3   thinking: high") -> None:
    cfg = renderer.config
    canvas = Image.new("L", (cfg.width, cfg.screen_height), 255)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, cfg.width - 1, cfg.title_height - 1), fill=28)
    draw.text((5, 2), title, fill=255, font=renderer._font(cfg.ui_font_size, False))
    y = cfg.title_height + 2
    content_bottom = cfg.screen_height - cfg.input_height
    total = sum(im.height + cfg.block_gap for im in blocks)
    source_y = max(0, total - (content_bottom - y))
    cursor = 0
    for block in blocks:
        extent = block.height + cfg.block_gap
        if cursor + extent <= source_y:
            cursor += extent
            continue
        crop_top = max(0, source_y - cursor)
        visible = min(block.height - crop_top, content_bottom - y)
        if visible > 0:
            canvas.paste(block.crop((0, crop_top, cfg.width, crop_top + visible)), (0, y))
            y += visible + cfg.block_gap
        cursor += extent
        if y >= content_bottom:
            break
    renderer.draw_input_line(canvas, r"Next: $\sum_{k=1}^n k$", cursor=15)
    _save(canvas, path)


def main(output: str = "artifacts/render-samples") -> None:
    out = Path(output)
    renderer = Renderer()
    _save(renderer.render_markdown(SAMPLE), out / "mixed.png")
    _save(renderer.render_user_turn(INPUT), out / "user.png")
    _save(renderer.render_info(INFO), out / "info.png")
    _save(renderer.render_typing_preview(r"\frac{-b\pm\sqrt{b^2-4ac}}{2a}"), out / "preview.png")

    commands = Commands()
    _save(renderer.render_menu(commands, "root"), out / "menu-root.png")
    _save(renderer.render_menu(commands, "math"), out / "menu-math.png")
    candidates = ["中国", "中文", "中", "忠", "钟", "种", "重", "众", "终", "中学", "中心"]
    _save(renderer.render_candidate_bar("zhong", candidates, 0), out / "candidates.png")
    _save(renderer.render_legend("qwerty"), out / "legend.png")
    _save(renderer.render_sessions([
        ("1", "Quadratic equations"), ("3", "中文输入法测试"),
        ("5", "A title that is deliberately much too long for one row"),
    ], "3"), out / "sessions.png")

    user = renderer.render_user_turn(INPUT)
    answer = renderer.render_markdown(SAMPLE)
    info = renderer.render_info(INFO)
    _screen(renderer, [user, answer, info], out / "screen.png")

    print(f"wrote {out}")


INFO = "Session 3 · openrouter/free · thinking: high · 已切换到新会话"


if __name__ == "__main__":
    main(os.environ.get("NSPIREAI_SAMPLE_DIR", "artifacts/render-samples"))
