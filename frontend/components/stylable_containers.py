from streamlit_extras.stylable_container import stylable_container


_div_chart = """
    button div:before {
        display: inline-block;
        margin-top: 1px;
        margin-right: 5px;
        font-family: 'Material Symbols Outlined';
        font-size: 20px;
        content: 'bar_chart';
        color: #9c9d9f;
    }
"""

_div_code = """
    button div:before {
        display: inline-block;
        margin-top: 1px;
        margin-right: 5px;
        font-family: 'Material Symbols Outlined';
        font-size: 20px;
        content: 'code';
        color: #9c9d9f;
    }
"""

_hover = """
    button div:hover:before {
        color: #ffffff;
    }
"""

_button = """
    button {
        width: 0;
        height: 0;
        border: none;
        background-color: #0e1117;
    }
"""

def chart_button_container():
    return stylable_container(
        key="chart_button_container",
        css_styles=[_div_chart, _hover, _button]
    )

def code_button_container():
    return stylable_container(
        key="code_button_container",
        css_styles=[_div_code, _hover, _button]
    )
