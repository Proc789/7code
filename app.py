from flask import Flask, render_template_string, request, redirect
import random
from collections import Counter

app = Flask(__name__)
history = []
predictions = []
hot_hits = 0
dynamic_hits = 0
extra_hits = 0
all_hits = 0
total_tests = 0
current_stage = 1
training_enabled = False
last_prediction = None
last_champion = None

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>7碼預測器</title>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
</head>
<body style='max-width: 400px; margin: auto; padding-top: 40px; font-family: sans-serif; text-align: center;'>
  <h2>7碼預測器</h2>
  <div>版本：熱號2 + 動熱2 + 補碼3（公版UI）</div>
  <form method='POST'>
    <input name='first' id='first' placeholder='冠軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'second')" inputmode="numeric"><br><br>
    <input name='second' id='second' placeholder='亞軍' required style='width: 80%; padding: 8px;' oninput="moveToNext(this, 'third')" inputmode="numeric"><br><br>
    <input name='third' id='third' placeholder='季軍' required style='width: 80%; padding: 8px;' inputmode="numeric"><br><br>
    <button type='submit' style='padding: 10px 20px;'>提交</button>
  </form>
  <br>
  <a href='/toggle'><button>{{ '關閉統計模式' if training else '啟動統計模式' }}</button></a>
  <a href='/reset'><button>清除所有資料</button></a>

  {% if prediction %}
    <div style='margin-top: 20px;'>
      <strong>本期預測號碼：</strong> {{ prediction }}（目前第 {{ stage }} 關）
    </div>
  {% endif %}
  {% if last_prediction %}
    <div style='margin-top: 10px;'>
      <strong>上期預測號碼：</strong> {{ last_prediction }}<br>
      <strong>上期冠軍號碼：</strong> {{ last_champion }}<br>
      <strong>是否命中：</strong> {{ '命中' if last_champion in last_prediction else '未命中' }}
    </div>
  {% endif %}

  {% if training %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>命中統計：</strong><br>
      冠軍命中次數（任一區）：{{ all_hits }} / {{ total_tests }}<br>
      熱號命中次數：{{ hot_hits }}<br>
      動熱命中次數：{{ dynamic_hits }}<br>
      補碼命中次數：{{ extra_hits }}<br>
    </div>
  {% endif %}

  {% if history %}
    <div style='margin-top: 20px; text-align: left;'>
      <strong>最近輸入紀錄：</strong>
      <ul>
        {% for row in history[-10:] %}
          <li>第 {{ loop.index }} 期：{{ row }}</li>
        {% endfor %}
      </ul>
    </div>
  {% endif %}

  <script>
    function moveToNext(current, nextId) {
      setTimeout(() => {
        if (current.value === '0') current.value = '10';
        let val = parseInt(current.value);
        if (!isNaN(val) && val >= 1 && val <= 10) {
          document.getElementById(nextId).focus();
        }
      }, 100);
    }
  </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global history, predictions, hot_hits, dynamic_hits, extra_hits
    global all_hits, total_tests, current_stage, training_enabled
    global last_prediction, last_champion

    prediction = None

    if request.method == 'POST':
        try:
            first = int(request.form['first'])
            second = int(request.form['second'])
            third = int(request.form['third'])
            current = [first, second, third]
            history.append(current)

            if len(history) >= 3:
                flat = [n for group in history[-3:] for n in group]
                freq = Counter(flat)
                hot = [n for n, _ in sorted(freq.items(), key=lambda x: (-x[1], -flat[::-1].index(x[0])))[:2]]
                dynamic_pool = [n for n in flat if n not in hot]
                dynamic_freq = Counter(dynamic_pool)
                dynamic = [n for n, _ in sorted(dynamic_freq.items(), key=lambda x: (-x[1], -dynamic_pool[::-1].index(x[0])))[:2]]
                used = set(hot + dynamic)
                remaining = [n for n in range(1, 11) if n not in used]
                random.shuffle(remaining)
                extra = remaining[:3]

                prediction = sorted(hot + dynamic + extra)
                predictions.append(prediction)
                last_prediction = prediction
                last_champion = first

                if training_enabled:
                    total_tests += 1
                    if first in prediction:
                        all_hits += 1
                        current_stage = 1
                    else:
                        current_stage += 1
                    if first in hot:
                        hot_hits += 1
                    elif first in dynamic:
                        dynamic_hits += 1
                    elif first in extra:
                        extra_hits += 1

        except:
            prediction = ['格式錯誤']

    return render_template_string(TEMPLATE,
        prediction=prediction,
        last_prediction=last_prediction,
        last_champion=last_champion,
        stage=current_stage,
        history=history,
        training=training_enabled,
        hot_hits=hot_hits,
        dynamic_hits=dynamic_hits,
        extra_hits=extra_hits,
        all_hits=all_hits,
        total_tests=total_tests)

@app.route('/toggle')
def toggle():
    global training_enabled, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage
    training_enabled = not training_enabled
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    return redirect('/')

@app.route('/reset')
def reset():
    global history, predictions, hot_hits, dynamic_hits, extra_hits, all_hits, total_tests, current_stage, last_prediction, last_champion
    history.clear()
    predictions.clear()
    hot_hits = dynamic_hits = extra_hits = all_hits = total_tests = 0
    current_stage = 1
    last_prediction = None
    last_champion = None
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
