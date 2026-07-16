# Godot 4 `.gdshader` Authoring Guide

This is a self-contained reference for generating Godot 4 shader files
(`.gdshader`) without relying on the Godot editor. It is intended for AI
systems that need to create valid shaders with the correct language syntax,
shader stages, uniforms, render modes, built-ins, preprocessor directives,
texture access, and renderer-specific behavior.

This guide is based on the Godot 4.7 documentation snapshot.

Godot shaders use a GLSL ES 3.0-like language, but they are not interchangeable
with arbitrary GLSL. Godot injects stage-specific inputs and outputs, applies
engine transforms, and validates declarations according to `shader_type`.

Read [`shared_concepts.md`](shared_concepts.md) for the
shared rules on project-specific facts, typed values, coordinate spaces,
dependencies, and general validation.

## 1. High-confidence generation rules

Use these rules when creating a `.gdshader`:

1. Begin with exactly one `shader_type` declaration.
2. Use the correct shader type for the object or rendering pass.
3. Put a `render_mode` declaration after `shader_type` when needed.
4. Declare uniforms, constants, varyings, structs, helper functions, and
   processor functions at global scope.
5. End ordinary statements with semicolons.
6. Use braces for every control-flow block and function body.
7. Do not assume implicit numeric or vector conversions; use constructors.
8. Initialize local variables before reading them.
9. Use the built-ins allowed by the selected shader type and stage.
10. Use texture hints for screen, depth, normal-roughness, and source-color
    textures.
11. Declare global uniforms in Project Settings before using them in a shader.
12. Keep preprocessor directives unindented and do not add semicolons to
    directives unless the replacement text explicitly requires one.
13. Include only `.gdshaderinc` files, never another `.gdshader`.
14. Do not write a stage function that is unavailable for the selected
    `shader_type`.
15. Check renderer limitations before using advanced samplers, passes, or
    built-ins.
16. Preserve engine-generated `.gdshader.uid` and `.gdshaderinc.uid` sidecars
    in Godot 4.4 and later. Commit and move them with their source files.

A shader can parse correctly and still fail to compile or render correctly if
it writes the wrong output, uses a built-in in the wrong stage, or assumes the
wrong coordinate space.

## 2. File identity and minimal structure

The normal extension is `.gdshader`. Shader include files use `.gdshaderinc`.

Minimal spatial shader:

```gdshader
shader_type spatial;
```

Minimal canvas item shader:

```gdshader
shader_type canvas_item;
```

Minimal particle shader:

```gdshader
shader_type particles;
```

Minimal sky shader:

```gdshader
shader_type sky;
```

Minimal fog shader:

```gdshader
shader_type fog;
```

Minimal texture blit shader:

```gdshader
shader_type texture_blit;
```

Typical complete structure:

```gdshader
shader_type spatial;

render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform vec4 tint : source_color = vec4(1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.5;

const float EPSILON = 0.0001;
varying vec3 world_position;

float remap_value(float value, float from_min, float from_max,
        float to_min, float to_max) {
    return to_min + (value - from_min) * (to_max - to_min)
            / (from_max - from_min);
}

void vertex() {
    world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    ALBEDO = tint.rgb;
    ROUGHNESS = roughness;
}
```

Global declarations must appear before the functions that use them. Includes
can provide global declarations and helper functions.

## 3. Shader types and entry points

Choose one shader type:

| Shader type | Primary use | Entry points |
| --- | --- | --- |
| `spatial` | 3D materials | `vertex`, `fragment`, `light` |
| `canvas_item` | 2D and CanvasItem materials | `vertex`, `fragment`, `light` |
| `particles` | GPU particle simulation | `start`, `process` |
| `sky` | Sky background and radiance | `sky` |
| `fog` | Volumetric fog volumes | `fog` |
| `texture_blit` | DrawableTexture2D blits | `blit` |

The function signatures are always:

```gdshader
void vertex() {}
void fragment() {}
void light() {}
void start() {}
void process() {}
void sky() {}
void fog() {}
void blit() {}
```

Only define functions supported by the selected shader type. A stage function
that is never defined uses Godot's default behavior for that stage.

## 4. Syntax and lexical rules

### 4.1 Statements and blocks

Statements end with semicolons:

```gdshader
float intensity = 1.0;
ALBEDO = vec3(intensity);
```

Blocks use braces:

```gdshader
if (value > 0.0) {
    result = value;
} else {
    result = 0.0;
}
```

Always use braces, including for one-line blocks. This avoids accidental
control-flow changes when code is generated or edited.

### 4.2 Comments

Single-line comments:

```gdshader
// This is a shader comment.
```

Block comments:

```gdshader
/*
    This comment spans multiple lines.
*/
```

Document uniforms and reusable functions with block comments directly above
their declarations:

```gdshader
/** Surface tint in linear color space. */
uniform vec4 tint : source_color = vec4(1.0);
```

### 4.3 Naming

Recommended naming:

- functions and variables: `snake_case`
- constants and preprocessor macros: `CONSTANT_CASE`
- structs: `PascalCase`
- shader include files: descriptive `snake_case.gdshaderinc`
- varyings: names that identify the stage-to-stage data

Names must not collide with reserved words, built-ins, uniforms, functions, or
other declarations in the same scope.

### 4.4 Whitespace and style

Use tabs for indentation, UTF-8 text, LF line endings, and no BOM. Keep braces
on the same line as the declaration:

```gdshader
void fragment() {
    COLOR = vec4(1.0);
}
```

Keep one statement per line and use spaces around operators and after commas.
Preprocessor directives should start at column zero.

## 5. Types and constructors

### 5.1 Scalar types

The principal scalar types are:

- `bool`
- `int`
- `uint`
- `float`

Use explicit suffixes or constructors when the intended type matters:

```gdshader
int count = 4;
uint flags = 1u;
float amount = 4.0;
bool enabled = true;
float converted = float(count);
uint unsigned_count = uint(count);
```

There are no general implicit casts between scalar types. Write the
conversion explicitly.

### 5.2 Vector types

Vector types are:

- `vec2`, `vec3`, `vec4`
- `ivec2`, `ivec3`, `ivec4`
- `uvec2`, `uvec3`, `uvec4`
- `bvec2`, `bvec3`, `bvec4`

Construct vectors from scalars or other vectors:

```gdshader
vec2 uv = vec2(0.5);
vec3 color = vec3(1.0, 0.0, 0.0);
vec4 color_with_alpha = vec4(color, 1.0);
vec3 expanded = vec3(vec2(uv), 0.0);
```

Component aliases:

- position-style: `.x`, `.y`, `.z`, `.w`
- color-style: `.r`, `.g`, `.b`, `.a`

Use the alias appropriate to the value:

```gdshader
float height = position.y;
vec3 rgb = color.rgb;
float alpha = color.a;
```

### 5.3 Matrices

Matrix types include `mat2`, `mat3`, and `mat4`. Matrix indexing is
column-first, then row:

```gdshader
float value = transform[column][row];
```

Constructors:

```gdshader
mat4 identity = mat4(1.0);
mat3 basis = mat3(1.0);
```

Do not assume row-major indexing when translating external GLSL.

### 5.4 Other types

Godot shaders also use:

- `sampler2D`
- `sampler2DArray`
- `sampler3D`
- `samplerCube`
- `samplerCubeArray`
- `samplerExternalOES` on supported renderers/platforms
- `atomic_uint`
- `struct` types
- arrays of supported types

The availability of samplers depends on the renderer and platform.

### 5.5 Uninitialized values

Local variables are not automatically initialized:

```gdshader
float value;
// Reading value here is invalid or undefined.
```

Initialize locals before use:

```gdshader
float value = 0.0;
```

Uniforms and varyings receive initialization from the engine or the pipeline,
but they must still be assigned or read according to the stage rules.

## 6. Variables, constants, uniforms, and varyings

### 6.1 Local and global variables

```gdshader
float global_scale = 1.0;

void fragment() {
    vec3 base_color = vec3(1.0);
    COLOR = vec4(base_color * global_scale, 1.0);
}
```

Avoid mutable global variables unless they are truly shared shader state.

### 6.2 Constants

Constants use `const`:

```gdshader
const float PI_APPROX = 3.14159265;
const vec3 UP_DIRECTION = vec3(0.0, 1.0, 0.0);
```

Constants are compile-time values and cannot be changed at runtime.

### 6.3 Uniforms

Uniforms are values supplied by the material, node, or engine:

```gdshader
uniform float speed;
uniform vec4 tint : source_color;
uniform sampler2D albedo_texture : source_color;
```

A default value may be specified:

```gdshader
uniform float intensity = 1.0;
uniform vec4 fallback_color = vec4(1.0, 0.0, 0.0, 1.0);
```

Uniform arrays can be declared, but uniform arrays cannot have default values:

```gdshader
uniform vec4 palette[8];
```

Structs cannot be declared as uniforms. Flatten a struct into separate
uniforms or use supported uniform arrays.

### 6.4 Uniform hints

Hints follow the type and name, before an optional default:

```gdshader
uniform float threshold : hint_range(0.0, 1.0, 0.01) = 0.5;
uniform int mode : hint_enum("First", "Second", "Third") = 0;
uniform vec4 color : source_color = vec4(1.0);
```

Common hints:

- `hint_range(min, max[, step])`
- `hint_enum("A", "B", ...)`
- `source_color`
- `hint_screen_texture`
- `hint_depth_texture`
- `hint_normal_roughness_texture`
- `hint_default_white`
- `hint_default_black`
- `hint_anisotropy`
- `hint_screen_texture`

Color textures should use `source_color`, especially in Forward+ and Mobile.
The hint tells Godot how to handle color space and material texture input.

Screen and depth textures must use their corresponding hints:

```gdshader
uniform sampler2D screen_texture : hint_screen_texture;
uniform sampler2D depth_texture : hint_depth_texture;
```

The old Godot 3 `SCREEN_TEXTURE` built-in is not the Godot 4 pattern. Declare a
sampler uniform with `hint_screen_texture`.

### 6.5 Global uniforms

Global uniforms are declared in Project Settings first, then referenced in the
shader:

```gdshader
global uniform vec4 environment_tint;
global uniform float world_time;
```

Global uniforms do not have shader-code default values. Their names and types
must match the project settings.

### 6.6 Per-instance uniforms

Per-instance uniforms can be set separately on `CanvasItem` nodes in 2D and
`GeometryInstance3D` nodes in 3D:

```gdshader
instance uniform vec4 instance_tint : source_color = vec4(1.0);
```

Set them with `CanvasItem.set_instance_shader_parameter()` or
`GeometryInstance3D.set_instance_shader_parameter()`. Per-instance uniforms do
not support textures or arrays, and there is a practical limit of 16 per
shader. With multiple materials, keep the uniform name, index, and type
consistent or assign an explicit `instance_index(0)` through
`instance_index(15)`.

### 6.7 Varyings

Varyings transfer values between shader stages:

```gdshader
varying vec3 vertex_world_position;

void vertex() {
    vertex_world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
    ALBEDO = vertex_world_position;
}
```

The value must be written in the producing stage before it is read in the
consuming stage. Varying interpolation is performed by the graphics pipeline.
Use `flat` interpolation where the target stage and renderer support it and
when interpolation must be disabled.

## 7. Functions

Functions have a return type, name, parameter list, and braced body:

```gdshader
float square(float value) {
    return value * value;
}

vec3 saturate_color(vec3 color) {
    return clamp(color, vec3(0.0), vec3(1.0));
}
```

Use `void` for functions with no return value:

```gdshader
void set_default_color() {
    // Write stage outputs in the caller instead when possible.
}
```

Functions can be overloaded by parameter types:

```gdshader
float blend_value(float a, float b) {
    return mix(a, b, 0.5);
}

vec3 blend_value(vec3 a, vec3 b) {
    return mix(a, b, 0.5);
}
```

Avoid overloads that make calls ambiguous. Helper functions must be declared
before use unless the language/compiler accepts the declaration order in the
specific context.

## 8. Control flow

Conditional:

```gdshader
if (amount > 0.5) {
    result = high_value;
} else if (amount > 0.0) {
    result = medium_value;
} else {
    result = low_value;
}
```

Ternary:

```gdshader
float value = enabled ? on_value : off_value;
```

For loop:

```gdshader
for (int index = 0; index < 4; index++) {
    total += values[index];
}
```

While loop:

```gdshader
while (distance > 0.0) {
    distance -= step_size;
}
```

Do-while loop:

```gdshader
do {
    value *= 0.5;
} while (value > 0.01);
```

Switch:

```gdshader
switch (mode) {
    case 0:
        result = first_value;
        break;
    case 1:
        result = second_value;
        break;
    default:
        result = fallback_value;
        break;
}
```

Use `break` to leave loops or switch cases where supported. Avoid data-
dependent unbounded loops because an infinite loop can stall or crash rendering.

Discard a fragment:

```gdshader
if (alpha < 0.01) {
    discard;
}
```

`discard` is only meaningful in fragment-like stages and changes depth,
blending, and performance behavior.

## 9. Structs and arrays

Structs group values:

```gdshader
struct SurfaceData {
    vec3 color;
    float roughness;
};

void fragment() {
    SurfaceData surface;
    surface.color = vec3(1.0);
    surface.roughness = 0.5;
    ALBEDO = surface.color;
    ROUGHNESS = surface.roughness;
}
```

Arrays:

```gdshader
const float WEIGHTS[3] = float[](0.25, 0.5, 0.25);

void fragment() {
    float value = WEIGHTS[1];
    ALBEDO = vec3(value);
}
```

Array indices must remain within bounds. Use compile-time fixed sizes where
possible and avoid dynamically indexing arrays when a renderer or platform
cannot support the resulting shader efficiently.

## 10. Preprocessor

Godot's shader preprocessor supports:

- `#define`
- `#undef`
- `#if`
- `#elif`
- `#else`
- `#endif`
- `#ifdef`
- `#ifndef`
- `#error`
- `#include`
- `#pragma disable_preprocessor`

Directives are not ordinary statements and do not normally end with semicolons.

### 10.1 Defines

```gdshader
#define USE_RIM_LIGHT
#define RIM_POWER 2.0
```

Use a define:

```gdshader
void fragment() {
    vec3 color = ALBEDO;
#ifdef USE_RIM_LIGHT
    color += vec3(0.1);
#endif
    ALBEDO = color;
}
```

Replacement text can contain shader code:

```gdshader
#define MY_COLOR vec3(1.0, 0.0, 0.0)
```

Do not place a semicolon at the end of a macro unless the semicolon should be
inserted at every use. A macro's replacement text is inserted literally.

### 10.2 Conditional compilation

```gdshader
#if CURRENT_RENDERER == RENDERER_COMPATIBILITY
    const float MAX_STEPS = 32.0;
#elif CURRENT_RENDERER == RENDERER_MOBILE
    const float MAX_STEPS = 16.0;
#else
    const float MAX_STEPS = 64.0;
#endif
```

Available renderer defines include:

| Define | Meaning |
| --- | --- |
| `CURRENT_RENDERER` | Numeric identifier for the renderer currently compiling the shader. Compare it with one of the renderer constants below. |
| `RENDERER_COMPATIBILITY` | Numeric constant identifying the Compatibility renderer. |
| `RENDERER_MOBILE` | Numeric constant identifying the Mobile renderer. |
| `RENDERER_FORWARD_PLUS` | Numeric constant identifying the Forward+ renderer. |

Use `#error` to fail compilation with a useful message:

```gdshader
#if MAX_STEPS <= 0
#error MAX_STEPS must be positive
#endif
```

### 10.3 Includes

Include syntax:

```gdshader
#include "res://shaders/fancy_color.gdshaderinc"
```

Relative paths are allowed when the shader is saved as `.gdshader` or the
include is saved as `.gdshaderinc`. Absolute `res://` paths can be used from
shaders embedded in scene or resource files.

Only `.gdshaderinc` resources can be included. A `.gdshader` file cannot
include another `.gdshader`, but an include can include another include.

Restrictions:

- cyclic dependencies are not allowed;
- include depth is limited to 25;
- duplicate declarations and function names are not allowed;
- include code must be valid in the context where it is inserted.

Example include:

```gdshader
// fancy_color.gdshaderinc
vec3 get_fancy_color() {
    return vec3(0.3, 0.6, 0.9);
}
```

Example shader:

```gdshader
shader_type spatial;

#include "res://shaders/fancy_color.gdshaderinc"

void fragment() {
    ALBEDO = get_fancy_color();
}
```

Include global declarations after `shader_type`. Includes inside function
bodies are allowed, but the included code must be valid at that insertion point.

### 10.4 Disabling preprocessing

`#pragma disable_preprocessor` prevents Godot's preprocessing of the file.
Use it only when the source must be passed through without preprocessing and
the target rendering backend supports the resulting code.

## 11. Render modes

Render modes change the pipeline behavior. Use comma-separated modes:

```gdshader
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
```

Only modes supported by the selected shader type are valid.

### 11.1 CanvasItem modes

Common `canvas_item` modes:

- `blend_mix`
- `blend_add`
- `blend_sub`
- `blend_mul`
- `blend_premul_alpha`
- `blend_disabled`
- `unshaded`
- `light_only`
- `skip_vertex_transform`
- `world_vertex_coords`

`skip_vertex_transform` requires manually transforming vertex coordinates.
`world_vertex_coords` changes the coordinate space in which vertex inputs are
provided.

### 11.2 Spatial modes

Blend modes:

- `blend_mix`
- `blend_add`
- `blend_sub`
- `blend_mul`
- `blend_premul_alpha`

Depth modes:

- `depth_draw_opaque`
- `depth_draw_always`
- `depth_draw_never`
- `depth_prepass_alpha`

Depth test modes:

- `depth_test_disabled`
- `depth_test_default`
- `depth_test_inverted`

Culling:

- `cull_back`
- `cull_front`
- `cull_disabled`

Lighting and shading:

- `unshaded`
- `vertex_lighting`
- `specular_disabled`
- `diffuse_lambert`
- `diffuse_lambert_wrap`
- `diffuse_toon`
- `diffuse_burley`
- `specular_schlick_ggx`
- `specular_toon`

Transforms and effects:

- `skip_vertex_transform`
- `world_vertex_coords`
- `ensure_correct_normals` (documented but currently unimplemented)
- `alpha_to_coverage`
- `alpha_to_coverage_and_one`
- `fog_disabled`
- `shadows_disabled`
- `ambient_light_disabled`
- `shadow_to_opacity`
- `particle_trails`
- `wireframe`
- `debug_shadow_splits`

Some stencil modes are experimental. Do not emit them without confirming the
target renderer and engine version.

Important interactions:

- `unshaded` changes lighting behavior.
- `vertex_lighting` can prevent `light()` from running.
- `skip_vertex_transform` means the shader must perform required transforms.
- `world_vertex_coords` changes assumptions about `VERTEX`, `NORMAL`, and
  related inputs.
- depth and alpha modes affect sorting, shadows, and visibility.

### 11.3 Particle modes

Supported particle modes include:

- `keep_data`
- `disable_force`
- `disable_velocity`
- `collision_use_scale`

These change how the particle simulation initializes and updates state.

### 11.4 Sky modes

- `use_half_res_pass`
- `use_quarter_res_pass`
- `disable_fog`

Half- and quarter-resolution passes require the shader to handle the
corresponding pass built-ins.

### 11.5 Texture blit modes

- `blend_mix`
- `blend_add`
- `blend_sub`
- `blend_mul`
- `blend_disabled`

## 12. `canvas_item` shaders

CanvasItem shaders operate on 2D geometry and can implement sprite, UI,
particle, and other CanvasItem effects.

Basic shader:

```gdshader
shader_type canvas_item;

void fragment() {
    COLOR = texture(TEXTURE, UV);
}
```

### 12.1 CanvasItem vertex stage

Common vertex built-ins:

- `MODEL_MATRIX`
- `CANVAS_MATRIX`
- `SCREEN_MATRIX`
- `INSTANCE_ID`
- `INSTANCE_CUSTOM`
- `AT_LIGHT_PASS`
- `TEXTURE_PIXEL_SIZE`
- `VERTEX`
- `VERTEX_ID`
- `UV`
- `COLOR`
- `POINT_SIZE`
- `CUSTOM0`
- `CUSTOM1`
- `CUSTOM2`
- `CUSTOM3`

Example:

```gdshader
shader_type canvas_item;

uniform float wave_strength = 4.0;
uniform float wave_speed = 2.0;

void vertex() {
    VERTEX.y += sin(VERTEX.x * 0.05 + TIME * wave_speed) * wave_strength;
}
```

### 12.2 CanvasItem fragment stage

Common fragment built-ins:

- `FRAGCOORD`
- `SCREEN_PIXEL_SIZE`
- `REGION_RECT`
- `POINT_COORD`
- `TEXTURE`
- `TEXTURE_PIXEL_SIZE`
- `AT_LIGHT_PASS`
- `SPECULAR_SHININESS_TEXTURE`
- `SPECULAR_SHININESS`
- `UV`
- `SCREEN_UV`
- `NORMAL_TEXTURE`
- `NORMAL`
- `NORMAL_MAP`
- `NORMAL_MAP_DEPTH`
- `VERTEX`
- `SHADOW_VERTEX`
- `LIGHT_VERTEX`
- `COLOR`

Texture sampling:

```gdshader
shader_type canvas_item;

void fragment() {
    vec4 source = texture(TEXTURE, UV);
    COLOR = source;
}
```

Screen reading:

```gdshader
shader_type canvas_item;

uniform sampler2D screen_texture : hint_screen_texture, repeat_disable,
        filter_nearest;

void fragment() {
    COLOR = texture(screen_texture, SCREEN_UV);
}
```

The exact sampler hint combination must match the desired filtering and
repetition behavior.

CanvasItem SDF helper functions:

- `texture_sdf(uv)`
- `texture_sdf_normal(uv)`
- `sdf_to_screen_uv(sdf_uv)`
- `screen_uv_to_sdf(screen_uv)`

### 12.3 CanvasItem light stage

Common light built-ins:

- `FRAGCOORD`
- `NORMAL`
- `COLOR`
- `UV`
- `TEXTURE`
- `TEXTURE_PIXEL_SIZE`
- `SCREEN_UV`
- `POINT_COORD`
- `LIGHT_COLOR`
- `LIGHT_ENERGY`
- `LIGHT_POSITION`
- `LIGHT_DIRECTION`
- `LIGHT_IS_DIRECTIONAL`
- `LIGHT_VERTEX`
- `LIGHT`
- `SPECULAR_SHININESS`
- `SHADOW_MODULATE`

Use `light()` only when custom per-light behavior is required. `unshaded` and
`light_only` change whether regular material or light processing contributes.

## 13. `spatial` shaders

Spatial shaders operate on 3D geometry and materials.

Basic shader:

```gdshader
shader_type spatial;

void fragment() {
    ALBEDO = vec3(1.0, 0.0, 0.0);
    ROUGHNESS = 0.5;
}
```

Textured material:

```gdshader
shader_type spatial;

uniform sampler2D albedo_texture : source_color;

void fragment() {
    vec4 sample_color = texture(albedo_texture, UV);
    ALBEDO = sample_color.rgb;
    ALPHA = sample_color.a;
}
```

### 13.1 Spatial global built-ins

Common global values:

- `TIME`
- `PI`
- `TAU`
- `E`
- `OUTPUT_IS_SRGB`
- `CLIP_SPACE_FAR`
- `IS_MULTIVIEW`
- `IN_SHADOW_PASS`

`OUTPUT_IS_SRGB` is `true` in Compatibility and `false` in Forward+ and
Mobile. `CLIP_SPACE_FAR` differs between Compatibility and the other render
methods. Use these values instead of hard-coding renderer assumptions.

### 13.2 Spatial vertex built-ins

Transform and camera values:

- `VIEWPORT_SIZE`
- `VIEW_MATRIX`
- `INV_VIEW_MATRIX`
- `MAIN_CAM_INV_VIEW_MATRIX`
- `INV_PROJECTION_MATRIX`
- `MODELVIEW_MATRIX`
- `MODELVIEW_NORMAL_MATRIX`
- `MODEL_MATRIX`
- `MODEL_NORMAL_MATRIX`
- `PROJECTION_MATRIX`
- `NODE_POSITION_WORLD`
- `NODE_POSITION_VIEW`
- `CAMERA_POSITION_WORLD`
- `CAMERA_DIRECTION_WORLD`
- `CAMERA_VISIBLE_LAYERS`

Geometry and instance values:

- `INSTANCE_ID`
- `INSTANCE_CUSTOM`
- `VIEW_INDEX`
- `VIEW_MONO_LEFT`
- `VIEW_RIGHT`
- `EYE_OFFSET`
- `VERTEX`
- `VERTEX_ID`
- `NORMAL`
- `TANGENT`
- `BINORMAL`
- `POSITION`
- `UV`
- `UV2`
- `COLOR`
- `POINT_SIZE`
- `BONE_INDICES`
- `BONE_WEIGHTS`
- `CUSTOM0`
- `CUSTOM1`
- `CUSTOM2`
- `CUSTOM3`
- `ROUGHNESS`
- `Z_CLIP_SCALE`

Write `POSITION` to override the final clip-space position. Once `POSITION` is
written, the normal automatic projection path is bypassed for that output.

Manual vertex transform:

```gdshader
shader_type spatial;

render_mode skip_vertex_transform;

void vertex() {
    VERTEX = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
}
```

This is an advanced mode. Normals and related vectors may require matching
manual transformation.

### 13.3 Spatial fragment built-ins

Screen, camera, and geometry values:

- `VIEWPORT_SIZE`
- `FRAGCOORD`
- `FRONT_FACING`
- `VIEW`
- `UV`
- `UV2`
- `COLOR`
- `POINT_COORD`
- `VERTEX`
- `LIGHT_VERTEX`
- `VIEW_INDEX`
- `VIEW_MONO_LEFT`
- `VIEW_RIGHT`
- `EYE_OFFSET`
- `MODEL_MATRIX`
- `MODEL_NORMAL_MATRIX`
- `VIEW_MATRIX`
- `INV_VIEW_MATRIX`
- `PROJECTION_MATRIX`
- `INV_PROJECTION_MATRIX`
- `NODE_POSITION_WORLD`
- `NODE_POSITION_VIEW`
- `CAMERA_POSITION_WORLD`
- `CAMERA_DIRECTION_WORLD`
- `CAMERA_VISIBLE_LAYERS`

Normal and depth values:

- `NORMAL`
- `TANGENT`
- `BINORMAL`
- `NORMAL_MAP`
- `NORMAL_MAP_DEPTH`
- `BENT_NORMAL_MAP`
- `DEPTH`

Material outputs:

- `ALBEDO`
- `ALPHA`
- `ALPHA_SCISSOR_THRESHOLD`
- `ALPHA_HASH_SCALE`
- `ALPHA_ANTIALIASING_EDGE`
- `ALPHA_TEXTURE_COORDINATE`
- `PREMUL_ALPHA_FACTOR`
- `METALLIC`
- `SPECULAR`
- `ROUGHNESS`
- `RIM`
- `RIM_TINT`
- `CLEARCOAT`
- `CLEARCOAT_GLOSS`
- `ANISOTROPY`
- `ANISOTROPY_FLOW`
- `SSS_STRENGTH`
- `SSS_TRANSMITTANCE_DEPTH`
- `SSS_TRANSMITTANCE_BOOST`
- `BACKLIGHT`
- `AO`
- `AO_LIGHT_AFFECT`
- `EMISSION`
- `FOG`
- `RADIANCE`
- `IRRADIANCE`
- `SHADOW_TO_OPACITY`

Typical fragment:

```gdshader
shader_type spatial;

uniform vec4 tint : source_color = vec4(1.0);
uniform float metallic : hint_range(0.0, 1.0) = 0.0;
uniform float roughness : hint_range(0.0, 1.0) = 0.5;

void fragment() {
    ALBEDO = tint.rgb;
    METALLIC = metallic;
    ROUGHNESS = roughness;
}
```

### 13.4 Spatial light stage

The `light()` stage receives fragment and lighting values and writes custom
diffuse/specular contributions. Its behavior depends on render modes and the
selected lighting model.

Important light outputs include:

- `DIFFUSE_LIGHT`
- `SPECULAR_LIGHT`

Use the built-in light inputs provided by the spatial shader reference. If
`vertex_lighting` is enabled, `light()` does not run.

### 13.5 Texture sampling and depth

Declare screen and depth textures explicitly:

```gdshader
shader_type spatial;

uniform sampler2D screen_texture : hint_screen_texture;
uniform sampler2D depth_texture : hint_depth_texture;

void fragment() {
    vec3 screen_color = texture(screen_texture, SCREEN_UV).rgb;
    float depth = texture(depth_texture, SCREEN_UV).r;
    ALBEDO = screen_color;
}
```

Use `SCREEN_UV` for screen-space sampling. Do not use `UV` unless the texture
coordinates are intended to come from the mesh.

## 14. `particles` shaders

Particle shaders simulate GPU particles. They do not use `vertex()`,
`fragment()`, or `light()`.

```gdshader
shader_type particles;

void start() {
    VELOCITY = vec3(0.0, 2.0, 0.0);
}

void process() {
    VELOCITY.y -= 9.8 * DELTA;
    TRANSFORM[3].xyz += VELOCITY * DELTA;
}
```

### 14.1 Particle built-ins

Global:

- `TIME`
- `PI`
- `TAU`
- `E`

Simulation:

- `LIFETIME`
- `DELTA`
- `NUMBER`
- `INDEX`
- `EMISSION_TRANSFORM`
- `RANDOM_SEED`
- `ACTIVE`
- `COLOR`
- `VELOCITY`
- `TRANSFORM`
- `CUSTOM`
- `MASS`
- `USERDATA1`
- `USERDATA2`
- `USERDATA3`
- `USERDATA4`
- `USERDATA5`
- `USERDATA6`
- `EMITTER_VELOCITY`
- `INTERPOLATE_TO_END`
- `AMOUNT_RATIO`

Restart values:

- `RESTART`
- `RESTART_POSITION`
- `RESTART_ROT_SCALE`
- `RESTART_VELOCITY`
- `RESTART_COLOR`
- `RESTART_CUSTOM`

Collision values:

- `COLLIDED`
- `COLLISION_NORMAL`
- `COLLISION_DEPTH`
- `ATTRACTOR_FORCE`

Flags:

- `FLAG_EMIT_POSITION`
- `FLAG_EMIT_ROT_SCALE`
- `FLAG_EMIT_VELOCITY`
- `FLAG_EMIT_COLOR`
- `FLAG_EMIT_CUSTOM`

`start()` runs for particle initialization and restart logic. `process()` runs
for ongoing simulation. Use the correct restart built-ins in the correct stage.

Subparticle emission:

```gdshader
emit_subparticle(
    mat4 transform,
    vec3 velocity,
    vec4 color,
    vec4 custom,
    uint flags
);
```

The exact emission flags and parent particle setup must match the particle
system configuration.

## 15. `sky` shaders

Sky shaders render the sky background and can contribute to the radiance
cubemap:

```gdshader
shader_type sky;

void sky() {
    vec3 horizon = vec3(0.1, 0.2, 0.4);
    vec3 zenith = vec3(0.0, 0.0, 0.05);
    float height = EYEDIR.y * 0.5 + 0.5;
    COLOR = mix(horizon, zenith, height);
}
```

Global built-ins:

- `TIME`
- `POSITION`
- `RADIANCE`
- `AT_HALF_RES_PASS`
- `AT_QUARTER_RES_PASS`
- `AT_CUBEMAP_PASS`
- `PI`
- `TAU`
- `E`

Light built-ins are provided for up to four environment lights:

- `LIGHT0`
- `LIGHT1`
- `LIGHT2`
- `LIGHT3`

Each light provides:

- `ENABLED`
- `ENERGY`
- `DIRECTION`
- `COLOR`
- `SIZE`

Sky-stage inputs:

- `EYEDIR`
- `SCREEN_UV`
- `SKY_COORDS`
- `HALF_RES_COLOR`
- `QUARTER_RES_COLOR`

Sky outputs:

- `COLOR`
- `ALPHA`
- `FOG`

Half- and quarter-resolution passes require checking
`AT_HALF_RES_PASS` and `AT_QUARTER_RES_PASS`. Radiance cubemap generation is
identified by `AT_CUBEMAP_PASS`.

## 16. `fog` shaders

Fog shaders operate on volumetric fog:

```gdshader
shader_type fog;

void fog() {
    DENSITY = 0.1;
    ALBEDO = vec3(0.5, 0.6, 0.7);
    EMISSION = vec3(0.0);
}
```

Global built-ins:

- `TIME`
- `PI`
- `TAU`
- `E`

Fog-stage inputs:

- `WORLD_POSITION`
- `OBJECT_POSITION`
- `UVW`
- `SIZE`
- `SDF`

Fog outputs:

- `ALBEDO`
- `DENSITY`
- `EMISSION`

Use `SDF` and object/world coordinates according to the FogVolume setup.
Density and emission values can have a large performance impact.

## 17. `texture_blit` shaders

Texture blit shaders are used by `DrawableTexture2D`:

```gdshader
shader_type texture_blit;

uniform sampler2D source : hint_blit_source0;

void blit() {
    COLOR0 = texture(source, UV);
}
```

This is a special-purpose blit pass, not a general CanvasItem material shader.
Use it only for `DrawableTexture2D` operations and write every output slot the
operation requires.

Source textures use:

- `hint_blit_source0`
- `hint_blit_source1`
- `hint_blit_source2`
- `hint_blit_source3`

Inputs:

- `TIME`
- `PI`
- `TAU`
- `E`
- `FRAGCOORD`
- `UV`
- `MODULATE`

Outputs:

- `COLOR0`
- `COLOR1`
- `COLOR2`
- `COLOR3`

The color outputs default to `(0, 0, 0, 0)`. Write every output that the
destination expects.

## 18. Built-in functions

Godot provides a large set of shader built-in functions. Use the function
signatures and overloads from the target Godot version rather than assuming
desktop GLSL behavior.

Function categories include:

- absolute value and sign: `abs`, `sign`
- trigonometry: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`
- hyperbolic functions: `sinh`, `cosh`, `tanh`, `asinh`, `acosh`, `atanh`
- exponentials and logarithms: `pow`, `exp`, `exp2`, `log`, `log2`
- rounding: `floor`, `ceil`, `round`, `trunc`, `fract`
- clamping and interpolation: `min`, `max`, `clamp`, `mix`, `step`, `smoothstep`
- geometry: `length`, `distance`, `dot`, `cross`, `normalize`, `reflect`,
  `refract`, `faceforward`
- vector operations: `outerProduct`, `matrixCompMult`, `lessThan`,
  `greaterThan`, `equal`, `notEqual`, `any`, `all`, `not`
- derivatives: `dFdx`, `dFdy`, `fwidth`
- texture sampling: `texture`, `textureLod`, `textureGrad`, `textureProj`
- packing and unpacking: packed float and integer helpers
- bit operations: bitwise and bitfield helpers
- interpolation and easing helpers
- signed-distance and screen-space helpers for supported shader types

The named functions in the list above have these purposes:

| Function(s) | Purpose |
| --- | --- |
| `abs` | Returns the component-wise absolute value. |
| `sign` | Returns the sign of each scalar or vector component. |
| `sin`, `cos`, `tan` | Evaluate trigonometric functions in radians. |
| `asin`, `acos`, `atan` | Evaluate inverse trigonometric functions; `atan` also has a two-argument form for quadrant-aware angles. |
| `sinh`, `cosh`, `tanh` | Evaluate hyperbolic trigonometric functions. |
| `asinh`, `acosh`, `atanh` | Evaluate inverse hyperbolic functions. |
| `pow` | Raises a value to a power. |
| `exp`, `exp2` | Compute `e^x` and `2^x`. |
| `log`, `log2` | Compute natural and base-2 logarithms. |
| `floor` | Rounds toward negative infinity. |
| `ceil` | Rounds toward positive infinity. |
| `round` | Rounds to the nearest integral value according to the shader language rules. |
| `trunc` | Removes the fractional part by rounding toward zero. |
| `fract` | Returns the fractional part, equivalent to `x - floor(x)`. |
| `min`, `max` | Select the component-wise minimum or maximum. |
| `clamp` | Restricts a value to an inclusive lower and upper bound. |
| `mix` | Linearly interpolates between two values using a scalar or vector factor. |
| `step` | Returns `0` below an edge and `1` at or above it. |
| `smoothstep` | Performs Hermite-smoothed interpolation between two edges. |
| `length` | Returns the Euclidean length of a vector. |
| `distance` | Returns the Euclidean distance between two points. |
| `dot` | Returns the dot product of two same-sized vectors. |
| `cross` | Returns the 3D cross product of two `vec3` values. |
| `normalize` | Returns a vector with length one; do not pass a zero-length vector. |
| `reflect` | Reflects an incident vector around a normal. |
| `refract` | Computes a refraction direction using an incident vector, normal, and index ratio. |
| `faceforward` | Orients a normal so it faces away from a reference direction. |
| `outerProduct` | Builds a matrix from the outer product of two vectors. |
| `matrixCompMult` | Multiplies matrices component by component rather than using matrix multiplication. |
| `lessThan`, `greaterThan` | Compare vector components and return a boolean vector. |
| `equal`, `notEqual` | Compare scalar or vector components for equality or inequality. |
| `any` | Returns true if any component of a boolean vector is true. |
| `all` | Returns true if every component of a boolean vector is true. |
| `not` | Inverts each component of a boolean vector. |
| `dFdx` | Estimates the screen-space derivative in the x direction; meaningful in fragment-like stages. |
| `dFdy` | Estimates the screen-space derivative in the y direction; meaningful in fragment-like stages. |
| `fwidth` | Returns the sum of the absolute x and y derivatives, useful for analytic antialiasing. |
| `texture` | Samples a texture using implicit derivatives and the sampler's filtering settings. |
| `textureLod` | Samples a texture at an explicitly selected mip level; only valid where the sampler/stage supports explicit LOD. |
| `textureGrad` | Samples a texture using explicitly supplied x and y derivatives. |
| `textureProj` | Performs projective texture sampling by dividing projected coordinates before sampling. |

Packing/unpacking functions convert between floating-point values and packed
integer or vector representations. Bit and bitfield functions operate on
integer bits. Use the exact overloads in the target Godot version; shader
functions are not interchangeable merely because their names resemble CPU or
desktop GLSL functions.

Examples:

```gdshader
float normalized_height = clamp(position.y, 0.0, 1.0);
float edge = smoothstep(0.2, 0.8, normalized_height);
vec3 direction = normalize(target - origin);
float facing = dot(normal, direction);
vec3 reflected = reflect(view_direction, normal);
```

Floating-point equality should normally use an epsilon:

```gdshader
if (abs(value - expected) < 0.0001) {
    // Treat values as equal.
}
```

Texture function choice depends on the sampler type, mipmaps, derivatives,
filtering, and stage. Do not use explicit LOD or gradients without confirming
the stage and texture support.

## 18.1 Complete built-in variable reference

The following tables define the built-in variables named in this guide. Do not
infer semantics from a built-in's name: the same-looking value can have a
different coordinate space, direction, or write behavior in another stage.

`in` means the engine provides the value. `out` means the shader writes it.
`inout` means the shader receives a value and may modify it.

### 18.1.1 Shared global constants

These values are available in the shader types and stages documented below:

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `TIME` | `in float` | Engine time in seconds. It rolls over every 3600 seconds, is affected by `time_scale`, and continues advancing while the game is paused. |
| `PI` | `in float` | Mathematical pi constant. |
| `TAU` | `in float` | One full turn in radians, equal to `2 * PI`. |
| `E` | `in float` | Euler's number, the base of natural logarithms. |

### 18.1.2 CanvasItem global values

CanvasItem uses the shared constants above. Its stage-specific values are:

#### CanvasItem vertex stage

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `MODEL_MATRIX` | `in mat4` | Transforms local CanvasItem coordinates to world coordinates. |
| `CANVAS_MATRIX` | `in mat4` | Transforms world coordinates to canvas coordinates. The canvas origin is at the upper-left and canvas coordinates map to the viewport. |
| `SCREEN_MATRIX` | `in mat4` | Transforms canvas coordinates to clip space, whose range is approximately `(-1, -1)` to `(1, 1)`. |
| `INSTANCE_ID` | `in int` | Identifier of the current rendered instance. |
| `INSTANCE_CUSTOM` | `in vec4` | Per-instance custom data supplied by instancing. |
| `AT_LIGHT_PASS` | `in bool` | Whether the vertex is in a light pass; for CanvasItem vertex processing this is always `false`. |
| `TEXTURE_PIXEL_SIZE` | `in vec2` | Size of one pixel in the default texture, expressed in normalized UV units. |
| `VERTEX` | `inout vec2` | Local-space vertex position in pixels. Modify it for 2D vertex deformation. |
| `VERTEX_ID` | `in int` | Index of the current vertex. |
| `UV` | `inout vec2` | Main normalized texture coordinates, normally in the `0..1` range. |
| `COLOR` | `inout vec4` | Vertex color multiplied by `modulate` and `self_modulate`. |
| `POINT_SIZE` | `inout float` | Point size when the primitive is rendered as points. |
| `CUSTOM0` | `in vec4` | First custom per-vertex channel. |
| `CUSTOM1` | `in vec4` | Second custom per-vertex channel. |
| `CUSTOM2` | `in vec4` | Third custom per-vertex channel. |
| `CUSTOM3` | `in vec4` | Fourth custom per-vertex channel. |
| `ROUGHNESS` | `out float` | Roughness value used by vertex lighting when that path is active. |
| `MODELVIEW_MATRIX` | `inout mat4` | Combined local-to-view transform. Override only when manually controlling the transform. |
| `MODELVIEW_NORMAL_MATRIX` | `inout mat3` | Normal transform corresponding to `MODELVIEW_MATRIX`. |
| `MODEL_NORMAL_MATRIX` | `in mat3` | Normal transform from local/model space to world space. |
| `PROJECTION_MATRIX` | `inout mat4` | View-to-clip transform. Override only when manually controlling projection. |
| `BONE_INDICES` | `in uvec4` | Four skinning bone indices for the current vertex. |
| `BONE_WEIGHTS` | `in vec4` | Four skinning weights corresponding to `BONE_INDICES`. |
| `Z_CLIP_SCALE` | `out float` | Scales a vertex toward the camera to reduce wall clipping; changing it can harm SSAO and SSR. |

#### CanvasItem fragment stage

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `VIEWPORT_SIZE` | `in vec2` | Viewport width and height in pixels. |
| `SCREEN_PIXEL_SIZE` | `in vec2` | Size of one screen pixel in normalized screen coordinates. |
| `FRAGCOORD` | `in vec4` | Current fragment center in screen space; `z` contains fragment depth unless custom depth is written. |
| `FRONT_FACING` | `in bool` | Whether the fragment belongs to a front-facing primitive. |
| `VIEW` | `in vec3` | Normalized vector from the fragment toward the camera in view space. |
| `UV` | `in vec2` | Interpolated main texture coordinate. |
| `UV2` | `in vec2` | Interpolated secondary texture coordinate. |
| `COLOR` | `inout vec4` | Interpolated vertex color, multiplied by the default texture when applicable; also the final CanvasItem color output. |
| `POINT_COORD` | `in vec2` | Coordinates within a point primitive. |
| `MODEL_MATRIX` | `in mat4` | Local-to-world transform for the current item. |
| `MODEL_NORMAL_MATRIX` | `in mat3` | Normal transform for the current item. |
| `VIEW_MATRIX` | `in mat4` | World-to-view transform. |
| `INV_VIEW_MATRIX` | `in mat4` | View-to-world transform. |
| `PROJECTION_MATRIX` | `in mat4` | View-to-clip transform. |
| `INV_PROJECTION_MATRIX` | `in mat4` | Clip-to-view transform. |
| `NODE_POSITION_WORLD` | `in vec3` | Current node origin in world space. |
| `NODE_POSITION_VIEW` | `in vec3` | Current node origin in view space. |
| `CAMERA_POSITION_WORLD` | `in vec3` | Camera position in world space; in multiview it is the midpoint of the eyes. |
| `CAMERA_DIRECTION_WORLD` | `in vec3` | Camera forward direction in world space. |
| `CAMERA_VISIBLE_LAYERS` | `in uint` | Bitmask of layers visible to the camera. |
| `VERTEX` | `in vec3` | Interpolated fragment position. Its exact space depends on the vertex transform mode. |
| `LIGHT_VERTEX` | `inout vec3` | Fragment position used for light and shadow calculations; modifying it affects lighting, not the visible geometry position. |
| `REGION_RECT` | `in vec4` | Rectangle of the CanvasItem texture region being rendered. |
| `AT_LIGHT_PASS` | `in bool` | Whether the fragment is being processed for a light pass. |
| `VIEW_INDEX` | `in int` | Current multiview eye index. |
| `VIEW_MONO_LEFT` | `in int` | Constant identifying the mono/left view, currently `0`. |
| `VIEW_RIGHT` | `in int` | Constant identifying the right view, currently `1`. |
| `EYE_OFFSET` | `in vec3` | Current eye offset in view space; meaningful in multiview. |
| `SCREEN_UV` | `in vec2` | Normalized screen coordinate for sampling the current viewport. |
| `TEXTURE` | `sampler2D` | Default CanvasItem texture sampler. |
| `TEXTURE_PIXEL_SIZE` | `in vec2` | One default-texture pixel expressed in normalized UV units. |
| `SCREEN_TEXTURE` | removed | Do not use the old Godot 3 built-in; declare a sampler with `hint_screen_texture`. |
| `DEPTH_TEXTURE` | removed | Do not use the old Godot 3 built-in; declare a sampler with `hint_depth_texture`. |
| `DEPTH` | `out float` | Optional custom depth value in the renderer's normalized depth range. If written, every control-flow path must write it. |
| `NORMAL_TEXTURE` | sampler/input | Default normal texture associated with the CanvasItem. |
| `NORMAL` | `inout vec3` | Normal value used by CanvasItem lighting. |
| `NORMAL_MAP` | `out vec3` | Tangent-space normal-map value supplied to the lighting pipeline. |
| `NORMAL_MAP_DEPTH` | `out float` | Depth/strength associated with `NORMAL_MAP`. |
| `SHADOW_VERTEX` | `inout vec3` | Vertex position used for shadow calculations. |
| `SPECULAR_SHININESS_TEXTURE` | sampler/input | Texture supplying per-pixel specular shininess. |
| `SPECULAR_SHININESS` | `in vec4` | Specular shininess data used by the CanvasItem light stage. |
| `ALBEDO` | `out vec3` | Base color contribution for the material-style CanvasItem lighting path. |
| `ALPHA` | `out float` | Alpha contribution for the material-style path. |
| `ALPHA_SCISSOR_THRESHOLD` | `out float` | Discards fragments whose alpha is below this threshold. |
| `ALPHA_HASH_SCALE` | `out float` | Scales alpha-hash transparency when that transparency mode is active. |
| `ALPHA_ANTIALIASING_EDGE` | `out float` | Alpha-to-coverage edge value; requires the matching render mode. |
| `ALPHA_TEXTURE_COORDINATE` | `out vec2` | Texture coordinate used by alpha-to-coverage processing. |
| `PREMUL_ALPHA_FACTOR` | `out float` | Controls premultiplied-alpha processing; effective with `blend_premul_alpha`. |
| `METALLIC` | `out float` | Metallic material factor for the material-style lighting path. |
| `SPECULAR` | `out float` | Specular material factor. A value of `0.0` disables reflections in the relevant path. |
| `ROUGHNESS` | `out float` | Surface roughness for lighting. |
| `RIM` | `out float` | Rim-light intensity. |
| `RIM_TINT` | `out float` | Tint factor for rim lighting. |
| `CLEARCOAT` | `out float` | Clearcoat layer strength. |
| `CLEARCOAT_GLOSS` | `out float` | Clearcoat gloss/roughness control. |
| `ANISOTROPY` | `out float` | Anisotropic reflection strength. |
| `ANISOTROPY_FLOW` | `out vec2` | Direction of anisotropic flow. |
| `SSS_STRENGTH` | `out float` | Subsurface-scattering strength. |
| `SSS_TRANSMITTANCE_COLOR` | `out vec4` | Color used for subsurface transmittance. |
| `SSS_TRANSMITTANCE_DEPTH` | `out float` | Depth scale for subsurface transmittance. |
| `SSS_TRANSMITTANCE_BOOST` | `out float` | Boost applied to subsurface transmittance. |
| `BACKLIGHT` | `inout vec3` | Backlight contribution used by the lighting path. |
| `AO` | `out float` | Ambient-occlusion factor. |
| `AO_LIGHT_AFFECT` | `out float` | How strongly ambient occlusion affects direct light. |
| `EMISSION` | `out vec3` | Emissive color added independently of ordinary lighting. |
| `FOG` | `out vec4` | Custom fog blend; the alpha component controls how strongly it blends. |
| `RADIANCE` | `out vec4` | Custom environment-radiance blend; alpha controls its blend amount. |
| `IRRADIANCE` | `out vec4` | Custom environment-irradiance blend; alpha controls its blend amount. |

#### CanvasItem light stage

`light()` runs once per affecting light. The `unshaded` render mode disables
CanvasItem lighting. The `vertex_lighting` and Force Vertex Shading caveats
apply to spatial shaders, not CanvasItem shaders.

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `FRAGCOORD` | `in vec4` | Current fragment center in screen space. |
| `NORMAL` | `in vec3` | Normal used for this light calculation. |
| `COLOR` | `in vec4` | Color output from the fragment stage entering the light pass. |
| `UV` | `in vec2` | Interpolated texture coordinate. |
| `TEXTURE` | `sampler2D` | Default CanvasItem texture. |
| `TEXTURE_PIXEL_SIZE` | `in vec2` | Default texture pixel size in UV units. |
| `SCREEN_UV` | `in vec2` | Normalized screen coordinate. |
| `POINT_COORD` | `in vec2` | Coordinates within a point primitive. |
| `LIGHT_COLOR` | `in vec4` | Current light color. |
| `LIGHT_ENERGY` | `in float` | Current light energy multiplier. |
| `LIGHT_POSITION` | `in vec3` | Light position in screen space; `(0, 0, 0)` for a directional light. |
| `LIGHT_DIRECTION` | `in vec3` | Direction from the light system for the current light. |
| `LIGHT_IS_DIRECTIONAL` | `in bool` | Whether the current light is directional. |
| `LIGHT_VERTEX` | `in vec3` | Fragment position after any fragment-stage light-position adjustment. |
| `LIGHT` | `inout vec4` | Color contribution for the current light; write the custom result here. |
| `SPECULAR_SHININESS` | `in vec4` | Specular shininess data from the fragment/material path. |
| `SHADOW_MODULATE` | `out vec4` | Modulation applied to the shadowed light contribution. |

CanvasItem signed-distance helpers:

| Function | Meaning |
| --- | --- |
| `texture_sdf(uv)` | Samples the CanvasItem signed-distance field at the supplied SDF coordinate. |
| `texture_sdf_normal(uv)` | Computes a normal from the CanvasItem signed-distance field. |
| `sdf_to_screen_uv(sdf_uv)` | Converts SDF coordinates to normalized screen UV coordinates. |
| `screen_uv_to_sdf(screen_uv)` | Converts normalized screen UV coordinates to SDF coordinates. |

### 18.1.3 Spatial global values

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `OUTPUT_IS_SRGB` | `in bool` | `true` in Compatibility and `false` in Forward+ and Mobile; indicates the output color-space convention. |
| `CLIP_SPACE_FAR` | `in float` | Far-plane clip-space depth: `-1.0` in Compatibility and `0.0` in Forward+/Mobile. |
| `IS_MULTIVIEW` | `in bool` | Whether the current render is stereo/multiview. |
| `IN_SHADOW_PASS` | `in bool` | Whether the shader is currently rendering a shadow-map pass. |

`TIME`, `PI`, `TAU`, and `E` have the shared meanings in the global table.

#### Spatial vertex stage

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `VIEWPORT_SIZE` | `in vec2` | Viewport dimensions in pixels. |
| `VIEW_MATRIX` | `in mat4` | World-to-view transform. |
| `INV_VIEW_MATRIX` | `in mat4` | View-to-world transform. |
| `MAIN_CAM_INV_VIEW_MATRIX` | `in mat4` | Main camera view-to-world transform, useful when rendering from another view. |
| `INV_PROJECTION_MATRIX` | `in mat4` | Clip-to-view transform. |
| `NODE_POSITION_WORLD` | `in vec3` | Node origin in world space. |
| `NODE_POSITION_VIEW` | `in vec3` | Node origin in view space. |
| `CAMERA_POSITION_WORLD` | `in vec3` | Camera world position; midpoint of the eyes in multiview. |
| `CAMERA_DIRECTION_WORLD` | `in vec3` | Camera forward direction in world space. |
| `CAMERA_VISIBLE_LAYERS` | `in uint` | Camera cull-layer bitmask. |
| `INSTANCE_ID` | `in int` | Current instance identifier. |
| `INSTANCE_CUSTOM` | `in vec4` | Custom per-instance data. |
| `VIEW_INDEX` | `in int` | Current multiview eye index. |
| `VIEW_MONO_LEFT` | `in int` | Constant for the mono/left view, currently `0`. |
| `VIEW_RIGHT` | `in int` | Constant for the right view, currently `1`. |
| `EYE_OFFSET` | `in vec3` | Current eye offset in view space; meaningful only for multiview. |
| `VERTEX` | `inout vec3` | Vertex position, normally in model space; in world space with `world_vertex_coords`. |
| `VERTEX_ID` | `in int` | Current vertex index. |
| `NORMAL` | `inout vec3` | Vertex normal in model or world space according to the transform mode. |
| `TANGENT` | `inout vec3` | Vertex tangent in model or world space according to the transform mode. |
| `BINORMAL` | `inout vec3` | Vertex binormal in model or world space according to the transform mode. |
| `POSITION` | `out vec4` | Optional final clip-space position override; writing it bypasses normal projection of `VERTEX`. |
| `UV` | `inout vec2` | Main mesh UV coordinate. |
| `UV2` | `inout vec2` | Secondary mesh UV coordinate. |
| `COLOR` | `inout vec4` | Vertex color, normally in the `0..1` range per channel. |
| `POINT_SIZE` | `inout float` | Point size for point primitives. |
| `MODELVIEW_MATRIX` | `inout mat4` | Model-to-view transform; override for custom vertex transforms. |
| `MODELVIEW_NORMAL_MATRIX` | `inout mat3` | Normal transform matching `MODELVIEW_MATRIX`. |
| `MODEL_MATRIX` | `in mat4` | Model-to-world transform. |
| `MODEL_NORMAL_MATRIX` | `in mat3` | Model-to-world normal transform. |
| `PROJECTION_MATRIX` | `inout mat4` | View-to-clip transform; override for custom projection. |
| `BONE_INDICES` | `in uvec4` | Four skinning bone indices. |
| `BONE_WEIGHTS` | `in vec4` | Four skinning weights matching `BONE_INDICES`. |
| `CUSTOM0` | `in vec4` | First custom vertex channel. |
| `CUSTOM1` | `in vec4` | Second custom vertex channel. |
| `CUSTOM2` | `in vec4` | Third custom vertex channel. |
| `CUSTOM3` | `in vec4` | Fourth custom vertex channel. |
| `ROUGHNESS` | `out float` | Roughness passed to vertex-lighting calculations. |
| `Z_CLIP_SCALE` | `out float` | Camera-directed vertex scaling intended to reduce wall clipping; can reduce SSAO/SSR quality. |

`skip_vertex_transform` requires manual transformation of position and any
related vectors. `world_vertex_coords` changes the input space of
`VERTEX`, `NORMAL`, `TANGENT`, and `BINORMAL`.

#### Spatial fragment stage

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `VIEWPORT_SIZE` | `in vec2` | Viewport dimensions in pixels. |
| `FRAGCOORD` | `in vec4` | Fragment center in screen space; `z` is depth unless `DEPTH` is written. |
| `FRONT_FACING` | `in bool` | Whether the fragment is front-facing. |
| `VIEW` | `in vec3` | Normalized fragment-to-camera vector in view space. |
| `UV` | `in vec2` | Interpolated main mesh UV. |
| `UV2` | `in vec2` | Interpolated secondary mesh UV. |
| `COLOR` | `in vec4` | Interpolated vertex color. |
| `POINT_COORD` | `in vec2` | Coordinates within a point primitive. |
| `MODEL_MATRIX` | `in mat4` | Model-to-world transform. |
| `MODEL_NORMAL_MATRIX` | `in mat3` | Model-to-world normal transform; accounts for non-uniform scale. |
| `VIEW_MATRIX` | `in mat4` | World-to-view transform. |
| `INV_VIEW_MATRIX` | `in mat4` | View-to-world transform. |
| `PROJECTION_MATRIX` | `in mat4` | View-to-clip transform. |
| `INV_PROJECTION_MATRIX` | `in mat4` | Clip-to-view transform. |
| `NODE_POSITION_WORLD` | `in vec3` | Node origin in world space. |
| `NODE_POSITION_VIEW` | `in vec3` | Node origin in view space. |
| `CAMERA_POSITION_WORLD` | `in vec3` | Camera world position, or eye midpoint in multiview. |
| `CAMERA_DIRECTION_WORLD` | `in vec3` | Camera forward direction in world space. |
| `CAMERA_VISIBLE_LAYERS` | `in uint` | Camera cull-layer bitmask. |
| `VERTEX` | `in vec3` | Interpolated fragment position in view space, unless transform modes change it. |
| `LIGHT_VERTEX` | `inout vec3` | Position used for lighting and shadows; changing it does not move the visible fragment. |
| `VIEW_INDEX` | `in int` | Current multiview eye index. |
| `VIEW_MONO_LEFT` | `in int` | Constant for mono/left view, currently `0`. |
| `VIEW_RIGHT` | `in int` | Constant for right view, currently `1`. |
| `EYE_OFFSET` | `in vec3` | Current eye offset in view space. |
| `SCREEN_UV` | `in vec2` | Normalized screen coordinate. |
| `DEPTH` | `out float` | Custom normalized depth. If written on any path, every path must write it. |
| `NORMAL` | `inout vec3` | Surface normal, normally in view space. |
| `TANGENT` | `inout vec3` | Surface tangent, normally in view space. |
| `BINORMAL` | `inout vec3` | Surface binormal, normally in view space. |
| `NORMAL_MAP` | `out vec3` | Tangent-space normal-map value; the engine reconstructs the blue component as needed. |
| `NORMAL_MAP_DEPTH` | `out float` | Strength/depth associated with `NORMAL_MAP`. |
| `BENT_NORMAL_MAP` | `out vec3` | Tangent-space bent normal used by supported ambient-lighting paths. |
| `ALBEDO` | `out vec3` | Base surface color. |
| `ALPHA` | `out float` | Surface opacity; writing it routes the material through the transparent pipeline. |
| `ALPHA_SCISSOR_THRESHOLD` | `out float` | Discards fragments whose alpha is below this value. |
| `ALPHA_HASH_SCALE` | `out float` | Scale for alpha-hash transparency. |
| `ALPHA_ANTIALIASING_EDGE` | `out float` | Alpha-to-coverage edge; requires `alpha_to_coverage` and should be below the scissor threshold. |
| `ALPHA_TEXTURE_COORDINATE` | `out vec2` | Texture coordinate used by alpha-to-coverage. |
| `PREMUL_ALPHA_FACTOR` | `out float` | Factor used with `blend_premul_alpha`. |
| `METALLIC` | `out float` | Metallic surface factor. |
| `SPECULAR` | `out float` | Specular reflection factor; `0.0` disables reflections in the relevant path. |
| `ROUGHNESS` | `out float` | Surface roughness. |
| `RIM` | `out float` | Rim-light intensity. |
| `RIM_TINT` | `out float` | Rim-light tint factor. |
| `CLEARCOAT` | `out float` | Clearcoat layer strength. |
| `CLEARCOAT_GLOSS` | `out float` | Clearcoat gloss control. |
| `ANISOTROPY` | `out float` | Anisotropic reflection strength. |
| `ANISOTROPY_FLOW` | `out vec2` | Anisotropy direction/flow. |
| `SSS_STRENGTH` | `out float` | Subsurface-scattering strength. |
| `SSS_TRANSMITTANCE_COLOR` | `out vec4` | Subsurface transmittance color. |
| `SSS_TRANSMITTANCE_DEPTH` | `out float` | Subsurface transmittance depth. |
| `SSS_TRANSMITTANCE_BOOST` | `out float` | Subsurface transmittance boost. |
| `BACKLIGHT` | `inout vec3` | Backlight contribution. |
| `AO` | `out float` | Ambient-occlusion factor. |
| `AO_LIGHT_AFFECT` | `out float` | Amount by which AO affects direct light. |
| `EMISSION` | `out vec3` | Emissive color independent of direct lighting. |
| `FOG` | `out vec4` | Custom fog color and blend amount; alpha controls blending. |
| `RADIANCE` | `out vec4` | Custom environment radiance and blend amount. |
| `IRRADIANCE` | `out vec4` | Custom environment irradiance and blend amount. |
| `SHADOW_TO_OPACITY` | `out float` | Shadow-to-opacity contribution for supported shadow-to-opacity rendering. |

Transparent spatial materials cannot cast shadows or use screen/depth texture
sampling in the same way as opaque materials. Alpha and depth modes must be
chosen together.

#### Spatial light stage

`light()` runs once per affecting light per pixel. It is ignored when
`vertex_lighting` is enabled or when the project uses Force Vertex Shading.

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `VIEWPORT_SIZE` | `in vec2` | Viewport dimensions in pixels. |
| `FRAGCOORD` | `in vec4` | Current fragment center and depth. |
| `MODEL_MATRIX` | `in mat4` | Model-to-world transform. |
| `VIEW_MATRIX` | `in mat4` | World-to-view transform. |
| `INV_VIEW_MATRIX` | `in mat4` | View-to-world transform. |
| `PROJECTION_MATRIX` | `in mat4` | View-to-clip transform. |
| `INV_PROJECTION_MATRIX` | `in mat4` | Clip-to-view transform. |
| `NORMAL` | `in vec3` | Surface normal for this light evaluation. |
| `SCREEN_UV` | `in vec2` | Normalized screen coordinate. |
| `UV` | `in vec2` | Main mesh UV. |
| `UV2` | `in vec2` | Secondary mesh UV. |
| `VIEW` | `in vec3` | Fragment-to-camera vector in view space. |
| `LIGHT` | `in vec3` | Light direction/vector in view space. |
| `LIGHT_COLOR` | `in vec3` | Light color multiplied by energy and `PI`. |
| `SPECULAR_AMOUNT` | `in float` | Specular scale: `2.0 * light_specular` for omni/spot lights and `1.0` for directional lights. |
| `LIGHT_IS_DIRECTIONAL` | `in bool` | Whether the current light is directional. |
| `ATTENUATION` | `in float` | Combined light attenuation factor. |
| `ALBEDO` | `in vec3` | Surface base color from the fragment stage. |
| `BACKLIGHT` | `in vec3` | Backlight contribution from the fragment stage. |
| `METALLIC` | `in float` | Surface metallic factor. |
| `ROUGHNESS` | `in float` | Surface roughness factor. |
| `DIFFUSE_LIGHT` | `out vec3` | Custom diffuse-light contribution. |
| `SPECULAR_LIGHT` | `out vec3` | Custom specular-light contribution. |
| `ALPHA` | `out float` | Alpha output for the light pass. |

### 18.1.4 Particle values

`start()` initializes particles. `process()` updates them every simulation
step. Values marked start-only or process-only must not be assumed valid in the
other stage.

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `LIFETIME` | `in float` | Total lifetime of the particle in seconds. |
| `DELTA` | `in float` | Elapsed simulation time for the current process step. |
| `NUMBER` | `in uint` | Unique emission number for the particle. |
| `INDEX` | `in uint` | Index of the particle in the particle buffer. |
| `EMISSION_TRANSFORM` | `in mat4` | Emitter transform used for non-local particle systems. |
| `RANDOM_SEED` | `in uint` | Per-particle random seed. |
| `USERDATA1` | `in vec4` | First user data channel supplied by the particle system. |
| `USERDATA2` | `in vec4` | Second user data channel. |
| `USERDATA3` | `in vec4` | Third user data channel. |
| `USERDATA4` | `in vec4` | Fourth user data channel. |
| `USERDATA5` | `in vec4` | Fifth user data channel. |
| `USERDATA6` | `in vec4` | Sixth user data channel. |
| `FLAG_EMIT_POSITION` | `in uint` | Flag passed to `emit_subparticle()` to emit position data. |
| `FLAG_EMIT_ROT_SCALE` | `in uint` | Flag passed to `emit_subparticle()` to emit rotation/scale data. |
| `FLAG_EMIT_VELOCITY` | `in uint` | Flag passed to `emit_subparticle()` to emit velocity data. |
| `FLAG_EMIT_COLOR` | `in uint` | Flag passed to `emit_subparticle()` to emit color data. |
| `FLAG_EMIT_CUSTOM` | `in uint` | Flag passed to `emit_subparticle()` to emit custom data. |
| `EMITTER_VELOCITY` | `in vec3` | Velocity of the particle emitter. |
| `INTERPOLATE_TO_END` | `in float` | Interpolation factor used by particle interpolation. |
| `AMOUNT_RATIO` | `in uint` | Particle amount ratio supplied by the system. |
| `RESTART_POSITION` | `in bool` | In `start()`, indicates that the position should be initialized or reset. |
| `RESTART_ROT_SCALE` | `in bool` | In `start()`, indicates that rotation/scale should be initialized or reset. |
| `RESTART_VELOCITY` | `in bool` | In `start()`, indicates that velocity should be initialized or reset. |
| `RESTART_COLOR` | `in bool` | In `start()`, indicates that color should be initialized or reset. |
| `RESTART_CUSTOM` | `in bool` | In `start()`, indicates that custom data should be initialized or reset. |
| `RESTART` | `in bool` | In `process()`, indicates the first process frame after restart. |
| `COLLIDED` | `in bool` | Whether the particle collided during the current step. |
| `COLLISION_NORMAL` | `in vec3` | Normal of the latest particle collision. |
| `COLLISION_DEPTH` | `in float` | Penetration/collision depth. |
| `ATTRACTOR_FORCE` | `in vec3` | Force contributed by particle attractors. |
| `ACTIVE` | `inout bool` | Whether the particle remains active. Set false to deactivate it. |
| `COLOR` | `inout vec4` | Particle color state. |
| `VELOCITY` | `inout vec3` | Particle velocity in the simulation's coordinate space. |
| `TRANSFORM` | `inout mat4` | Particle transform; translation is commonly `TRANSFORM[3].xyz`. |
| `CUSTOM` | `inout vec4` | Particle custom data passed to the draw process. |
| `MASS` | `inout float` | Particle mass, defaulting to `1.0`. |

Particle helper:

| Function | Meaning |
| --- | --- |
| `emit_subparticle(xform, velocity, color, custom, flags)` | Emits a subparticle and returns whether emission succeeded; `flags` selects which supplied fields are valid. |

### 18.1.5 Sky values

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `POSITION` | `in vec3` | Camera position in world space. |
| `RADIANCE` | `samplerCube` | Environment radiance cubemap; readable in the background pass, not during the cubemap pass. |
| `AT_HALF_RES_PASS` | `in bool` | True while rendering the optional half-resolution sky pass. |
| `AT_QUARTER_RES_PASS` | `in bool` | True while rendering the optional quarter-resolution sky pass. |
| `AT_CUBEMAP_PASS` | `in bool` | True while generating the radiance cubemap. |
| `EYEDIR` | `in vec3` | Normalized direction from the camera through the current sky pixel. |
| `SCREEN_UV` | `in vec2` | Normalized screen coordinate. |
| `SKY_COORDS` | `in vec2` | Spherical UV coordinates for the sky. |
| `HALF_RES_COLOR` | `in vec4` | Color produced by the half-resolution pass. |
| `QUARTER_RES_COLOR` | `in vec4` | Color produced by the quarter-resolution pass. |
| `COLOR` | `out vec3` | Sky color output. |
| `ALPHA` | `out float` | Sky alpha output, meaningful in subpasses. |
| `FOG` | `out vec4` | Sky fog color and blend amount. |

Sky light groups are named `LIGHT0` through `LIGHT3`; each group has:

| Built-in pattern | Direction/type | Meaning |
| --- | --- | --- |
| `LIGHT0` through `LIGHT3` | property-group prefix | Selects one of the four environment-light groups; use the suffixed properties below rather than reading the prefix by itself. |
| `LIGHT0_ENABLED` through `LIGHT3_ENABLED` | `in bool` | Whether that environment light is enabled. If false, its other values may be undefined and must not be read. |
| `LIGHT0_ENERGY` through `LIGHT3_ENERGY` | `in float` | Light energy. |
| `LIGHT0_DIRECTION` through `LIGHT3_DIRECTION` | `in vec3` | Light direction in world space. |
| `LIGHT0_COLOR` through `LIGHT3_COLOR` | `in vec3` | Light color. |
| `LIGHT0_SIZE` through `LIGHT3_SIZE` | `in float` | Angular diameter of the light in radians. |

Use the pass flags before reading `RADIANCE`, half-resolution, or quarter-
resolution values. `use_half_res_pass` and `use_quarter_res_pass` enable the
corresponding passes.

### 18.1.6 Fog values

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `WORLD_POSITION` | `in vec3` | World position of the current froxel/cell. |
| `OBJECT_POSITION` | `in vec3` | FogVolume center in world space. |
| `UVW` | `in vec3` | Three-dimensional normalized coordinate within the FogVolume. |
| `SIZE` | `in vec3` | FogVolume size when the selected shape has a size. |
| `SDF` | `in vec3` | Signed distance information for the FogVolume surface; negative values are inside. |
| `ALBEDO` | `out vec3` | Color of the fog volume. |
| `DENSITY` | `out float` | Fog density. It must be written for the shader to affect fog; negative values can subtract fog. |
| `EMISSION` | `out vec3` | Emissive fog color. |

### 18.1.7 Texture blit values

| Built-in | Direction/type | Meaning |
| --- | --- | --- |
| `FRAGCOORD` | `in vec4` | Current pixel center in screen space. |
| `UV` | `in vec2` | Coordinates intended to sample the complete source texture. |
| `MODULATE` | `in vec4` | Modulation value supplied by the RenderingServer. |
| `COLOR0` | `out vec4` | First output target; initialized to `(0, 0, 0, 0)`. |
| `COLOR1` | `out vec4` | Second output target; initialized to `(0, 0, 0, 0)`. |
| `COLOR2` | `out vec4` | Third output target; initialized to `(0, 0, 0, 0)`. |
| `COLOR3` | `out vec4` | Fourth output target; initialized to `(0, 0, 0, 0)`. |

Declare source samplers with these hints:

| Hint | Meaning |
| --- | --- |
| `hint_blit_source0` | Binds the first source texture. |
| `hint_blit_source1` | Binds the second source texture. |
| `hint_blit_source2` | Binds the third source texture. |
| `hint_blit_source3` | Binds the fourth source texture. |

## 19. Coordinate spaces and transforms

Shaders commonly work in several spaces:

- local/model space
- world space
- view/camera space
- clip space
- screen space
- UV/texture space

Do not mix them without an explicit transform. For spatial shaders:

```gdshader
vec3 world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
vec3 view_position = (VIEW_MATRIX * vec4(world_position, 1.0)).xyz;
```

Godot automatically transforms vertices unless a render mode disables the
automatic path. `skip_vertex_transform` and `world_vertex_coords` change the
meaning of the inputs and require corresponding code changes.

`POSITION` in a spatial vertex shader is a clip-space override. Writing it
bypasses the normal projection path for that output.

Screen-space values use screen coordinates and `SCREEN_UV`, not mesh UVs.
Depth values are renderer-dependent; use `INV_PROJECTION_MATRIX` and the
documented clip-space constants when reconstructing positions.

## 20. Color space and renderer portability

Color texture uniforms should normally use:

```gdshader
uniform sampler2D color_texture : source_color;
```

The render method affects color handling:

- Compatibility uses an sRGB output path in relevant cases.
- Forward+ and Mobile generally use linear shader calculations and differ in
  output handling.

Use `OUTPUT_IS_SRGB` where a shader must branch on output color space. Avoid
hard-coded assumptions about gamma conversion.

Renderer-specific features include:

- `samplerCubeArray` only on supported Forward+ and Mobile paths.
- `samplerExternalOES` only on supported Compatibility/Android paths.
- normal-roughness screen textures only where supported.
- different clip-space far-plane conventions.
- different precision and feature support on mobile hardware.

Use preprocessor renderer defines when one shader must support multiple paths.

## 21. GLSL conversion rules

When converting GLSL:

| GLSL concept | Godot shader equivalent |
| --- | --- |
| `main()` vertex function | `vertex()` |
| `main()` fragment function | `fragment()` |
| `gl_FragColor` | `COLOR` |
| `gl_FragCoord` | `FRAGCOORD` |
| `gl_Position` | `VERTEX` or `POSITION`, depending on stage and intent |
| custom uniform | same uniform declaration, with Godot hints as needed |
| `#include` | Godot `.gdshaderinc` include |

Godot may already apply model, view, and projection transforms. Do not copy
GLSL transform code blindly. First determine whether the corresponding Godot
render mode disables the automatic transform.

Common conversion problems:

- GLSL `main` must be replaced with the correct Godot stage function.
- `gl_FragColor` must be replaced by the output appropriate to the shader type.
- screen texture built-ins changed in Godot 4; declare a hinted sampler.
- `UV.y` orientation may differ from a screen-space GLSL assumption.
- Shadertoy uniforms such as time, resolution, and mouse are not automatically
  available; declare and populate equivalent uniforms.
- GLSL precision qualifiers become per-variable precision qualifiers.
- external GLSL functions may have incompatible overloads or types.
- desktop GLSL extensions may not be available in Godot's shader language.

## 22. Precision

Precision qualifiers include:

- `lowp`
- `mediump`
- `highp`

Example:

```gdshader
mediump float value = 0.5;
highp vec3 position = vec3(0.0);
```

Mobile precision can be driver-sensitive. Use the minimum precision that
preserves the effect, but use `highp` for values such as world positions,
depth reconstruction, and long iterative calculations when required.

## 23. Complete templates

### 23.1 CanvasItem texture shader

```gdshader
shader_type canvas_item;

render_mode blend_mix;

uniform sampler2D source_texture : source_color;
uniform vec4 tint : source_color = vec4(1.0);

void fragment() {
    vec4 source = texture(source_texture, UV);
    COLOR = source * tint;
}
```

### 23.2 Spatial textured shader

```gdshader
shader_type spatial;

render_mode cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_texture : source_color;
uniform float roughness : hint_range(0.0, 1.0) = 0.5;

void fragment() {
    vec4 source = texture(albedo_texture, UV);
    ALBEDO = source.rgb;
    ALPHA = source.a;
    ROUGHNESS = roughness;
}
```

### 23.3 Spatial vertex displacement

```gdshader
shader_type spatial;

uniform sampler2D height_texture;
uniform float displacement_strength = 0.1;

void vertex() {
    float height = texture(height_texture, UV).r;
    VERTEX += NORMAL * height * displacement_strength;
}
```

### 23.4 Particle simulation

```gdshader
shader_type particles;

uniform vec3 acceleration = vec3(0.0, -9.8, 0.0);

void start() {
    VELOCITY = vec3(0.0, 1.0, 0.0);
}

void process() {
    VELOCITY += acceleration * DELTA;
    TRANSFORM[3].xyz += VELOCITY * DELTA;
}
```

### 23.5 Sky gradient

```gdshader
shader_type sky;

uniform vec3 horizon_color : source_color = vec3(0.3, 0.5, 0.8);
uniform vec3 zenith_color : source_color = vec3(0.02, 0.04, 0.1);

void sky() {
    float height = EYEDIR.y * 0.5 + 0.5;
    COLOR = mix(horizon_color, zenith_color, height);
}
```

### 23.6 Fog volume

```gdshader
shader_type fog;

uniform vec3 fog_color : source_color = vec3(0.5, 0.6, 0.7);
uniform float fog_density = 0.1;

void fog() {
    ALBEDO = fog_color;
    DENSITY = fog_density;
    EMISSION = vec3(0.0);
}
```

### 23.7 Include-based shader

`lighting_helpers.gdshaderinc`:

```gdshader
float rim_factor(vec3 normal, vec3 view_direction, float power) {
    return pow(1.0 - max(dot(normal, view_direction), 0.0), power);
}
```

`rim_material.gdshader`:

```gdshader
shader_type spatial;

#include "res://shaders/lighting_helpers.gdshaderinc"

uniform vec3 rim_color : source_color = vec3(1.0, 0.5, 0.1);
uniform float rim_power : hint_range(0.1, 8.0) = 2.0;

void fragment() {
    float rim = rim_factor(NORMAL, VIEW, rim_power);
    ALBEDO = rim_color * rim;
}
```

## 24. Validation checklist

The common project, type, coordinate-space, dependency, and validation
checklist in `shared_concepts.md` also applies.

### File and declarations

- Shader source files end in `.gdshader`; include files end in
  `.gdshaderinc`.
- Matching `.uid` sidecars are preserved after Godot generates them.
- The first declaration is a valid `shader_type`.
- There is at most one `shader_type`.
- `render_mode` contains only modes supported by that shader type.
- Functions match the selected shader type.

### Types and expressions

- Every statement has a semicolon.
- Every block has braces.
- Every local variable is initialized before use.
- Numeric conversions are explicit.
- Vector and matrix constructors have compatible component types.
- Matrix indexing uses column then row.
- Array indices remain in bounds.
- Float equality uses an epsilon where appropriate.

### Resources and uniforms

- Texture uniforms use the correct hints.
- `source_color` is present for color textures.
- Screen/depth samplers use `hint_screen_texture` and `hint_depth_texture`.
- Global uniforms exist in Project Settings with matching names and types.
- Uniform arrays do not use defaults.
- Structs are not declared as uniforms.

### Stages and built-ins

- Each built-in is valid for the current shader type and stage.
- Varyings are written before they are read.
- Outputs are written in the stage that owns them.
- `light()` is not relied on when `vertex_lighting` is enabled.
- `POSITION` is used only when clip-space override is intended.
- `skip_vertex_transform` includes the required manual transforms.
- Sky pass built-ins are handled when half, quarter, or cubemap passes are used.
- Particle restart and process values are used in their valid stages.

### Preprocessor and portability

- Directives start at column zero.
- Cyclic includes do not exist.
- Include depth is at most 25.
- No `.gdshader` is included.
- Macro replacement text does not accidentally inject semicolons.
- Renderer-specific samplers and modes are guarded or intentionally limited.
- Mobile precision is sufficient for the calculation.

### Performance and behavior

- Loops have bounded or provably terminating iteration.
- Texture sampling is not performed unnecessarily in every stage.
- `discard` is used only when alpha rejection is intended.
- Transparent, depth, culling, and blending modes match the material.
- Screen/depth reads account for screen resolution and coordinate space.

## 25. Failure patterns to avoid

Do not:

- write `shader_type` after functions or declarations;
- omit semicolons from ordinary shader statements;
- use GDScript or Python syntax in a shader;
- use arbitrary desktop GLSL extensions without checking support;
- use implicit casts between `int`, `uint`, `float`, and vectors;
- read an uninitialized local variable;
- use `SCREEN_TEXTURE` as if this were Godot 3;
- sample a screen texture without a hinted sampler;
- use a spatial built-in in a canvas item shader;
- use `fragment()` in a particle shader;
- assume `light()` runs with `vertex_lighting`;
- transform a vertex twice;
- use `POSITION` without understanding clip space;
- include a `.gdshader` file;
- create cyclic includes;
- add semicolons to macro directives accidentally;
- define a struct as a uniform;
- add defaults to uniform arrays;
- compare floats for exact equality;
- run an unbounded loop;
- assume a renderer supports every sampler or precision;
- copy GLSL transform code without checking Godot's automatic transforms;
- use `UV` where `SCREEN_UV` is required;
- assume Shadertoy uniforms exist automatically.

## 26. Generation workflow

Use this sequence when generating a shader:

1. Identify the target object and select `shader_type`.
2. Identify the render method: Compatibility, Mobile, or Forward+.
3. Select required `render_mode` options.
4. List uniforms and choose exact types and hints.
5. List varyings and decide which stages produce and consume them.
6. Add constants and helper functions.
7. Add renderer preprocessor branches only where necessary.
8. Add the stage functions supported by the shader type.
9. Write only valid built-ins and outputs for each stage.
10. Check coordinate spaces and automatic transforms.
11. Check texture hints and color-space behavior.
12. Check loop bounds, array bounds, and float comparisons.
13. Check include paths and dependency depth.
14. Compare the final shader against a minimal shader of the same type.
15. Compile it in the target project when possible and fix warnings/errors.

## 27. Source authority and limits

This guide describes the Godot shader language and the shader-stage structures
covered by the Godot 4.7 documentation. It cannot replace the exact class
reference for material properties, renderer-specific features, or project
configuration.

When a shader uses a feature not shown here:

1. Confirm that the feature exists in the target Godot version.
2. Confirm the selected `shader_type` and stage.
3. Confirm the render method and platform support.
4. Confirm the exact built-in name, type, and read/write direction.
5. Confirm texture hints, coordinate spaces, and automatic transforms.

If a generated shader conflicts with a shader produced by the target Godot
version, prefer the target-version compiler behavior and update the guide with
a minimal reproducible example.
