uniform mat4 transform;
uniform mat4 projection;

in vec3 pos;

void main() {
    gl_Position = projection * transform * vec4(pos, 1.0);
}
