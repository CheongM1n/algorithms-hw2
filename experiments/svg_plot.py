"""외부 라이브러리 없이 꺾은선 그래프를 SVG로 그린다."""

COLORS = ["#2a6fdb", "#d9534f", "#1a9e5c", "#e08a00"]


def line_chart(path, title, xlabel, ylabel, xs, series, width=720, height=440):
    """series: [(이름, ys, 색 번호, 점선 여부), ...]. 측정값은 실선+점, 이론값은 점선."""
    left, right, top, bottom = 70, 190, 50, 60
    pw, ph = width - left - right, height - top - bottom
    ymax = max(max(ys) for _, ys, _, _ in series)
    ymax = _nice(ymax)
    xmin, xmax = 0, max(xs)

    def px(x):
        return left + (x - xmin) / (xmax - xmin) * pw

    def py(y):
        return top + ph - y / ymax * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'font-family="sans-serif" font-size="12">',
           f'<rect width="{width}" height="{height}" fill="white"/>',
           f'<text x="{left + pw / 2}" y="28" text-anchor="middle" font-size="15" font-weight="bold">{title}</text>']
    for i in range(6):
        y = ymax * i / 5
        out.append(f'<line x1="{left}" y1="{py(y):.1f}" x2="{left + pw}" y2="{py(y):.1f}" stroke="#e5e5e5"/>')
        out.append(f'<text x="{left - 8}" y="{py(y) + 4:.1f}" text-anchor="end">{y:g}</text>')
    ticks = _ticks(xmax)
    for x in ticks:
        out.append(f'<text x="{px(x):.1f}" y="{top + ph + 18}" text-anchor="middle">{x:g}</text>')
    out.append(f'<line x1="{left}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}" stroke="#333"/>')
    out.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + ph}" stroke="#333"/>')
    out.append(f'<text x="{left + pw / 2}" y="{height - 15}" text-anchor="middle">{xlabel}</text>')
    out.append(f'<text x="18" y="{top + ph / 2}" text-anchor="middle" '
               f'transform="rotate(-90 18 {top + ph / 2})">{ylabel}</text>')

    for k, (name, ys, color, dashed) in enumerate(series):
        c = COLORS[color % len(COLORS)]
        pts = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in zip(xs, ys))
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="2"{dash}/>')
        if not dashed:
            for x, y in zip(xs, ys):
                out.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="3" fill="{c}"/>')
        ly = top + 10 + k * 22
        lx = left + pw + 15
        out.append(f'<line x1="{lx}" y1="{ly}" x2="{lx + 28}" y2="{ly}" stroke="{c}" stroke-width="2"{dash}/>')
        out.append(f'<text x="{lx + 34}" y="{ly + 4}">{name}</text>')
    out.append("</svg>")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def _nice(v):
    for step in (0.5, 1, 2, 2.5, 5, 10, 20, 25, 50):
        if v <= step * 5:
            return step * 5
    return v


def _ticks(xmax):
    step = 0.5 if xmax > 2 else 0.1
    n = int(round(xmax / step))
    return [round(i * step, 2) for i in range(n + 1)]
