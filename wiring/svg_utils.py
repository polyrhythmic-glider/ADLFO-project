from html import escape

INK = '#233449'
BLUE = '#2673bc'
RED = '#cb4148'
GREEN = '#187961'
PURPLE = '#8144ad'
ORANGE = '#b77218'
GRAY = '#728292'

class Svg:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
        self.box(0, 0, width, height, '#f5f8fc')

    def box(self, x, y, w, h, fill='white', stroke='none', radius=0):
        self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

    def text(self, x, y, value, size=21, color=INK, anchor='start', bold=False):
        self.s.append(f'<text x="{x}" y="{y}" xml:space="preserve" font-family="DejaVu Sans,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{"bold" if bold else "normal"}">{escape(value)}</text>')

    def line(self, points, color=INK, width=3, halo=False):
        if halo:
            self.line(points, '#f5f8fc', width + 4)
        pts = ' '.join(f'{x},{y}' for x, y in points)
        self.s.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')

    def dot(self, x, y, color=INK, r=5):
        self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def path(self, d, fill='white', stroke=INK, width=3):
        self.s.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}"/>')
