import streamlit as st


_typewriter_style = """
    <link href="https://fonts.googleapis.com/css2?family=Source+Sans+Pro" rel="stylesheet"/>
    <style>
        /* Keyframes for animations */
        @keyframes typing {
            from { max-width: 0; }
            to { max-width: 100%; }
        }

        @keyframes blink-caret {
            from, to { border-color: transparent; }
            50% { border-color: #31333f; }
        }

        @keyframes disappear {
            0% { border-color: #31333f; }
            100% { border-color: transparent; }
        }

        /* Main typewriter container styling */
        .typewriter {
            display: inline-block;
            font-family: "Source Sans Pro", sans-serif;
            white-space: nowrap; /* Keeps the content on a single line */
            overflow: hidden; /* Ensures the content is not revealed until the animation */
            padding-right: 0.1em; /* Adds space between the text and the cursor */
            margin: 0 auto; /* Centering effect */
            border-right: 0.125em solid #31333f; /* The typewriter cursor */
            animation:
                typing 1s steps(80, end),
                blink-caret 0.75s step-end infinite,
                disappear 0s 0.75s forwards; /* Hides cursor after typing */
        }

        /* Styling for the text within the typewriter container */
        .typewriter h3 {
            display: inline;
            font-family: "Source Sans Pro", sans-serif;
            font-size: 1.5em;
            line-height: 1.25em;
            margin: 0;
        }
    </style>
"""

_typewriter_text = """
    <div class="typewriter">
        <h3>{text}</h3>
    </div>
"""

def typewrite(text: str):
    return st.html(
        _typewriter_style +
        _typewriter_text.format(text=text)
    )
