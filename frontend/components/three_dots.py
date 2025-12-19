import streamlit as st

_three_waving_dots_animation = """
    <style>
        .progress {
            margin-top: -4px;
            width: 28px;
        }

        .progress > div {
            width: 7px;
            height: 7px;
            background-color: #7c7f84;
            border-radius: 100%;
            display: inline-block;
            animation: wave 1.4s infinite ease-in-out both;
        }

        .progress .dot1 {
            animation-delay: -0.32s;
        }

        .progress .dot2 {
            animation-delay: -0.16s;
        }

        .progress .dot3 {
            animation-delay: 0s;
        }

        @keyframes wave {
            0%, 60%, 100% {
                transform: initial;
            }

            30% {
                transform: translateY(-8px);
            }
        }
    </style>

    <div class="progress">
        <div class="dot1"></div>
        <div class="dot2"></div>
        <div class="dot3"></div>
    </div>
"""

_three_pulsing_dots_animation = """
    <style>
        .progress {
            margin-top: -4px;
            width: 28px;
        }

        .progress > div {
            width: 7px;
            height: 7px;
            background-color: #7c7f84;
            border-radius: 100%;
            display: inline-block;
            animation: pulse 1.4s infinite ease-in-out both;
        }

        .progress .dot1 {
            animation-delay: -0.32s;
        }

        .progress .dot2 {
            animation-delay: -0.16s;
        }

        .progress .dot3 {
            animation-delay: 0s;
        }

        @keyframes pulse {
            0%, 80%, 100% {
                transform: scale(0);
            }
            40% {
                transform: scale(1.0);
            }
        }
    </style>

    <div class="progress">
        <div class="dot1"></div>
        <div class="dot2"></div>
        <div class="dot3"></div>
    </div>
"""

def three_waving_dots():
    return st.html(_three_waving_dots_animation)

def three_pulsing_dots():
    return st.html(_three_pulsing_dots_animation)
