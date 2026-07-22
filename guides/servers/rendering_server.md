# RenderingServer Authoring Guide (Godot 4.7)

This guide explains how to create and control rendering resources and visual
objects directly through `RenderingServer`, without relying on scene-tree
nodes such as `Sprite2D`, `MeshInstance3D`, `Camera3D`, or `GPUParticles3D`.

`RenderingServer` is the low-level graphics API underneath Godot's scene
system. It is useful for procedural rendering, large numbers of objects,
custom render wrappers, server-only visualizations, and systems that need to
bypass node overhead. It is not automatically faster: the caller must manage
resource dependencies, transforms, visibility, synchronization, and cleanup.

For ordinary gameplay, prefer nodes and resources. Use this guide when the
server API is intentionally the authoritative rendering layer.

Read [`../shared_concepts.md`](../shared_concepts.md) for
the shared rules on project assumptions, typed values, resource ownership,
RID lifetime, timing, coordinate spaces, dependencies, and validation.

## 1. RenderingServer mental model

RenderingServer separates rendering into resource objects and instances:

- **resources** describe reusable data, such as textures, shaders, materials,
  meshes, skeletons, MultiMeshes, environments, and particle materials;
- **instances** place a resource into a 3D scenario or attach a canvas item to a
  2D canvas;
- **viewports** select what is rendered and where it is rendered;
- **RIDs** are opaque handles used to refer to all server objects.

The scene tree normally creates and owns these objects for you. Direct server
code must build the same dependency graph explicitly.

A server-created object:

- does not create a scene-tree node;
- does not automatically appear on screen;
- does not automatically receive input, notifications, or node callbacks;
- does not automatically have a `Node2D`/`Node3D` transform;
- must be connected to a canvas or scenario and, for 3D, a viewport;
- must be freed with `RenderingServer.free_rid(rid)`.

## 2. RIDs, rendering resources, and lifetime

The shared concepts guide defines the general RID and ownership contract.
RenderingServer RIDs are opaque; never construct one manually or assume that
its integer representation has meaning.

Create RIDs through `RenderingServer`:

```gdscript
var texture: RID = RenderingServer.texture_2d_create(image)
var shader: RID = RenderingServer.shader_create()
var material: RID = RenderingServer.material_create()
var mesh: RID = RenderingServer.mesh_create()
var instance: RID = RenderingServer.instance_create()
```

Many Godot resources can provide their server RID:

```gdscript
var texture_rid: RID = texture_resource.get_rid()
var mesh_rid: RID = mesh_resource.get_rid()
```

Keep a strong reference to every `Resource` or `RefCounted` object whose RID is
being used. The RID does not keep the source resource alive, so a released
source can invalidate a handle still stored by a script.

Free dependents before their dependencies. For example:

```gdscript
RenderingServer.free_rid(instance)
RenderingServer.free_rid(material)
RenderingServer.free_rid(mesh)
RenderingServer.free_rid(shader)
RenderingServer.free_rid(texture)
```

Do not free a RID obtained from a node or resource that still owns it. Direct
server code should normally create and own its own RIDs. If a node already
owns an object, use the node/resource API rather than mutating its internal
server object.

Do not free the current world canvas, scenario, or viewport RIDs. They are
owned by the corresponding `World2D`, `World3D`, or `Viewport`.

## 3. Threading and asynchronous behavior

RenderingServer commands are commonly queued for the rendering thread. Follow
the shared synchronization rules: a setter does not mean that the GPU has
completed the operation, and getters may flush queued work or stall. Prefer
maintaining authoritative values in your own data structures.

`call_on_render_thread(callable)` schedules a `Callable` on the rendering
thread. Use it only when an operation must execute on that thread and the
callable is safe to run there. Do not access scene-tree objects from the
render-thread callable unless the operation is explicitly thread-safe.

`force_draw(swap_buffers, frame_step)` forces rendering work and is intended
for special synchronization, screenshots, editor-like tools, or controlled
frame stepping. It is not a normal per-frame update method.

## 4. Textures

### 4.1 Texture types

RenderingServer distinguishes:

| Type | Meaning |
|---|---|
| `TEXTURE_TYPE_2D` | A regular 2D texture. |
| `TEXTURE_TYPE_LAYERED` | A layered texture. |
| `TEXTURE_TYPE_3D` | A volume texture. |

Layered types are:

- `TEXTURE_LAYERED_2D_ARRAY`: an array of 2D texture layers;
- `TEXTURE_LAYERED_CUBEMAP`: six faces forming a cubemap;
- `TEXTURE_LAYERED_CUBEMAP_ARRAY`: an array of cubemaps.

### 4.2 Creating textures

Use the matching constructor:

```gdscript
var texture_2d: RID = RenderingServer.texture_2d_create(image)
var texture_array: RID = RenderingServer.texture_2d_layered_create(
    layers,
    RenderingServer.TEXTURE_LAYERED_2D_ARRAY
)
var texture_3d: RID = RenderingServer.texture_3d_create(
    image_format,
    width,
    height,
    depth,
    mipmaps,
    depth_images
)
```

Other texture creation methods support placeholders, native graphics handles,
and `RenderingDevice` textures:

- `texture_2d_placeholder_create()`;
- `texture_2d_layered_placeholder_create()`;
- `texture_create_from_native_handle()`;
- `texture_rd_create()`.

Use native-handle methods only when the external handle, format, dimensions,
layer count, and ownership rules are known. The server cannot infer missing
metadata.

Useful texture methods include:

- `texture_get_format()`;
- `texture_get_path()`;
- `texture_set_path()`;
- `texture_set_force_redraw_if_visible()`.

Texture RIDs used as shader parameters, material parameters, mesh textures,
light projectors, decals, or canvas textures must remain valid for the entire
period in which those users reference them.

## 5. Shaders

Create a shader RID and assign Godot shader language source:

```gdscript
var shader: RID = RenderingServer.shader_create()
RenderingServer.shader_set_code(shader, shader_source)
RenderingServer.shader_set_path_hint(shader, "res://generated/example.gdshader")
```

`ShaderMode` identifies the expected shader stage:

| Constant | Meaning |
|---|---|
| `SHADER_SPATIAL` | 3D material shader. |
| `SHADER_CANVAS_ITEM` | 2D canvas-item shader. |
| `SHADER_PARTICLES` | Particle-process shader. |
| `SHADER_SKY` | Sky shader. |
| `SHADER_FOG` | Fog-volume shader. |
| `SHADER_TEXTURE_BLIT` | Texture blit shader. |

The shader source's `shader_type` must match the resources and draw path that
consume it. A canvas-item shader is not interchangeable with a spatial shader.
Use the `.gdshader` authoring guide for built-ins, render modes, uniforms,
varyings, and stage-specific semantics.

Shader methods:

- `shader_set_code()` replaces the source code;
- `shader_get_code()` retrieves the current source;
- `shader_get_parameter_default()` reads a declared uniform's default value;
- `shader_set_default_texture_parameter()` assigns a default texture for a
  named sampler and optional array index;
- `shader_get_default_texture_parameter()` reads a default texture;
- `shader_set_path_hint()` stores a path used for debugging and caching.

Uniform values are normally set on a material with
`material_set_param()`, not by mutating the shader source.

## 6. Materials

Create a material, assign a shader, then set shader parameters:

```gdscript
var material: RID = RenderingServer.material_create()
RenderingServer.material_set_shader(material, shader)
RenderingServer.material_set_param(
    material,
    &"albedo_texture",
    texture
)
RenderingServer.material_set_param(
    material,
    &"albedo_color",
    Color.WHITE
)
```

`material_set_param(material, parameter, value)` uses a `StringName` uniform
name and a `Variant` value. The value must match the shader uniform's declared
type. A texture uniform requires a valid texture RID; a scalar requires a
numeric value; vectors and colors must use compatible value types.

Other material methods:

- `material_get_param()` reads a parameter;
- `material_set_next_pass()` chains a second material pass;
- `material_set_render_priority()` changes material ordering where supported;
- `material_set_use_debanding()` enables material debanding behavior.

Material parameters are shared by every instance using that material. If one
object needs a different value, create a separate material or use an instance
shader parameter API instead of mutating a shared material.

## 7. Meshes and surface arrays

### 7.1 Mesh structure

A mesh RID contains one or more surfaces. Each surface has:

- a primitive topology;
- a vertex-data array;
- optional blend-shape arrays;
- optional distance-based LOD index arrays;
- optional compression settings.

Create and populate a mesh:

```gdscript
var mesh: RID = RenderingServer.mesh_create()
RenderingServer.mesh_add_surface_from_arrays(
    mesh,
    RenderingServer.PRIMITIVE_TRIANGLES,
    arrays
)
```

`PrimitiveType` values are:

- `PRIMITIVE_POINTS`;
- `PRIMITIVE_LINES`;
- `PRIMITIVE_LINE_STRIP`;
- `PRIMITIVE_TRIANGLES`;
- `PRIMITIVE_TRIANGLE_STRIP`.

`mesh_create_from_surfaces()` can build a mesh from serialized surface
dictionaries. `mesh_clear()` removes all surfaces.

### 7.2 Surface arrays

The `arrays` argument is an array with `Mesh.ARRAY_MAX` slots. Each slot is
either an appropriately typed array or `null`. The vertex slot is required;
the other slots are optional:

| Slot | Meaning |
|---|---|
| `ARRAY_VERTEX` | Vertex positions. |
| `ARRAY_NORMAL` | Vertex normals. |
| `ARRAY_TANGENT` | Tangent data. |
| `ARRAY_COLOR` | Per-vertex colors. |
| `ARRAY_TEX_UV` | First UV set. |
| `ARRAY_TEX_UV2` | Second UV set. |
| `ARRAY_CUSTOM0` to `ARRAY_CUSTOM3` | Four custom per-vertex channels. |
| `ARRAY_BONES` | Bone indices for skinning. |
| `ARRAY_WEIGHTS` | Bone weights for skinning. |
| `ARRAY_INDEX` | Optional index order. |

The index array changes the surface to indexed mode. The other arrays provide
per-vertex data and must have matching lengths, except where the documented
format permits multiple packed values per vertex. The index array can have its
own length and defines the order in which vertices are assembled.

Example triangle surface:

```gdscript
var arrays: Array = []
arrays.resize(Mesh.ARRAY_MAX)
arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([
    Vector3(0.0, 1.0, 0.0),
    Vector3(-1.0, -1.0, 0.0),
    Vector3(1.0, -1.0, 0.0),
])
arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([
    Vector3.FORWARD,
    Vector3.FORWARD,
    Vector3.FORWARD,
])
arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([
    Vector2(0.5, 0.0),
    Vector2(0.0, 1.0),
    Vector2(1.0, 1.0),
])

var mesh := RenderingServer.mesh_create()
RenderingServer.mesh_add_surface_from_arrays(
    mesh,
    RenderingServer.PRIMITIVE_TRIANGLES,
    arrays
)
```

Use `mesh_surface_get_arrays()` and
`mesh_surface_get_blend_shape_arrays()` when inspecting an existing mesh.
`mesh_get_surface_count()`, `mesh_get_surface()`, and
`mesh_set_custom_aabb()` provide surface and culling control.

`mesh_set_shadow_mesh()` assigns a lower-cost mesh used for shadow rendering.
It does not change the visible mesh.

### 7.3 Blend shapes

Set the mesh blend-shape mode with `mesh_set_blend_shape_mode()`. A blend
shape contains vertex, normal, and tangent data only when those channels exist
in the base surface. Use `instance_set_blend_shape_weight()` to select a
weight on a particular instance.

## 8. MultiMesh instancing

`MultiMesh` stores many transforms and optional per-instance colors or custom
data while referencing one mesh. It reduces draw overhead for large numbers of
copies.

```gdscript
var mesh: RID = RenderingServer.mesh_create()
var multimesh: RID = RenderingServer.multimesh_create()

RenderingServer.multimesh_allocate_data(
    multimesh,
    1000,
    RenderingServer.MULTIMESH_TRANSFORM_3D,
    true,
    true
)
RenderingServer.multimesh_set_mesh(multimesh, mesh)
RenderingServer.multimesh_instance_set_transform(
    multimesh,
    0,
    Transform3D(Basis.IDENTITY, Vector3.ZERO)
)
```

`multimesh_allocate_data()` fixes the instance count and storage formats:

- `MULTIMESH_TRANSFORM_2D` stores `Transform2D`;
- `MULTIMESH_TRANSFORM_3D` stores `Transform3D`;
- `color_format` enables per-instance `Color`;
- `custom_data_format` enables per-instance `Color` custom data;
- `use_indirect` enables indirect rendering data where supported.

Use the matching setter:

- `multimesh_instance_set_transform_2d()`;
- `multimesh_instance_set_transform()`;
- `multimesh_instance_set_color()`;
- `multimesh_instance_set_custom_data()`.

The index must be in the allocated range. The transform format and enabled
color/custom-data formats cannot be changed by simply calling a setter;
reallocate the MultiMesh when those formats change.

## 9. 2D canvas rendering

### 9.1 Canvas and canvas items

Create a canvas item and parent it to a canvas or an existing `CanvasItem`:

```gdscript
var item: RID = RenderingServer.canvas_item_create()
RenderingServer.canvas_item_set_parent(item, get_canvas_item())
RenderingServer.canvas_item_set_transform(
    item,
    Transform2D(0.0, Vector2(100.0, 80.0))
)
RenderingServer.canvas_item_set_visible(item, true)
```

`get_canvas_item()` returns the RID owned by a `CanvasItem`. A standalone
canvas can be obtained from `get_world_2d().canvas`, or created with
`canvas_create()` and connected to a viewport explicitly.

Canvas-item drawing commands include:

- `canvas_item_add_texture_rect()` and
  `canvas_item_add_texture_rect_region()`;
- `canvas_item_add_mesh()` and `canvas_item_add_multimesh()`;
- `canvas_item_add_rect()`, `canvas_item_add_circle()`,
  `canvas_item_add_ellipse()`, and `canvas_item_add_line()`;
- `canvas_item_add_polygon()`, `canvas_item_add_polyline()`, and
  `canvas_item_add_multiline()`;
- `canvas_item_add_nine_patch()`;
- `canvas_item_add_triangle_array()`;
- `canvas_item_add_particles()`;
- `canvas_item_add_set_transform()`;
- `canvas_item_add_clip_ignore()`.

Most draw commands append immutable commands to the canvas item. To change
their geometry, call `canvas_item_clear()` and add the commands again. The
canvas item transform, visibility, material, modulation, and parent can be
changed without rebuilding its draw commands.

### 9.2 Texture drawing

`canvas_item_add_texture_rect(item, rect, texture, tile, modulate, transpose)`
draws a texture in the target rectangle. It does not copy the texture; the
texture RID must remain alive.

`canvas_item_add_texture_rect_region()` adds a selected source rectangle and
supports UV clipping. Use it for sprite sheets and atlas regions.

### 9.3 Canvas item state

Important canvas-item setters include:

- `canvas_item_set_parent()`;
- `canvas_item_set_transform()`;
- `canvas_item_set_visible()`;
- `canvas_item_set_modulate()` and
  `canvas_item_set_self_modulate()`;
- `canvas_item_set_z_index()` and
  `canvas_item_set_z_as_relative_to_parent()`;
- `canvas_item_set_material()`;
- `canvas_item_set_light_mask()`;
- `canvas_item_set_visibility_layer()`;
- `canvas_item_set_draw_behind_parent()`;
- `canvas_item_set_use_parent_material()`;
- `canvas_item_set_clip()`;
- `canvas_item_set_custom_rect()`;
- `canvas_item_set_default_texture_filter()` and
  `canvas_item_set_default_texture_repeat()`;
- `canvas_item_set_instance_shader_parameter()`.

Canvas items created from code should call
`canvas_item_reset_physics_interpolation()` after their initial transform when
they are created during runtime. Without this, the first interpolated frame
can appear to teleport from an uninitialized position.

For physics-driven motion, use:

- `canvas_item_set_interpolated()`;
- `canvas_item_transform_physics_interpolation()`;
- `canvas_item_reset_physics_interpolation()`.

These operate on rendering interpolation state and do not perform physics.

### 9.4 2D lights and occluders

Create a 2D light with `canvas_light_create()`, attach it to a canvas with
`canvas_light_attach_to_canvas()`, and configure color, energy, texture,
transform, masks, z range, shadows, and blend mode.

Create an occluder with `canvas_light_occluder_create()` and assign its
polygon using `canvas_light_occluder_set_polygon()`. The polygon resource is
created with `canvas_occluder_polygon_create()` and configured with its
points and cull mode.

Canvas lighting affects only compatible canvas items and masks. It is not the
same system as 3D lights.

## 10. 3D scenarios and visual instances

### 10.1 Scenario and instance relationship

A 3D visual instance needs:

1. a base resource such as a mesh, MultiMesh, particle system, light, decal,
   reflection probe, or fog volume;
2. an instance RID;
3. a scenario RID;
4. a transform;
5. a viewport that renders the scenario.

Use the current world scenario when the object should appear with the existing
scene:

```gdscript
var instance: RID = RenderingServer.instance_create()
RenderingServer.instance_set_scenario(instance, get_world_3d().scenario)
RenderingServer.instance_set_base(instance, mesh)
RenderingServer.instance_set_transform(
    instance,
    Transform3D(Basis.IDENTITY, Vector3(0.0, 0.0, -3.0))
)
RenderingServer.instance_set_visible(instance, true)
```

`instance_create2(base, scenario)` combines creation and base/scenario
assignment.

The instance base determines the instance type:

| Type | Meaning |
|---|---|
| `INSTANCE_MESH` | Mesh geometry. |
| `INSTANCE_MULTIMESH` | MultiMesh geometry. |
| `INSTANCE_PARTICLES` | Particle emitter. |
| `INSTANCE_PARTICLES_COLLISION` | Particle collision resource. |
| `INSTANCE_LIGHT` | 3D light. |
| `INSTANCE_REFLECTION_PROBE` | Reflection probe. |
| `INSTANCE_DECAL` | Decal projector. |
| `INSTANCE_VOXEL_GI` | VoxelGI volume. |
| `INSTANCE_LIGHTMAP` | Lightmap data. |
| `INSTANCE_OCCLUDER` | Occlusion culling geometry. |
| `INSTANCE_VISIBLITY_NOTIFIER` | Visibility notifier. |
| `INSTANCE_FOG_VOLUME` | Fog volume. |

### 10.2 Instance configuration

Use:

- `instance_set_base()`;
- `instance_set_scenario()`;
- `instance_set_transform()`;
- `instance_set_visible()`;
- `instance_set_layer_mask()`;
- `instance_set_custom_aabb()`;
- `instance_set_extra_visibility_margin()`;
- `instance_set_ignore_culling()`;
- `instance_set_visibility_parent()`;
- `instance_set_pivot_data()`;
- `instance_attach_object_instance_id()`;
- `instance_teleport()`.

Geometry-specific methods use the instance RID:

- `instance_geometry_set_material_override()`;
- `instance_geometry_set_material_overlay()`;
- `instance_set_surface_override_material()`;
- `instance_geometry_set_cast_shadows_setting()`;
- `instance_geometry_set_flag()`;
- `instance_geometry_set_lod_bias()`;
- `instance_geometry_set_transparency()`;
- `instance_geometry_set_lightmap()`;
- `instance_geometry_set_shader_parameter()`;
- `instance_set_blend_shape_weight()`.

`SHADOW_CASTING_SETTING_OFF`, `ON`, `DOUBLE_SIDED`, and `SHADOWS_ONLY` control
shadow behavior. `SHADOWS_ONLY` draws the object's shadow but not the visible
object.

Instance shader parameters are per-instance values. Use them when many
instances share one material but need different uniform values.

## 11. Cameras, viewports, and scenarios

### 11.1 Cameras

Create and configure a camera RID:

```gdscript
var camera: RID = RenderingServer.camera_create()
RenderingServer.camera_set_transform(
    camera,
    Transform3D(Basis.IDENTITY, Vector3(0.0, 0.0, 5.0))
)
RenderingServer.camera_set_perspective(camera, 70.0, 0.05, 1000.0)
```

Projection methods:

- `camera_set_perspective(camera, fovy_degrees, z_near, z_far)`;
- `camera_set_orthogonal(camera, size, z_near, z_far)`;
- `camera_set_frustum(camera, size, offset, z_near, z_far)`.

Additional camera controls:

- `camera_set_environment()`;
- `camera_set_camera_attributes()`;
- `camera_set_compositor()`;
- `camera_set_cull_mask()`;
- `camera_set_use_vertical_aspect()`.

The camera transform is a `Transform3D` in world space. Near and far planes
must be chosen for the intended world scale; an unnecessarily huge depth range
reduces depth precision.

### 11.2 Viewports

Create a viewport with `viewport_create()`, then configure its size, update
mode, clear mode, scenario, and camera:

```gdscript
var viewport: RID = RenderingServer.viewport_create()
RenderingServer.viewport_set_size(viewport, 1280, 720)
RenderingServer.viewport_set_scenario(viewport, get_world_3d().scenario)
RenderingServer.viewport_attach_camera(viewport, camera)
RenderingServer.viewport_set_active(viewport, true)
```

Important viewport methods include:

- `viewport_set_size()`;
- `viewport_set_update_mode()`;
- `viewport_set_clear_mode()`;
- `viewport_set_active()`;
- `viewport_set_scenario()`;
- `viewport_attach_camera()`;
- `viewport_set_parent_viewport()`;
- `viewport_set_canvas_transform()`;
- `viewport_set_scaling_3d_mode()`;
- `viewport_set_use_xr()`.

`ViewportUpdateMode` controls whether the viewport renders continuously,
only when requested, or only when visible according to the mode. Do not assume
that creating a viewport automatically makes it active or visible.

`ViewportClearMode` controls whether the viewport clears its color/depth
buffers before drawing. A non-clearing viewport preserves previous contents
and can expose undefined or stale pixels if every region is not overwritten.

### 11.3 Canvas attachment

2D canvases are assigned to viewports through the viewport canvas methods.
Use `viewport_set_canvas_transform(viewport, canvas, transform)` to position a
canvas in viewport space. Canvas item transforms are local to their parent
hierarchy; viewport canvas transforms are a separate layer of transform.

## 12. Lights and environment

### 12.1 3D lights

Create a light base with one of:

- `directional_light_create()`;
- `omni_light_create()`;
- `spot_light_create()`;
- `area_light_create()`.

Configure common light properties with:

- `light_set_color()`;
- `light_set_param()` using `LightParam`;
- `light_set_shadow()`;
- `light_set_cull_mask()`;
- `light_set_shadow_caster_mask()`;
- `light_set_projector()`;
- `light_set_negative()`;
- `light_set_bake_mode()`;
- `light_set_distance_fade()`.

Type-specific methods configure directional shadow splits and sky mode,
omnidirectional shadow mode, area light size, and projector filtering.

Light cull masks decide which visual layers are affected. They are independent
from physics collision layers and from camera cull masks.

### 12.2 Environment

Create an environment RID with `environment_create()`. Configure background,
ambient lighting, sky, fog, glow, tone mapping, screen-space effects, and
global illumination through the environment methods:

- `environment_set_background()`;
- `environment_set_bg_color()` and `environment_set_bg_energy()`;
- `environment_set_sky()`, `environment_set_sky_orientation()`, and
  `environment_set_sky_custom_fov()`;
- `environment_set_ambient_light()`;
- `environment_set_fog()` and `environment_set_fog_depth()`;
- `environment_set_glow()`;
- `environment_set_tonemap()`;
- `environment_set_ssao()` and `environment_set_ssao_quality()`;
- `environment_set_ssil_quality()`;
- `environment_set_ssr()`, `environment_set_ssr_half_size()`, and
  `environment_set_ssr_roughness_quality()`;
- `environment_set_sdfgi()`, its ray-count and convergence methods;
- `environment_set_volumetric_fog()` and its filter/volume-size methods;
- `environment_set_adjustment()`.

These methods configure renderer features; they do not create a visible
environment until the RID is assigned to a camera or viewport path.

## 13. Particles

`particles_create()` creates a GPU particle system resource. Configure it with:

- `particles_set_amount()` and `particles_set_amount_ratio()`;
- `particles_set_lifetime()`;
- `particles_set_one_shot()`;
- `particles_set_emitting()`;
- `particles_set_speed_scale()`;
- `particles_set_randomness_ratio()`;
- `particles_set_explosiveness_ratio()`;
- `particles_set_fixed_fps()`;
- `particles_set_fractional_delta()`;
- `particles_set_pre_process_time()`;
- `particles_set_process_material()`;
- `particles_set_draw_passes()` and
  `particles_set_draw_pass_mesh()`;
- `particles_set_custom_aabb()`;
- `particles_set_emission_transform()`;
- `particles_set_use_local_coordinates()`;
- `particles_set_trails()`;
- `particles_set_subemitter()`.

The process material is a material RID using the particle shader mode. Draw
passes are mesh RIDs used to render each particle. A particle RID alone does
not appear; create an `INSTANCE_PARTICLES` instance, assign the particle base,
and place it in a scenario.

Particle coordinate mode matters:

- local coordinates make particles follow the emitter transform;
- global coordinates preserve world positions when the emitter moves.

Set a custom AABB when the automatic bounds cannot cover the particle motion,
but keep it as tight as practical to preserve culling efficiency.

## 14. Skeletons and skinning

Create a skeleton RID and allocate its bone count:

```gdscript
var skeleton: RID = RenderingServer.skeleton_create()
RenderingServer.skeleton_allocate_data(skeleton, bone_count, false)
RenderingServer.skeleton_bone_set_transform(
    skeleton,
    0,
    Transform3D.IDENTITY
)
```

Use `is_2d_skeleton = true` for a 2D skeleton. The matching setters are:

- `skeleton_bone_set_transform()` for 3D bones;
- `skeleton_bone_set_transform_2d()` for 2D bones;
- `skeleton_set_base_transform_2d()` for the 2D skeleton base transform.

Meshes must contain compatible `ARRAY_BONES` and `ARRAY_WEIGHTS` data.
Attach the skeleton with `instance_attach_skeleton()` or
`canvas_item_attach_skeleton()`. Bone indices and weights are mesh data, not
shader parameters inferred automatically from a material.

## 15. Global shader parameters

Global shader parameters are renderer-wide named values:

```gdscript
RenderingServer.global_shader_parameter_add(
    &"wind_direction",
    RenderingServer.GLOBAL_VAR_TYPE_VEC3,
    Vector3.RIGHT
)
RenderingServer.global_shader_parameter_set(
    &"wind_direction",
    Vector3(1.0, 0.0, 0.2)
)
```

Use:

- `global_shader_parameter_add()` to declare the name, type, and default;
- `global_shader_parameter_set()` to set the project-wide value;
- `global_shader_parameter_set_override()` to override it temporarily;
- `global_shader_parameter_get()`;
- `global_shader_parameter_get_type()`;
- `global_shader_parameter_get_list()`;
- `global_shader_parameter_remove()`.

The shader must declare a compatible `global uniform`. Global names are
project-wide and can collide with other systems; use a stable naming
convention.

## 16. Specialized rendering resources

RenderingServer also provides low-level bases for:

- reflection probes: `reflection_probe_create()` and its box, intensity,
  update-mode, cull-mask, ambient, and reflection settings;
- decals: `decal_create()` plus albedo, normal, emission, size, fade,
  cull-mask, and distance-fade settings;
- VoxelGI: `voxel_gi_create()` and bounds, cell-size, energy, bias, and
  quality settings;
- fog volumes: `fog_volume_create()` plus shape, size, and material;
- lightmaps: `lightmap_create()` plus baked texture and probe data;
- compositors and compositor effects;
- occlusion culling geometry;
- visibility notifiers.

These resources still follow the same pattern: create a base RID, configure
it, create an instance of the appropriate type, assign the base and scenario,
set a transform or bounds, and free the instance before the base.

Do not confuse a resource RID with an instance RID. For example, a reflection
probe base describes probe behavior, while an instance places that probe in a
scenario.

## 17. Complete 2D texture item example

```gdscript
extends Node2D

var item: RID
var texture: Texture2D

func _ready() -> void:
    item = RenderingServer.canvas_item_create()
    RenderingServer.canvas_item_set_parent(item, get_canvas_item())

    texture = load("res://icon.svg")
    RenderingServer.canvas_item_add_texture_rect(
        item,
        Rect2(-texture.get_size() * 0.5, texture.get_size()),
        texture.get_rid()
    )
    RenderingServer.canvas_item_set_transform(
        item,
        Transform2D(0.0, Vector2(200.0, 120.0))
    )
    RenderingServer.canvas_item_reset_physics_interpolation(item)

func _exit_tree() -> void:
    if item.is_valid():
        RenderingServer.free_rid(item)
```

The `Texture2D` reference is intentionally stored. The canvas item draw
command uses the texture RID and does not replace the resource lifetime.

## 18. Complete 3D mesh instance example

```gdscript
extends Node3D

var mesh: Mesh
var instance: RID

func _ready() -> void:
    mesh = load("res://models/example_mesh.tres") as Mesh
    instance = RenderingServer.instance_create2(
        mesh.get_rid(),
        get_world_3d().scenario
    )
    RenderingServer.instance_set_transform(
        instance,
        Transform3D(Basis.IDENTITY, Vector3(0.0, 0.0, -3.0))
    )
    RenderingServer.instance_set_visible(instance, true)

func _exit_tree() -> void:
    if instance.is_valid():
        RenderingServer.free_rid(instance)
```

The exact way a `Mesh` is obtained from an imported asset depends on the
resource type. The important server contract is that the mesh resource remains
referenced while the instance uses its RID.

## 19. Validation checklist

Before generating or reviewing RenderingServer code, verify:

- The common ownership, identifier, lifetime, timing, type, and coordinate
  checklist in `../shared_concepts.md` passes.
- A 2D canvas item has a valid parent canvas or `CanvasItem`.
- A 3D instance has a base, scenario, transform, and visible viewport path.
- A viewport is sized, active, and configured with the intended camera or
  parent viewport.
- Mesh arrays have `Mesh.ARRAY_MAX` slots, a valid vertex array, compatible
  lengths, and correct index-mode semantics.
- Primitive topology matches the vertex/index data.
- Shader mode matches the shader source and consuming resource.
- Material parameter names and `Variant` values match shader uniform types.
- Shared-material behavior follows the duplication and ownership rules in
  `../shared_concepts.md`.
- MultiMesh formats are allocated before per-instance setters are called.
- Per-instance shader parameters are used for instance-specific variation.
- Physics-driven rendering uses interpolation reset/synchronization where
  needed.
- Camera, light, and instance masks are not confused with physics masks.
- Custom AABBs cover all rendered geometry without being unnecessarily huge.
- Render-thread callbacks do not access unsafe scene-tree state.
- `force_draw()` is reserved for intentional synchronization rather than
  ordinary polling.
