import streamlit.components.v1 as components


_card_style = """
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined&family=Source+Sans+Pro" rel="stylesheet"/>
    <style>
        body {
            margin: 0;
        }

        .card {
            margin: 14px 0px;
            padding: 15px;
            border: 1px solid #262730;
            font-family: "Source Sans Pro", sans-serif;
            line-height: 1.5;
            background-color: #0e1117;
            border-radius: 15px;
            transition: background-color 0.3s ease;
            cursor: default;
        }

        .card:hover {
            background-color: #1a1c23;
        }

        .card:hover .copy-icon {
            opacity: 1;
        }

        .icon {
            color: #9398a7;
        }

        .copy-icon {
            position: absolute;
            top: 24px;
            right: 12px;
            font-size: 18px;
            color: #ffffff;
            opacity: 0;
            transform: scale(1);
            transition: opacity 0.3s ease, transform 0.3s ease;
            cursor: pointer;
        }

        .text {
            font-size: 16px;
            color: #9398a7;
        }
    </style>
"""

_card_functions = """
    <script>
        function copyToClipboard(iconElement, textContent) {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(textContent).then(() => {
                    triggerCopyIconTransition(iconElement);
                });
            } else {
                let tempText = document.createElement("input");
                tempText.value = textContent;
                document.body.appendChild(tempText);
                tempText.select();
                document.execCommand("copy");
                document.body.removeChild(tempText);
                triggerCopyIconTransition(iconElement);
            }
        }

        function triggerCopyIconTransition(iconElement){
            iconElement.style.transform = "scale(1.2)";
            iconElement.innerHTML = "check";
            setTimeout(() => {
                iconElement.style.transform = "scale(1)";
            }, 300);
            setTimeout(() => {
                iconElement.innerHTML = "content_copy";
            }, 1700);
        }

        function resetCopyIcon(cardElement) {
            iconElement = cardElement.querySelector(".copy-icon");
            setTimeout(() => {
                iconElement.innerHTML = "content_copy";
            }, 300);
        }
    </script>
"""

_card = """
    <div class="card" onmouseleave="resetCopyIcon(this)">
        <span class="material-symbols-outlined icon">
            {icon}
        </span>
        <div class="text">
            {text}
        </div>
        <span class="material-symbols-outlined copy-icon" onclick="copyToClipboard(this, '{text}')">
            content_copy
        </span>
    </div>
"""

def render_card(icon: str, text: str):
    components.html(
        _card_style +
        _card_functions +
        _card.format(icon=icon, text=text),
        height=175,
    )
