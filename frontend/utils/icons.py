from importlib.resources import files

import frontend


_assistant_avatar = str(
    files(frontend)
    .joinpath("images")
    .joinpath("logo_bd.svg")
)

AVATARS = {
    "user": "https://api.dicebear.com/9.x/avataaars-neutral/svg?backgroundColor=7ec876&eyebrows=default&eyes=default&mouth=twinkle",
    "assistant": _assistant_avatar
}
