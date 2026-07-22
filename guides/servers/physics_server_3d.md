# PhysicsServer3D Authoring Guide (Godot 4.7)

This guide explains how to create and control 3D physics objects directly
through `PhysicsServer3D`, without creating `Node3D`, `Area3D`,
`RigidBody3D`, or other scene-tree nodes. It is intended for AI-generated
GDScript and for node-independent, procedural, or performance-sensitive
systems.

For ordinary gameplay, use the node-level APIs described by the shared physics
and 3D physics guides. `PhysicsServer3D` is a low-level API based on opaque
`RID` handles; it does not provide scene-tree ownership, rendering, or
automatic cleanup.

Read [`../shared_concepts.md`](../shared_concepts.md) for
the shared rules on project assumptions, typed values, RID ownership, resource
lifetime, timing, coordinate spaces, and validation.

## 1. What the server represents

`PhysicsServer3D` is the global Godot server responsible for 3D spaces, shapes,
areas, bodies, joints, and soft bodies. Nodes such as `RigidBody3D`,
`Area3D`, and `SoftBody3D` wrap server objects at a higher level.

A server-created object:

- can exist without a scene-tree node;
- is identified by an opaque `RID`;
- must be assigned to a physics space;
- does not render itself;
- does not automatically synchronize a `Node3D` or `MeshInstance3D`;
- must be explicitly destroyed with `PhysicsServer3D.free_rid(rid)`.

Use the server for custom wrappers, procedural simulations, node-independent
objects, and specialized high-volume systems. The lower level means that
visual synchronization, callbacks, filtering, resource lifetime, and cleanup
must all be designed explicitly.

## 2. RIDs and lifetime

The shared concepts guide defines the general RID and ownership contract.
For this server, create RIDs only through server APIs or obtain them from valid
resources:

```gdscript
var space: RID = PhysicsServer3D.space_create()
var shape: RID = PhysicsServer3D.box_shape_create()
var body: RID = PhysicsServer3D.body_create()
var area: RID = PhysicsServer3D.area_create()
var joint: RID = PhysicsServer3D.joint_create()
```

Keep strong references to `Shape3D`, `Mesh`, and other reference-counted
resources whose RIDs are being used. An RID is only a handle and does not keep
the source resource alive.

Free dependent objects before the objects they use:

```gdscript
PhysicsServer3D.free_rid(joint)
PhysicsServer3D.free_rid(body)
PhysicsServer3D.free_rid(area)
PhysicsServer3D.free_rid(shape)
PhysicsServer3D.free_rid(space)
```

Only free `space` when it was created by your system with `space_create()`.
Never free `get_world_3d().space`; the world owns it.

Clear callbacks before freeing their targets, do not free a RID twice, and do
not call server methods with a freed or invalid RID.

## 3. Spaces, direct state, and timing

Use an independent space from `space_create()`, or the current world:

```gdscript
var space: RID = get_world_3d().space
```

Space methods:

- `space_set_active(space, active)`;
- `space_is_active(space)`;
- `space_set_param(space, param, value)`;
- `space_get_param(space, param)`;
- `space_get_direct_state(space)`, returning
  `PhysicsDirectSpaceState3D`.

`SpaceParameter` controls contact recycling and separation thresholds,
penetration tolerance, contact and constraint bias, sleep thresholds, sleep
time, and solver iterations. Increasing solver iterations can improve
constraint/contact accuracy at a CPU cost.

Physics server state is synchronized with fixed physics processing. Follow the
shared timing rules and use `_physics_process()` or documented physics
callbacks for simulation work. Avoid repeatedly polling getters from
render-time code when they can synchronize the physics server.

## 4. 3D shapes

Shape creation methods include:

| Method | Shape |
|---|---|
| `world_boundary_shape_create()` | Infinite plane boundary. |
| `separation_ray_shape_create()` | Separation ray, useful for character-style contact. |
| `sphere_shape_create()` | Sphere. |
| `box_shape_create()` | Box. |
| `capsule_shape_create()` | Capsule. |
| `cylinder_shape_create()` | Cylinder. |
| `convex_polygon_shape_create()` | Convex polygon/polyhedron shape. |
| `concave_polygon_shape_create()` | Concave triangle-mesh shape. |
| `heightmap_shape_create()` | Heightmap collision shape. |
| `custom_shape_create()` | Custom shape creation hook; backend support and data requirements must be checked before use. |

Set geometry with `shape_set_data(shape, data)`, retrieve it with
`shape_get_data(shape)`, and inspect the type with `shape_get_type(shape)`.
`shape_set_margin()` and `shape_get_margin()` configure/query the collision
margin where supported.

Do not invent payload formats from method names. Use the matching shape
resource documentation (`SphereShape3D`, `BoxShape3D`, `CapsuleShape3D`,
`ConvexPolygonShape3D`, `ConcavePolygonShape3D`, `HeightMapShape3D`, and
others) for exact data types. Primitive shapes are preferred for dynamic
bodies; concave triangle meshes are generally for static geometry.

Attach shapes with `body_add_shape()` or `area_add_shape()`. Each attachment
has a local `Transform3D`, a stable array index, and a disabled flag.
Use `body_set_shape_transform()`, `area_set_shape_transform()`,
`body_set_shape_disabled()`, `area_set_shape_disabled()`, removal methods, or
the clear methods to manage attachments.

## 5. Creating and configuring a body

The normal sequence is:

1. Create with `body_create()`.
2. Set a `BodyMode`.
3. Attach one or more shapes.
4. Assign a space.
5. Set the initial transform and body parameters.
6. Configure callbacks, filtering, and optional CCD.
7. Keep all required RIDs and resources alive.

```gdscript
extends Node3D

var body: RID
var shape: RID

func _ready() -> void:
    body = PhysicsServer3D.body_create()
    shape = PhysicsServer3D.box_shape_create()
    PhysicsServer3D.shape_set_data(shape, Vector3(1.0, 1.0, 1.0)) # half-extents

    PhysicsServer3D.body_set_mode(body, PhysicsServer3D.BODY_MODE_RIGID)
    PhysicsServer3D.body_add_shape(body, shape)
    PhysicsServer3D.body_set_space(body, get_world_3d().space)
    PhysicsServer3D.body_set_state(
        body,
        PhysicsServer3D.BODY_STATE_TRANSFORM,
        Transform3D(Basis.IDENTITY, Vector3(0.0, 2.0, 0.0))
    )

func _exit_tree() -> void:
    if body.is_valid():
        PhysicsServer3D.free_rid(body)
    if shape.is_valid():
        PhysicsServer3D.free_rid(shape)
```

`BodyMode` values are:

| Constant | Meaning |
|---|---|
| `BODY_MODE_STATIC` | Moved by user code and not swept through collisions. |
| `BODY_MODE_KINEMATIC` | Moved by user code with path collision behavior. |
| `BODY_MODE_RIGID` | Simulated using forces, impulses, contacts, and constraints. |
| `BODY_MODE_RIGID_LINEAR` | Rigid-like body that does not rotate. |

Configure:

- `body_set_space()`;
- `body_set_state()`;
- `body_set_collision_layer()` and `body_set_collision_mask()`;
- `body_set_collision_priority()`;
- `body_set_ray_pickable()`;
- `body_attach_object_instance_id()`;
- `body_add_collision_exception()` and
  `body_remove_collision_exception()`.

`body_attach_object_instance_id()` attaches an application identity returned
as the `instance_id` argument of an area's body-monitor callback. Use
`area_attach_object_instance_id()` for IDs returned by area-area monitor
callbacks. This metadata is not a strong reference.

## 6. Body parameters and state

`body_set_param()` accepts `BodyParameter` values:

| Parameter | Meaning |
|---|---|
| `BODY_PARAM_BOUNCE` | Restitution/bounce factor. |
| `BODY_PARAM_FRICTION` | Friction coefficient. |
| `BODY_PARAM_MASS` | Mass; can trigger automatic mass-property recalculation. |
| `BODY_PARAM_INERTIA` | Rotational inertia; non-positive values request automatic calculation. |
| `BODY_PARAM_CENTER_OF_MASS` | Local center of mass. |
| `BODY_PARAM_GRAVITY_SCALE` | Gravity multiplier. |
| `BODY_PARAM_LINEAR_DAMP_MODE` | Combine or replace environmental linear damping. |
| `BODY_PARAM_ANGULAR_DAMP_MODE` | Combine or replace environmental angular damping. |
| `BODY_PARAM_LINEAR_DAMP` | Linear damping factor. |
| `BODY_PARAM_ANGULAR_DAMP` | Angular damping factor. |

`BodyDampMode` is `BODY_DAMP_MODE_COMBINE` or
`BODY_DAMP_MODE_REPLACE`.

`BodyState` values are:

- `BODY_STATE_TRANSFORM` (`Transform3D`);
- `BODY_STATE_LINEAR_VELOCITY` (`Vector3`);
- `BODY_STATE_ANGULAR_VELOCITY` (`Vector3`);
- `BODY_STATE_SLEEPING` (`bool`);
- `BODY_STATE_CAN_SLEEP` (`bool`).

Force and impulse methods:

- `body_apply_central_force()`;
- `body_apply_central_impulse()`;
- `body_apply_force()` and `body_apply_impulse()` at a position;
- `body_apply_torque()` and `body_apply_torque_impulse()`;
- `body_add_constant_central_force()`;
- `body_add_constant_force()`;
- `body_add_constant_torque()`;
- `body_set_axis_velocity()`.

3D-only body controls include:

- `body_set_axis_lock()` and `body_is_axis_locked()` for X/Y/Z lock axes;
- `body_set_enable_continuous_collision_detection()`;
- `body_is_continuous_collision_detection_enabled()`;
- `body_set_ray_pickable()`.

CCD predicts intermediate collisions for fast-moving bodies. It costs more
than discrete detection and should be enabled selectively.

## 7. Force integration and state callbacks

`body_set_force_integration_callback(body, callable, userdata)` invokes a
`Callable` every physics tick before standard integration. Without userdata:

```gdscript
func integrate_body(state: PhysicsDirectBodyState3D) -> void:
    state.linear_velocity += Vector3.UP * 2.0
```

With userdata, the callable receives `(state, userdata)`. The state can read
and modify the body's current physics state.

`body_set_omit_force_integration(body, true)` disables standard force,
torque, and damping integration. Use it only when the callback performs the
replacement integration itself.

`body_set_state_sync_callback(body, callable)` invokes a callable after an
active physics tick with a `PhysicsDirectBodyState3D`. Use it to copy the
simulated transform to a custom visual object. Clear callbacks with
`Callable()`, and do not retain the direct state after the callback.

## 8. Areas and monitoring

Create an area with `area_create()`, attach shapes, assign a space, and set its
transform. Configure:

- collision layer and mask;
- `area_set_monitorable()`;
- `area_set_monitor_callback()`;
- `area_set_area_monitor_callback()`;
- `area_set_ray_pickable()`;
- `area_attach_object_instance_id()`.

The body monitor callback receives:

```gdscript
func area_body_event(
    status: int,
    body_rid: RID,
    instance_id: int,
    body_shape_index: int,
    area_shape_index: int
) -> void:
    if status == PhysicsServer3D.AREA_BODY_ADDED:
        pass
    elif status == PhysicsServer3D.AREA_BODY_REMOVED:
        pass
```

Events are shape-level. Track shape pairs when whole-body enter/exit behavior
is required. `AREA_BODY_ADDED` means a body shape entered; `AREA_BODY_REMOVED`
means a body shape exited.

Area parameters include gravity override mode, gravity strength, gravity
direction or point behavior, point-gravity unit distance, linear and angular
damping overrides, and priority. `AreaSpaceOverrideMode` determines whether
an area's values are disabled, combined, combined then terminating,
replaced and terminating, or replaced while continuing.

## 9. Motion tests and direct queries

`body_test_motion(body, parameters, result)` tests a proposed motion without
committing it. Use `PhysicsTestMotionParameters3D` and optionally
`PhysicsTestMotionResult3D`.

For direct space queries:

```gdscript
var state := PhysicsServer3D.space_get_direct_state(get_world_3d().space)
var hit := state.intersect_ray(query_parameters)
```

`PhysicsDirectSpaceState3D` provides ray, point, shape, and motion-collision
queries. Query during `_physics_process()` or a server-provided physics
callback while the space is safe to access. Avoid render-time queries that
can race or force synchronization.

## 10. Joints

Create a joint with `joint_create()`, then use one of:

- `joint_make_pin(joint, body_a, local_a, body_b, local_b)`;
- `joint_make_hinge(joint, body_a, transform_a, body_b, transform_b)`;
- `joint_make_slider(joint, body_a, transform_a, body_b, transform_b)`;
- `joint_make_cone_twist(joint, body_a, transform_a, body_b, transform_b)`;
- `joint_make_generic_6dof(joint, body_a, transform_a, body_b, transform_b)`.

Use `joint_get_type()`, `joint_disable_collisions_between_bodies()`,
`joint_set_solver_priority()`, and `joint_clear()` as needed.

The joint families are:

- pin: keeps anchor points together;
- hinge: permits rotation around one axis, with optional limits and motor;
- slider: constrains motion to an axis with linear and angular limits;
- cone-twist: limits swing and twist angles;
- generic 6DOF: independently configures the three linear and three angular
  axes.

Use the matching parameter methods:

- `pin_joint_set_param()`;
- `hinge_joint_set_param()` and `hinge_joint_set_flag()`;
- `slider_joint_set_param()`;
- `cone_twist_joint_set_param()`;
- `generic_6dof_joint_set_param()` and
  `generic_6dof_joint_set_flag()`.

3D joint parameter values include limits, softness, restitution, damping,
motors, spring settings, and force limits. Several advanced softness,
relaxation, bias, and spring parameters are backend-dependent; verify the
selected physics backend before relying on them. Parameters documented as
GodotPhysics3D-only are ignored by Jolt Physics.

## 11. Soft bodies

`soft_body_create()` creates a server-level soft body. Configure it with:

- `soft_body_set_mesh()`;
- `soft_body_set_space()`;
- `soft_body_set_transform()`;
- collision layer and mask setters;
- total mass, damping, drag, pressure, shrinking factor, linear stiffness,
  and simulation precision setters;
- `soft_body_pin_point()`, `soft_body_is_point_pinned()`,
  `soft_body_remove_all_pinned_points()`, and `soft_body_move_point()`;
- force, impulse, point-force, and point-impulse methods;
- `soft_body_update_rendering_server()` when using the matching rendering
  integration path.

Soft-body methods operate on mesh points rather than rigid-body transforms.
The mesh resource and any rendering object must remain alive. Prefer the Jolt
backend when the project needs stronger soft-body behavior, as documented by
the 3D physics guide.

## 12. Process information and activation

`set_active(active)` controls global server processing. It is not a
per-object pause mechanism.

`get_process_info()` reports:

- `INFO_ACTIVE_OBJECTS`: active non-sleeping objects;
- `INFO_COLLISION_PAIRS`: possible collision pairs;
- `INFO_ISLAND_COUNT`: solver islands.

Use these values for diagnostics and profiling, not gameplay state.

## 13. Complete minimal body example

```gdscript
extends Node3D

var body: RID
var shape: RID

func _ready() -> void:
    body = PhysicsServer3D.body_create()
    shape = PhysicsServer3D.sphere_shape_create()
    PhysicsServer3D.shape_set_data(shape, 0.5)
    PhysicsServer3D.body_set_mode(body, PhysicsServer3D.BODY_MODE_RIGID)
    PhysicsServer3D.body_add_shape(body, shape)
    PhysicsServer3D.body_set_space(body, get_world_3d().space)
    PhysicsServer3D.body_set_collision_layer(body, 1)
    PhysicsServer3D.body_set_collision_mask(body, 1)
    PhysicsServer3D.body_set_state(
        body,
        PhysicsServer3D.BODY_STATE_TRANSFORM,
        Transform3D(Basis.IDENTITY, Vector3(0.0, 3.0, 0.0))
    )

func _physics_process(_delta: float) -> void:
    var transform: Transform3D = PhysicsServer3D.body_get_state(
        body,
        PhysicsServer3D.BODY_STATE_TRANSFORM
    )
    # Copy `transform` to a custom Node3D or rendering-server instance here.

func _exit_tree() -> void:
    if body.is_valid():
        PhysicsServer3D.free_rid(body)
    if shape.is_valid():
        PhysicsServer3D.free_rid(shape)
```

## 14. Validation checklist

Before generating or reviewing server-level 3D code, verify:

- The common ownership, identifier, lifetime, timing, and type checklist in
  `../shared_concepts.md` passes.
- All bodies, areas, joints, and soft bodies use the intended space.
- Shape data matches the exact 3D shape type.
- Dynamic bodies use appropriate primitive or convex shapes.
- Collision layers and masks are intentional.
- Callback signatures match the documented `Callable` arguments.
- Force integration is not omitted unless custom integration replaces it.
- State callbacks do not retain direct state objects after the callback.
- Server-created objects have an explicit visual synchronization path.
- Backend-specific joint and soft-body behavior is not assumed to be portable.
