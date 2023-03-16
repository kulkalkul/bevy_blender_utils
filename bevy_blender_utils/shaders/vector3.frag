uniform vec4 color;

out vec4 fragColor;

void main() {
    vec2 coord = 2.0 * gl_PointCoord - 1.0;
    float radius = length(coord);

    float delta = fwidth(radius);
    float alpha = 1.0 - smoothstep(1.0 - delta, 1.0 + delta, radius);

    fragColor = color * alpha;
}

