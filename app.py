# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
import math

# --- Constants for Bar Exam Simulation (UPDATED) ---
CHARS_PER_LINE = 49  # Characters per line based on CBT standard
LINES_PER_PAGE = 33  # Standard lines per page on the answer sheet
LINES_PER_100_POINTS = 130 # Standard lines expected for 100 points
MINUTES_PER_100_POINTS = 60 # Standard time allocated for 100 points
# -----------------------------------------

app = Flask(__name__)

def calculate_lines(text, chars_per_line):
    """
    Estimates the number of lines the text would occupy based on CHARS_PER_LINE.
    Counts explicit newlines and estimates lines based on character count.
    len() correctly counts precomposed Korean syllables as 1 character.
    """
    if not text:
        return 0

    lines = text.split('\n')
    total_lines = 0
    for line in lines:
        if not line:
             total_lines += 1
        else:
            total_lines += math.ceil(len(line) / max(1, chars_per_line))

    if total_lines == 0 and len(text) > 0:
         return math.ceil(len(text) / max(1, chars_per_line))

    return total_lines


def format_minutes_seconds(total_seconds):
    """Helper function to format total seconds into minutes and seconds."""
    if total_seconds is None or total_seconds < 0:
        return 0, 0
    total_seconds = max(0, total_seconds)
    minutes = math.floor(total_seconds / 60)
    remainder_seconds = total_seconds % 60
    return minutes, remainder_seconds

@app.route('/', methods=['GET', 'POST'])
def index():
    context = {
        'calculation_done': False, 'error': None, 'text_input': '', 'typing_speed': '',
        'char_count': 0, 'estimated_lines': 0, 'estimated_pages': 0.0, # Default to float
        'estimated_score': 0.0, 'standard_time_for_score_seconds': 0, 'standard_time_minutes': 0,
        'standard_time_remainder_seconds': 0, 'typing_time_total_seconds': 0, 'typing_time_minutes': 0,
        'typing_time_remainder_seconds': 0, 'diff_vs_standard_seconds': None,
        'diff_vs_standard_minutes_abs': 0, 'diff_vs_standard_seconds_abs': 0,
        'chars_per_line_const': CHARS_PER_LINE, 'lines_per_page_const': LINES_PER_PAGE,
        'lines_per_100_points_const': LINES_PER_100_POINTS, 'minutes_per_100_points_const': MINUTES_PER_100_POINTS,
    }

    if request.method == 'POST':
        text = request.form.get('text_input', '').strip()
        speed_str = request.form.get('typing_speed', '')

        context['text_input'] = text
        context['typing_speed'] = speed_str

        speed_cpm = 0
        if not text:
            context['error'] = "답안 텍스트를 입력해주세요."
        elif not speed_str:
            context['error'] = "타자 속도(분당 글자 수)를 입력해주세요."
        else:
            try:
                speed_cpm = int(speed_str)
                if speed_cpm <= 0:
                    context['error'] = "타자 속도는 0보다 커야 합니다."
            except ValueError:
                 context['error'] = "타자 속도는 숫자로 입력해주세요."

        if context['error'] is None and speed_cpm > 0:
            try:
                context['char_count'] = len(text)
                context['typing_time_total_seconds'] = (context['char_count'] / speed_cpm) * 60 if speed_cpm > 0 else 0
                context['typing_time_minutes'], context['typing_time_remainder_seconds'] = format_minutes_seconds(context['typing_time_total_seconds'])

                context['estimated_lines'] = calculate_lines(text, CHARS_PER_LINE)

                # --- MODIFIED CALCULATION for estimated_pages ---
                if LINES_PER_PAGE > 0:
                    context['estimated_pages'] = context['estimated_lines'] / LINES_PER_PAGE # Use simple division, remove math.ceil
                else:
                    context['estimated_pages'] = 0.0
                # --- END MODIFICATION ---

                context['estimated_score'] = (context['estimated_lines'] / LINES_PER_100_POINTS) * 100 if LINES_PER_100_POINTS > 0 else 0
                context['standard_time_for_score_seconds'] = (context['estimated_score'] / 100) * MINUTES_PER_100_POINTS * 60 if context['estimated_score'] > 0 else 0
                context['standard_time_minutes'], context['standard_time_remainder_seconds'] = format_minutes_seconds(context['standard_time_for_score_seconds'])

                if context['standard_time_for_score_seconds'] > 0:
                     context['diff_vs_standard_seconds'] = context['standard_time_for_score_seconds'] - context['typing_time_total_seconds']
                     diff_abs_standard = abs(context['diff_vs_standard_seconds'])
                     context['diff_vs_standard_minutes_abs'], context['diff_vs_standard_seconds_abs'] = format_minutes_seconds(diff_abs_standard)

                context['calculation_done'] = True

            except Exception as e:
                print(f"An error occurred during calculation: {e}")
                context['error'] = "계산 중 오류가 발생했습니다."

    return render_template('index.html', **context)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
