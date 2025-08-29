from importlib.resources import files

import frontend

BD_LOGO = str(
    files(frontend)
    .joinpath("images")
    .joinpath("logo_bd.svg")
)
