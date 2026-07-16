# Godot 4.7 Authoring Guides Entry Point

This is the entry point for the Godot authoring guides in this directory. Read
it first when generating or reviewing Godot files without relying on the
editor. It explains which guide to use, when multiple guides are required, how
the formats connect, and how to validate the final result.

These guides target Godot 4.7. They describe documented engine behavior and
serialization rules, but they cannot know project-specific class names, input
actions, node paths, resource paths, imported assets, project settings, or
custom scripts. Never invent those project details.

Read [`shared_concepts.md`](shared_concepts.md) alongside
this entry point whenever a task crosses formats or uses shared ownership,
timing, coordinate-space, identifier, or validation rules.

## 0. AI execution contract

This directory is designed to be copied into a Godot project and used as a
standalone authoring reference. Only this guide directory, the target project,
and the target Godot executable are assumed. Use this order of authority:

1. The target Godot executable's parser, loader, compiler, and runtime behavior.
2. These Godot 4.7 authoring guides.
3. The target project's files, settings, tests, generated examples, and
   established conventions.
4. Generic model knowledge or remembered examples.

For engine API facts, do not let stale project code override the target engine
or these versioned guides. For project-specific facts, do not let a generic
example override the project.

### Optional local class reference

The copied guide directory may contain locally generated files under
`class_reference/`. This cache is optional and is commonly excluded from Git
to keep project repositories small.

Before using it, confirm that:

- class `.rst` files are actually present;
- `class_reference/VERSION` matches Godot 4.7;
- the requested class file exists;
- the files are not a partial or mixed-version copy.

If any check fails, ignore the cache and continue with these authoring guides,
the target project, and the target Godot executable. Missing class-reference
files are not permission to guess an API. Search the relevant specialized
guide and project usage, test a minimal candidate when possible, and preserve
uncertainty when the exact member cannot be established.

### Inspect before generating

Before writing an artifact:

1. Read `project.godot`, especially its feature tags and renderer/physics
   settings. `config_version` alone does not identify the exact engine release.
2. Check the project's README, CI, export configuration, and launch scripts for
   the exact Godot version and validation commands.
3. Search for the closest existing script, scene, resource, shader, or server
   wrapper and preserve its conventions.
4. Verify every custom class, autoload, input action, collision layer, node
   path, resource path, shader parameter, renderer, and physics backend used by
   the change.
5. Identify whether the edited file is source-controlled authoring data,
   engine-generated metadata, imported output, or runtime-only state.

If the project does not establish a required fact, make the uncertainty
explicit and choose a conservative, reversible default. Never fabricate a UID,
path, API, input action, node, or project setting to make an example look
complete.

### Choose the safest authoring surface

Prefer the highest-level surface that satisfies the requirement:

```text
node/resource API
        |
        v
simple text scene/resource editing
        |
        v
ResourceSaver/editor-generated complex serialization
        |
        v
low-level PhysicsServer/RenderingServer RIDs
```

Use hand-authored `.tscn` and `.tres` for small, well-understood structures.
Use the target Godot version to generate complex animation, mesh, tile, import,
or packed-array structures. Use server APIs only when node/resource APIs are
insufficient or measured node overhead justifies the added ownership burden.

Do not edit files under `.godot/` as project source. Preserve imported source
assets and change import settings rather than patching generated import output.
For Godot 4.4 and later, scripts and shaders have engine-generated `.uid`
sidecars. Commit them, move them with their source file, and do not invent,
copy, or casually delete their contents.

### Keep prompt context focused

Do not load all guides for every task. Read this entry point, the shared guide,
and only the specialized guides and sections required by the dependency graph.
Search within this directory for the exact concept, class, method, annotation,
format field, or built-in before loading another complete guide. If an
exhaustive class member is outside the scope of these guides, inspect existing
target-project usage or test the smallest candidate with the target Godot
executable. If neither establishes the fact, state the uncertainty instead of
inventing an API.

### Validate behavior, not just text

Use the strongest available validation:

1. structural checks for references, IDs, paths, and dependency order;
2. target-engine parse, import, load, and shader compilation;
3. the project's existing tests or minimal runtime reproduction;
4. behavioral checks for collisions, transforms, rendering, ownership, and
   cleanup.

When supported by the project, a headless editor start such as
`godot --headless --path <project> --editor --quit` can expose import, parse,
load, and shader errors. It can also execute editor plugins and `@tool` code, so
run it in a controlled worktree and inspect all resulting changes. Use the
project's documented command when one exists.

Do not claim a file was engine-validated when it was only inspected as text.

## 1. Guide map

### File-format guides

| Guide | Read it when generating or editing |
|---|---|
| [`shared_concepts.md`](shared_concepts.md) | Any task involving project assumptions, typed values, shared resources, identifiers, RIDs, timing, coordinate spaces, cross-format dependencies, or common validation. |
| [`tscn.md`](tscn.md) | A `.tscn` scene, node hierarchy, scene instance, connection, or serialized node property. |
| [`tres_resource.md`](tres_resource.md) | A `.tres` resource, material, shader material, animation resource, shape resource, theme resource, or custom `Resource`. |
| [`gdscript.md`](gdscript.md) | A `.gd` script, GDScript type, annotation, signal, export, RPC, lifecycle method, or engine API call. |
| [`gdshader.md`](gdshader.md) | A `.gdshader` file, shader uniform, render mode, built-in, shader stage, or shader-language expression. |

### Shared and dimension-specific physics guides

| Guide | Read it when generating or editing |
|---|---|
| [`physics.md`](physics.md) | Any physics behavior shared by 2D and 3D: timing, collision layers/masks, body roles, areas, forces, queries, materials, stability, and server concepts. |
| [`physics_2d.md`](physics_2d.md) | 2D-only physics classes, `Vector2`, 2D shapes, `CharacterBody2D`, `RigidBody2D`, `RayCast2D`, `ShapeCast2D`, and `PhysicsDirectSpaceState2D`. |
| [`physics_3d.md`](physics_3d.md) | 3D-only physics classes, `Vector3`, 3D shapes, `CharacterBody3D`, `RigidBody3D`, `SoftBody3D`, `VehicleBody3D`, `RayCast3D`, and `PhysicsDirectSpaceState3D`. |

Read the shared physics guide together with exactly one dimension-specific
guide. The shared guide intentionally avoids repeating dimension-specific API
details.

### Low-level server guides

| Guide | Read it when generating or editing |
|---|---|
| [`servers/physics_server_2d.md`](servers/physics_server_2d.md) | Creating 2D physics spaces, shapes, bodies, areas, joints, callbacks, or queries directly with `PhysicsServer2D` and `RID`s. |
| [`servers/physics_server_3d.md`](servers/physics_server_3d.md) | Creating 3D physics spaces, shapes, bodies, areas, joints, soft bodies, callbacks, or queries directly with `PhysicsServer3D` and `RID`s. |
| [`servers/rendering_server.md`](servers/rendering_server.md) | Creating textures, shaders, materials, meshes, canvas items, 3D visual instances, viewports, cameras, lights, particles, or other graphics directly with `RenderingServer` and `RID`s. |

Server guides are supplemental, not replacements for the shared and
dimension-specific guides. Read the ordinary physics guides first when the
server object represents gameplay physics. Read the RenderingServer guide
alongside the scene/resource guides when server-created visuals must be
serialized or synchronized with scene objects.

### Shared concepts guide

[`shared_concepts.md`](shared_concepts.md) is the common
reference for project-specific assumptions, typed values, shared resources,
identifier distinctions, RID ownership, timing, synchronization, coordinate
spaces, cross-artifact dependencies, and general validation. Specialized
guides retain only the rules that are unique to their format, dimension, or
server.

## 2. Choose the correct primary guide

Start by identifying the artifact being created:

```text
Need a node tree or scene instance?       -> .tscn guide
Need reusable serialized data/resource?   -> .tres guide
Need executable behavior?                 -> GDScript guide
Need GPU shader source?                   -> gdshader guide
Need physics behavior on nodes?           -> shared physics + 2D or 3D guide
Need low-level physics RIDs?              -> matching PhysicsServer guide
Need low-level rendering RIDs?            -> RenderingServer guide
```

The file extension is not enough when a change crosses formats. A typical
feature can require several guides:

| Feature | Guides normally required |
|---|---|
| A scene with scripted gameplay | `.tscn` + GDScript + the relevant physics or rendering guide. |
| A custom material | `.tres` + `.gdshader`; add RenderingServer only if bypassing nodes/resources. |
| A physics object in a scene | `.tscn` + shared physics + 2D or 3D physics + GDScript if controlled by code. |
| A server-created physics object with a visible mesh | matching PhysicsServer + RenderingServer + GDScript; add `.tres`/`.tscn` only for persistent assets. |
| A particle effect | `.tscn` or `.tres` + GDScript if controlled at runtime + `.gdshader` for custom particle shaders; add RenderingServer for direct RIDs. |
| A shader uniform configured in a material | `.gdshader` + `.tres` or GDScript material API. |
| A generated mesh saved as a resource | `.tres` + RenderingServer concepts if the mesh is built from raw arrays. |

## 3. Shared concepts and dependency graph

Read [`shared_concepts.md`](shared_concepts.md) for the
cross-format dependency graph and the rules shared by all authoring guides.

## 4. When to read each guide in detail

### 4.1 Read the `.tscn` guide first when

The output is a scene file, even if the difficult part is physics, materials,
animation, or scripting. The `.tscn` guide defines:

- `[gd_scene]`, `[ext_resource]`, `[sub_resource]`, `[node]`, and
  `[connection]` sections;
- resource ordering and local IDs;
- root and parent paths;
- ownership, groups, node paths, instance placeholders, and inherited nodes;
- scene instances and animation track paths;
- exact Godot Variant serialization syntax.

Then read the guide for the referenced resource or behavior. Do not put
runtime logic, shader source, or arbitrary JSON inside a `.tscn`.

### 4.2 Read the `.tres` guide first when

The output is a reusable resource or when a scene property points to a
resource with nested sub-resources. The `.tres` guide defines:

- `[gd_resource]`, `[ext_resource]`, `[sub_resource]`, and `[resource]`;
- resource type declarations and scripts;
- UID and local resource-ID distinctions;
- resource sharing and `resource_local_to_scene`;
- Variant values and resource-specific serialization;
- when exact engine-generated output should be copied rather than fabricated.

Read the shader guide for shader source and the physics guide for the meaning
of physics resources. A `.tres` guide explains serialization; it does not
replace the semantic guide for the resource's properties.

### 4.3 Read the GDScript guide first when

The output is executable code or a scene/resource depends on a script. It
defines:

- syntax, indentation, declarations, typing, and operators;
- built-in types and engine classes;
- lifecycle methods and scene-tree timing;
- annotations, exports, signals, RPC, coroutines, and documentation comments;
- loading, node lookup, groups, freeing, and physics movement APIs;
- exact distinctions such as `get_node()` versus `get_node_or_null()` and
  `queue_free()` versus `free()`.

Then read the relevant physics, shader, or server guide before calling those
systems. GDScript syntax alone does not establish the semantics of a physics
body or a rendering RID.

### 4.4 Read the shader guide first when

The output is `.gdshader` source or a shader uniform is being configured. It
defines:

- shader types and stages;
- built-in variables and functions;
- coordinate spaces, units, read/write direction, and renderer restrictions;
- uniforms, hints, render modes, varyings, preprocessing, and texture usage;
- CanvasItem, Spatial, Particle, Sky, Fog, and Texture Blit differences.

Then read the `.tres` guide if the shader is saved in a material resource, or
the RenderingServer guide if the shader and material are created by RID.

### 4.5 Read the physics guides first when

The feature involves collisions, movement, overlap detection, forces, rigid
simulation, raycasts, shape casts, or physics materials. Read:

1. `physics.md` for shared rules;
2. exactly one of `physics_2d.md` or
   `physics_3d.md`;
3. the matching PhysicsServer guide only if using low-level RIDs.

Do not use the PhysicsServer guides as a shortcut for understanding ordinary
`CharacterBody`, `RigidBody`, `Area`, or collision-shape node behavior.

### 4.6 Read a server guide first when

The code intentionally bypasses scene nodes and creates server objects with
RIDs. Server guides are required when the code calls methods such as:

```gdscript
PhysicsServer2D.body_create()
PhysicsServer3D.body_create()
RenderingServer.canvas_item_create()
RenderingServer.instance_create()
```

Then also read GDScript for ownership and timing, the relevant physics guide
for simulation semantics, or the shader/resource guide for the data assigned
to the server objects.

## 5. Cross-format authoring workflows

### Workflow A: create a scene with a script

1. Read the `.tscn` guide.
2. Read the GDScript guide.
3. Confirm the script's `extends` class matches the root node type.
4. Confirm every `@export`, node path, signal connection, and resource path.
5. If the script moves or queries physics, read the shared physics guide and
   the matching 2D/3D guide.
6. Generate the script before attaching it in the scene.
7. Generate the scene with valid external-resource paths and local IDs.
8. Verify that every connection's source, signal, target, and method exist.

### Workflow B: create a material and shader

1. Read the shader guide and choose the correct `shader_type`.
2. Define uniforms with exact types and hints.
3. Read the `.tres` guide if the material is persisted.
4. Create a `Shader` sub-resource, then a compatible material resource.
5. Set material parameters using names and Variant values matching the shader.
6. Reference the material from a `.tscn` or load it from GDScript.
7. Read the RenderingServer guide only if the material is created or assigned
   through RIDs rather than ordinary resources.

### Workflow C: create a physics object

1. Read the shared physics guide.
2. Read the 2D or 3D guide for the dimension-specific body, shape, and query.
3. Choose the correct body family before choosing a class.
4. Define collision layers and masks from the project's existing contract.
5. Use `.tres` for reusable shape/material resources and `.tscn` for nodes.
6. Use GDScript for physics timing, movement, forces, and callbacks.
7. Use the matching PhysicsServer guide only when node APIs are insufficient.
8. If the object is server-created and visible, read the RenderingServer guide
   and define an explicit physics-to-render transform synchronization path.

### Workflow D: create a server-rendered object

1. Read the RenderingServer guide.
2. Decide whether the object is a 2D canvas item or a 3D scenario instance.
3. Create or obtain the required texture, shader, material, mesh, or particle
   RIDs.
4. Keep strong references to source resources and store every owned RID.
5. Attach the object to the correct canvas/scenario and viewport path.
6. Set transforms, visibility, culling, materials, and custom AABBs.
7. Reset or configure physics interpolation when transforms originate in
   physics processing.
8. Free instances before their bases and never free world-owned RIDs.

### Workflow E: create a serialized scene/resource plus runtime behavior

Use this order:

1. Determine which data is persistent and which data is runtime-only.
2. Put reusable data in `.tres`.
3. Put node hierarchy and references in `.tscn`.
4. Put behavior in `.gd`.
5. Put GPU code in `.gdshader`.
6. Keep server-created RIDs out of text files unless the file format and
   resource type explicitly support that serialization.
7. Recreate runtime server state from serialized resources during initialization.

## 6. Serialization versus runtime state

The shared guide defines the dependency and ownership rules for separating
`.tscn`, `.tres`, `.gd`, `.gdshader`, physics runtime state, and rendering
runtime state. Use it before persisting or recreating server objects.

## 7. End-to-end validation checklist

Start with the common checklist in
[`shared_concepts.md`](shared_concepts.md), then run the
format-, dimension-, or server-specific checklist in every guide involved.

## 8. Recommended reading order for an AI model

For a new feature, use this sequence:

1. Read this entry point.
2. Inspect the project and establish the version, renderer, backend, local
   conventions, and validation commands.
3. Identify the primary output format and the smallest set of required guides.
4. Retrieve exact target-version documentation for every API fact not fully
   established by those guides.
5. Separate verified facts from assumptions before generating.
6. Generate the smallest valid artifact first and preserve unrelated existing
   content and engine-managed metadata.
7. Add optional features only after the base structure is correct.
8. Run the strongest available target-engine and project validation.
9. Re-read the checklist for every involved subsystem.
10. Inspect the final files as one dependency graph and report any validation
    that could not be performed.

The guides are complementary. The strongest result comes from combining
serialization rules, language/API semantics, resource lifetime, scene
structure, and runtime timing rather than treating any one guide as a
complete substitute for the others.
