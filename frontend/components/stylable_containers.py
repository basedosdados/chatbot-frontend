from streamlit_extras.stylable_container import stylable_container

_div_chart = """
    button div:before {
        display: inline-block;
        margin-top: 1px;
        margin-right: 5px;
        font-family: 'Material Symbols Outlined';
        font-size: 20px;
        content: 'bar_chart';
        color: #7c7f84;
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
        color: #7c7f84;
    }
"""

_hover = """
    button div:hover:before {
        color: #252a32;
    }
"""

_button = """
    button {
        width: 0;
        height: 0;
        border: none;
        background-color: #ffffff;
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
