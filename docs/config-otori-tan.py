# An otori-tan theme: Otori-tan's colours — the student council's PR officer in
# `Seitokai ni mo Ana wa Aru!`, the pale green of her hair and the warm amber
# her eyes run to — drawn as a dusk the terminal is inked over. Long strands of
# mint drift across it, sparks of her two eye tones climb between them, and the
# shell's own colours are graded into the same palette, so `ls`, a diff and a
# status line all come out hers.
#
# A picture of her can stand in it, too: name a cut-out as `background_image`
# and the shader draws it whole — as tall as the window and centred — over the
# dusk, the transparent parts of the cut-out letting the dusk through and the
# sparks still climbing over her.
#
# Copy it over the file hext writes on first run — `~/.config/hext/config.py` —
# and save it again while the terminal is open: a debug build watches the file,
# so the look changes without a restart.
#
# A theme is a shader and the two colours the config owns (`background` and
# `cursor_color`), and the shader is the interesting half, because the grid
# carries the colours the shell asked for: the only place to re-colour a
# terminal is after the cells are drawn. That is the `otori()` ramp below — the
# shell's ink turned into its brightness and walked through three stops, the
# deep sage under her hair, the mint of it, and the amber her eyes run to — so
# brightness, and with it the reading order of the text, survives the grade.
#
# This is the third of the examples: `docs/config-aurora.py` animates from
# Python as well as from the shader, and `docs/config-neon.py` is a synthwave
# sunset.

# The screen shader, as WGSL source. It has to declare the `vs_screen` and
# `fs_screen` entry points and the bindings `src/render/shaders/screen.wgsl`
# uses — group 0, bindings 0 to 4: the uniform, the screen texture (the grid as
# ink, its alpha the coverage), a sampler, the picture behind the grid and the
# picture over everything. A source that does not compile is reported and the
# built-in shader used instead, so a typo here is a note rather than a terminal
# that will not start.
shader = """
// The otori-tan screen: a dusk of deep sage, strands of pale green hair
// drifting across it, and warm sparks climbing through them, with the grid
// inked over the top. `screen.time` is what makes it move — the strands sway,
// the sparks rise and twinkle — and `animate = True` below is what keeps
// `time` ticking.
//
// The struct matches the uniform `src/render/drawable.rs` writes, field for
// field, and `pad` is only there to keep the size a multiple of sixteen.
struct Screen {
    background: vec4<f32>,
    cursor_color: vec4<f32>,
    resolution: vec2<f32>,
    grid: vec2<u32>,
    cursor: vec2<u32>,
    cursor_visible: u32,
    cursor_style: u32,
    cursor_size: vec2<f32>,
    time: f32,
    pad: u32,
}

@group(0) @binding(0) var<uniform> screen: Screen;
@group(0) @binding(1) var screen_tex: texture_2d<f32>;
@group(0) @binding(2) var screen_sampler: sampler;
@group(0) @binding(3) var background_tex: texture_2d<f32>;
@group(0) @binding(4) var foreground_tex: texture_2d<f32>;

const CURSOR_BLOCK: u32 = 0u;
const CURSOR_BAR: u32 = 1u;

// The two colours the whole picture is made of: the hair and the eyes.
const MINT: vec3<f32> = vec3(0.55, 0.83, 0.63);
const AMBER: vec3<f32> = vec3(1.00, 0.72, 0.44);

// The picture's own shape: its width divided by its height. The picture is
// drawn whole — as tall as the window and centred — so this is what keeps her
// from being squashed; 474 / 646 is the one this file was written for, and it
// wants updating when the picture does.
const PICTURE_ASPECT: f32 = 0.7337;

@vertex
fn vs_screen(@builtin(vertex_index) index: u32) -> @builtin(position) vec4<f32> {
    let corner = vec2<f32>(f32((index << 1u) & 2u), f32(index & 2u));

    return vec4<f32>(corner * 2.0 - vec2<f32>(1.0), 0.0, 1.0);
}

// A number that jumps about between 0 and 1 for every input: what the sparks
// are scattered by, and what the dither is made of.
fn hash(value: vec2<f32>) -> f32 {
    return fract(sin(dot(value, vec2<f32>(127.1, 311.7))) * 43758.5453);
}

// How bright a colour is, for telling a cell's ink from its background.
fn luma(color: vec3<f32>) -> f32 {
    return dot(color, vec3<f32>(0.2126, 0.7152, 0.0722));
}

// The room behind everything: a deep sage, lighter towards the top where the
// window is, with the warm patch of that window kept in the corner the way a
// classroom still holds the afternoon after the bell.
fn dusk(uv: vec2<f32>) -> vec3<f32> {
    var color = mix(
        vec3<f32>(0.015, 0.030, 0.022),
        vec3<f32>(0.050, 0.085, 0.065),
        1.0 - uv.y,
    );

    let away = uv - vec2<f32>(0.84, 0.16);
    color = color + AMBER * (0.075 / (1.0 + 30.0 * dot(away, away)));

    return color;
}

// Where the picture is sampled from: drawn whole, as tall as the window and
// centred, so a portrait of her stands in the room rather than being stretched
// across it. A sample outside 0..1 is her absence: there is nothing to draw.
fn picture_at(uv: vec2<f32>) -> vec2<f32> {
    let shown = PICTURE_ASPECT * screen.resolution.y / screen.resolution.x;

    return vec2<f32>((uv.x - 0.5) / shown + 0.5, uv.y);
}

// The strands: five ribbons of pale green, each a soft band in x that leans on
// its own slow sway and shimmers unevenly down its length, the way light slides
// down hair. They add, so where two cross the green builds.
fn strands(uv: vec2<f32>, time: f32) -> f32 {
    var light = 0.0;

    for (var band = 0; band < 5; band = band + 1) {
        let index = f32(band);
        let lean = 0.030 * sin(uv.y * 3.4 + time * 0.35 + index * 2.3);
        let centre = 0.10 + 0.20 * index + lean;
        let width = 0.045 + 0.012 * sin(index * 1.7 + 0.6);
        let offset = (uv.x - centre) / width;
        let body = exp(-offset * offset);
        let shimmer = 0.80 + 0.20 * sin(uv.y * 7.0 - time * 0.6 + index * 3.1);

        // Thin towards the very top and bottom, so the strands fade into the
        // room rather than running the full height of the window.
        let ends = smoothstep(0.0, 0.12, uv.y) * (1.0 - smoothstep(0.72, 1.0, uv.y));

        light = light + body * shimmer * ends;
    }

    return light;
}

// The sparks: her eyes, scattered and climbing. One candidate per cell of a
// coarse grid, only the very few whose hash is near the top drawn, each with
// its own twinkle — and each coloured somewhere between the two tones her iris
// runs between, a warm gold and a deeper coral.
fn sparks(uv: vec2<f32>, time: f32) -> vec3<f32> {
    let scale = vec2<f32>(48.0, 32.0);
    let drift = uv * scale + vec2<f32>(0.0, time * 5.0);
    let cell = floor(drift);
    let seed = hash(cell);

    let centre = vec2<f32>(
        0.25 + 0.5 * fract(seed * 13.7),
        0.25 + 0.5 * fract(seed * 7.3),
    );
    let away = fract(drift) - centre;
    let spark = 1.0 - smoothstep(0.02, 0.14, length(away));

    let lit = step(0.972, seed);
    let twinkle = 0.55 + 0.45 * sin(time * (0.5 + seed) + seed * 40.0);
    let tone = mix(
        vec3<f32>(1.00, 0.76, 0.48),
        vec3<f32>(0.92, 0.46, 0.40),
        fract(seed * 3.9),
    );

    return tone * spark * lit * twinkle;
}

// The theme's own palette: whatever colour the shell asked for is turned into
// its brightness and read back out of this ramp, so every cell on screen is in
// the theme. The stops are hers — the deep sage under her hair, the mint of it,
// and the warm amber her eyes run to — and brightness is what is preserved, so
// brighter still reads as louder.
fn otori(color: vec3<f32>) -> vec3<f32> {
    let level = clamp(luma(color), 0.0, 1.0);

    let deep = vec3<f32>(0.14, 0.20, 0.16);
    let mid = vec3<f32>(0.55, 0.83, 0.63);
    let hot = vec3<f32>(1.00, 0.78, 0.55);

    if (level < 0.5) {
        return mix(deep, mid, level * 2.0);
    }

    return mix(mid, hot, (level - 0.5) * 2.0);
}

// What the cursor covers in a cell, the way the built-in shader works it out.
fn cursor_mask(local: vec2<f32>, size: vec2<f32>, style: u32) -> f32 {
    let text = min(screen.cursor_size, size);
    let origin = (size - text) * 0.5;
    let inside = all(local >= origin) && all(local < origin + text);

    if (style == CURSOR_BAR) {
        let bar = max(1.0, text.x * 0.125);

        return select(0.0, 1.0, inside && local.x < origin.x + bar);
    }

    return select(0.0, 1.0, inside);
}

@fragment
fn fs_screen(@builtin(position) position: vec4<f32>) -> @location(0) vec4<f32> {
    let uv = position.xy / screen.resolution;
    let size = max(screen.cursor_size, vec2<f32>(1.0));

    // The room: the dusk and the strands drifting across it, and — when the
    // config named a picture — her, standing in front of the strands. This is
    // what the grid is inked onto.
    var color = dusk(uv);
    color = color + MINT * strands(uv, screen.time) * 0.32;

    // Her, drawn whole: the cut-out is premultiplied, so its edges filter into
    // the dusk without a pale fringe, and the app hands the shader a one-pixel
    // stand-in of the background colour when no picture is named — a sample
    // that is exactly that colour is how "no picture" reads here.
    let raw = picture_at(uv);
    let inside = all(raw >= vec2<f32>(0.0)) && all(raw <= vec2<f32>(1.0));
    let picture = textureSample(
        background_tex,
        screen_sampler,
        clamp(raw, vec2<f32>(0.0), vec2<f32>(1.0)),
    );
    let named = smoothstep(0.015, 0.05, distance(picture.rgb, screen.background.rgb));
    let held = select(0.0, named, inside);

    color = color * (1.0 - held * picture.a) + picture.rgb * held;

    // The sparks climb over her the way they climb over everything.
    color = color + sparks(uv, screen.time);

    // The glass the cursor falls back to, and what tells its ink from the room
    // below.
    let backdrop = color;

    // The grid is ink rather than a picture: its alpha says how much of the
    // pixel a cell covers, so the shell's own colours, graded into the theme,
    // land over the room.
    let ink = textureSample(screen_tex, screen_sampler, uv);
    color = mix(color, otori(ink.rgb), ink.a);

    // A cheap glow: the ink above and below a pixel is added back over it, so
    // bright text lights the space around it in its own colour. A real bloom
    // blurs a downsampled copy of the frame; at a cell's size this is close
    // enough and far cheaper.
    let pixel = 1.0 / screen.resolution;
    let above = textureSample(screen_tex, screen_sampler, uv - vec2<f32>(0.0, pixel.y * 2.0));
    let below = textureSample(screen_tex, screen_sampler, uv + vec2<f32>(0.0, pixel.y * 2.0));
    color = color + otori((above.rgb + below.rgb) * 0.5) * (above.a + below.a) * 0.05;

    // The cursor: her eyes' amber by default — the Python below walks it over
    // to her hair's mint and back — and a block keeps the character under it
    // readable by falling back to the room wherever the ink brightened the
    // pixel, the same bargain the built-in shader makes.
    let cell = min(
        vec2<u32>(position.xy / size),
        max(screen.grid, vec2<u32>(1u)) - vec2<u32>(1u),
    );

    if (screen.cursor_visible != 0u && all(cell == screen.cursor)) {
        let local = position.xy - vec2<f32>(cell) * size;
        let mask = cursor_mask(local, size, screen.cursor_style);
        var cursor = screen.cursor_color.rgb;

        if (screen.cursor_style == CURSOR_BLOCK) {
            let drawn = clamp((luma(color) - luma(backdrop)) * 4.0, 0.0, 1.0);

            cursor = mix(cursor, backdrop, drawn);
        }

        color = mix(color, cursor, mask);
    }

    // The glass: the corners of a tube fall away, its lines are drawn across
    // the picture, and the supply is never perfectly steady.
    let centred = (uv - vec2<f32>(0.5)) * vec2<f32>(1.0, screen.resolution.y / screen.resolution.x);
    color = color * (1.0 - 0.80 * pow(dot(centred, centred), 1.5));
    color = color * (0.93 + 0.07 * sin(position.y * 3.14159265));

    // A one-step dither, fixed to the pixel rather than to the frame, so the
    // flat parts of the dusk do not band without the picture crawling.
    color = color + vec3<f32>((hash(position.xy) - 0.5) / 255.0);

    // Whatever the config put over everything goes over all of it. There is
    // nothing there here, but this is where a `foreground_image` would land.
    let glass = textureSample(foreground_tex, screen_sampler, uv);
    color = mix(color, glass.rgb, glass.a);

    return vec4<f32>(color, 1.0);
}
"""

# Whether to draw a frame every frame: the strands sway, the sparks climb and
# twinkle, so this theme wants one. Nothing is drawn while the window is in the
# background.
animate = True

# The two colours the config owns, as (r, g, b) in 0.0..=1.0. The dusk is drawn
# by the shader above, so `background` is mostly the colour the window is
# cleared to before it — the deep sage the picture starts from. The cursor
# starts on her eyes' amber; the render function below walks it from there.
background = (0.02, 0.045, 0.035)
cursor_color = (1.00, 0.70, 0.36)

# A cut-out of her to stand in the dusk, as the path to a PNG: the shader above
# draws it whole — as tall as the window and centred — and the cut-out wants
# its background keyed out with a soft, anti-aliased edge and saved with the
# pixels multiplied through their own alpha, so the rim filters into the dusk
# smoothly and without a pale fringe. `None` is the dusk alone, and a picture
# that cannot be read is reported and the dusk used.
#
#     background_image = "/home/you/pictures/otori-tan.png"
background_image = None

# A render function: a system in the frame's pipeline, handed the world just
# before the frame is drawn. `world.terminal()` is the running terminal, so this
# is where the terminal's own colours can be animated from Python.
import math
import time

started = time.monotonic()


def breathe(world):
    terminal = world.terminal()

    # The file is read before the app builds the terminal, so a system is the
    # only place this can be non-None.
    if terminal is None:
        return

    phase = time.monotonic() - started
    pulse = 0.5 + 0.5 * math.sin(phase * 0.5)

    # The cursor breathes between the two colours that are hers — the mint of
    # her hair at one end, the amber of her eyes at the other — and never quite
    # rests on either. The colour lands on the next frame, which is a frame too
    # soon to see.
    terminal.cursor_color = (
        0.42 + 0.58 * pulse,
        0.88 - 0.18 * pulse,
        0.62 - 0.26 * pulse,
    )


world.add_system(breathe, pipeline=render_pipeline)
