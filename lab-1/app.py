from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def rgb_to_cmyk(r, g, b):
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    k = 1.0 - max(r_norm, g_norm, b_norm)
    if k >= 1.0:
        return 0.0, 0.0, 0.0, 100.0

    c = (1.0 - r_norm - k) / (1.0 - k)
    m = (1.0 - g_norm - k) / (1.0 - k)
    y = (1.0 - b_norm - k) / (1.0 - k)

    return round(c * 100, 1), round(m * 100, 1), round(y * 100, 1), round(k * 100, 1)


def cmyk_to_rgb(c, m, y, k):
    c_norm = c / 100.0
    m_norm = m / 100.0
    y_norm = y / 100.0
    k_norm = k / 100.0

    r = 255.0 * (1.0 - c_norm) * (1.0 - k_norm)
    g = 255.0 * (1.0 - m_norm) * (1.0 - k_norm)
    b = 255.0 * (1.0 - y_norm) * (1.0 - k_norm)

    return int(round(r)), int(round(g)), int(round(b))


def rgb_to_hls(r, g, b):
    r_norm = r / 255.0
    g_norm = g / 255.0
    b_norm = b / 255.0

    max_c = max(r_norm, g_norm, b_norm)
    min_c = min(r_norm, g_norm, b_norm)
    delta = max_c - min_c

    l = (max_c + min_c) / 2.0

    if delta == 0:
        h = 0.0
        s = 0.0
    else:
        if l < 0.5:
            s = delta / (max_c + min_c)
        else:
            s = delta / (2.0 - max_c - min_c)

        if max_c == r_norm:
            h = 60.0 * (((g_norm - b_norm) / delta) % 6)
        elif max_c == g_norm:
            h = 60.0 * (((b_norm - r_norm) / delta) + 2)
        else:
            h = 60.0 * (((r_norm - g_norm) / delta) + 4)

    return round(h, 1), round(l * 100, 1), round(s * 100, 1)


def _hue_to_rgb(p, q, t):
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p


def hls_to_rgb(h, l, s):
    h_norm = h / 360.0
    l_norm = l / 100.0
    s_norm = s / 100.0

    if s_norm == 0:
        r = g = b = l_norm
    else:
        q = l_norm * (1.0 + s_norm) if l_norm < 0.5 else l_norm + s_norm - (l_norm * s_norm)
        p = 2.0 * l_norm - q

        r = _hue_to_rgb(p, q, h_norm + 1 / 3)
        g = _hue_to_rgb(p, q, h_norm)
        b = _hue_to_rgb(p, q, h_norm - 1 / 3)

    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


# --- РОУТЫ СЕРВЕРА ---

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/convert', methods=['POST'])
def convert():
    data = request.json
    source_model = data.get('model')
    values = data.get('values')

    r, g, b = 0, 0, 0

    # 1. Приводим всё к промежуточной базовой модели RGB
    if source_model == 'RGB':
        r = int(values['r'])
        g = int(values['g'])
        b = int(values['b'])
    elif source_model == 'CMYK':
        c = float(values['c'])
        m = float(values['m'])
        y = float(values['y'])
        k = float(values['k'])
        r, g, b = cmyk_to_rgb(c, m, y, k)
    elif source_model == 'HLS':
        h = float(values['h'])
        l = float(values['l'])
        s = float(values['s'])
        r, g, b = hls_to_rgb(h, l, s)

    # Ограничиваем диапазон [0, 255]
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    # 2. Вычисляем значения для двух других моделей
    c, m, y, k = rgb_to_cmyk(r, g, b)
    h, l, s = rgb_to_hls(r, g, b)

    hex_color = f"#{r:02x}{g:02x}{b:02x}"

    return jsonify({
        'rgb': {'r': r, 'g': g, 'b': b},
        'cmyk': {'c': c, 'm': m, 'y': y, 'k': k},
        'hls': {'h': h, 'l': l, 's': s},
        'hex': hex_color
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)