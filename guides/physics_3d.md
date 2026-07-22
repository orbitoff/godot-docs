# Godot 4.7 3D Physics Authoring Guide

This guide contains only 3D-specific physics information. Read
`physics.md` first for shared physics concepts such as timing,
body-family selection, collision layers/masks, areas, rigid-body semantics,
queries, physics materials, and performance.

Cross-format ownership, identifier, coordinate-space, and validation rules are
in [`shared_concepts.md`](shared_concepts.md).

## 1. 3D coordinate and class model

3D physics uses `Vector3`, `Basis`, `Transform3D`, and `Node3D` coordinates.
The default 3D gravity direction is downward along negative Y:

```gdscript
var gravity := Vector3(0, -9.8, 0)
```

The 3D collision class hierarchy is:

```text
CollisionObject3D
├── Area3D
└── PhysicsBody3D
    ├── StaticBody3D
    ├── AnimatableBody3D
    ├── CharacterBody3D
    └── RigidBody3D
```

`RayCast3D` and `ShapeCast3D` are query nodes, not collision bodies.
`SoftBody3D` is also separate from this hierarchy: it inherits
`MeshInstance3D`, derives its collision and simulation from its mesh, and is
not an ordinary `PhysicsBody3D` with a `CollisionShape3D` child.

## 2. 3D collision shape resources

Use these `Shape3D` resources:

| Shape | Use and constraints |
| --- | --- |
| `BoxShape3D` | Rectangular solid with configurable size; efficient for crates, walls, and architectural pieces. |
| `SphereShape3D` | Uniform-radius solid; efficient for balls and radial objects. |
| `CapsuleShape3D` | Rounded elongated solid; a strong default for character bodies. |
| `CylinderShape3D` | Cylindrical solid; useful for rotationally symmetric objects, but can be less stable in some GodotPhysics cases. |
| `SeparationRayShape3D` | Character-oriented separation ray; it is not a general solid volume. |
| `WorldBoundaryShape3D` | Infinite plane boundary; useful for world limits. |
| `ConvexPolygonShape3D` | Custom convex solid; suitable for dynamic bodies when kept reasonably simple. |
| `ConcavePolygonShape3D` | Trimesh surface geometry; intended for static bodies and level collision. |
| `HeightMapShape3D` | Height-field terrain representation; useful for terrain-like static collision with height data. |

Primitive shapes are preferred for `RigidBody3D` and `CharacterBody3D`.
Concave polygon shapes are hollow surfaces rather than filled volumes and are
normally valid only on static bodies. A concave mesh can allow objects to
exist inside or outside its surface; do not use it as a general character
volume.

## 3. CollisionShape3D

`CollisionShape3D` references one `Shape3D` resource:

```text
[node name="CollisionShape3D" type="CollisionShape3D" parent="Player"]
shape = SubResource("CapsuleShape3D_player")
```

Collision shape nodes must be direct children of the `CollisionObject3D`.
Indirect descendants are ignored as that object's shapes. Multiple shapes on a
body form a compound collider and do not collide with one another.

Do not resize a shape by non-uniformly scaling the body or collision shape.
Change `BoxShape3D.size`, `SphereShape3D.radius`, `CapsuleShape3D.radius` and
`height`, or the corresponding shape property instead. Keep collision-object
scale uniform.

For dynamic objects, use a small number of primitive or convex shapes. For
static level geometry, a simplified concave mesh is often appropriate.

## 4. CharacterBody3D

`CharacterBody3D` is script-controlled. It detects collisions and affects
other bodies, but physics does not apply gravity or friction automatically.
Game code computes the desired velocity and calls `move_and_slide()`.

Minimal grounded pattern:

```gdscript
extends CharacterBody3D

@export var speed := 5.0
@export var gravity := 9.8
@export var jump_velocity := 4.5

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= gravity * delta

	if Input.is_action_just_pressed("jump") and is_on_floor():
		velocity.y = jump_velocity

	var input_2d := Input.get_vector(
		"move_left",
		"move_right",
		"move_forward",
		"move_back",
	)
	var direction := Vector3(input_2d.x, 0.0, input_2d.y)
	velocity.x = direction.x * speed
	velocity.z = direction.z * speed
	move_and_slide()
```

`move_and_slide()` uses `velocity` in units per second, performs slide
collisions, and updates `velocity`. Do not multiply velocity by `delta` for
this call.

Important properties:

| Property | Meaning |
| --- | --- |
| `velocity` | Desired/current linear velocity in 3D units per second. |
| `motion_mode` | `MOTION_MODE_GROUNDED` recognizes floor, wall, and ceiling; `MOTION_MODE_FLOATING` treats all contacts as walls and is suitable for space/top-down movement. |
| `up_direction` | Defines the floor-facing direction. Default is `Vector3(0, 1, 0)`. |
| `floor_max_angle` | Maximum contact angle classified as a floor, in radians. |
| `floor_stop_on_slope` | Prevents sliding down a slope while standing still when enabled. |
| `floor_snap_length` | Distance used to keep the body attached to sloped floors. |
| `wall_min_slide_angle` | Minimum angle for wall sliding. |
| `max_slides` | Maximum slide-collision iterations per movement call. |
| `safe_margin` | Collision recovery margin used for near contacts. |
| `floor_constant_speed` | Keeps speed constant on slopes when enabled. |
| `slide_on_ceiling` | Controls whether upward motion slides along ceilings. |
| `floor_block_on_wall` | Prevents a floor classification when the body is also blocked by a wall according to the class rules. |
| `platform_floor_layers` | Layers of moving platforms that can transfer floor motion. |
| `platform_wall_layers` | Layers of moving platforms that can transfer wall motion. |
| `platform_on_leave` | Controls how platform velocity is handled when leaving. |

After movement, use `is_on_floor()`, `is_on_wall()`, and `is_on_ceiling()`.
`*_only()` variants require that the corresponding contact category is the
only category reported for the last motion. Use `get_floor_normal()`,
`get_wall_normal()`, `get_real_velocity()`, and slide-collision accessors for
detailed contact results.

For custom response:

```gdscript
var collision := move_and_collide(velocity * delta)
if collision:
	velocity = velocity.bounce(collision.get_normal())
```

`move_and_collide()` receives a relative `Vector3` motion, stops at the first
collision, and returns `KinematicCollision3D` or `null`. It does not perform
the automatic slide loop of `move_and_slide()`.

## 5. RigidBody3D

`RigidBody3D` is fully simulated. Apply forces, impulses, torques, or
integration-state changes instead of setting its transform every physics frame.

3D forces and impulses use `Vector3`; angular velocity and torque are also
3D vectors:

```gdscript
extends RigidBody3D

func launch(direction: Vector3, impulse_strength: float) -> void:
	apply_central_impulse(direction.normalized() * impulse_strength)
```

Use:

- `apply_central_force()` for a force through the center;
- `apply_force(force, position)` for force at a position;
- `apply_central_impulse()` for an immediate linear impulse;
- `apply_impulse(impulse, position)` for an impulse that can add rotation;
- `apply_torque()` and `apply_torque_impulse()` for angular changes;
- `add_constant_*()` for forces/torques that persist until removed.

Important 3D properties include `mass`, `linear_velocity`,
`angular_velocity`, `gravity_scale`, `linear_damp`, `angular_damp`,
`lock_rotation`, `freeze`, `freeze_mode`, `can_sleep`, `sleeping`,
`continuous_cd`, `contact_monitor`, `max_contacts_reported`, and
`physics_material_override`.

`_integrate_forces(state: PhysicsDirectBodyState3D)` is the preferred callback
for direct control of simulated state. `custom_integrator` bypasses default
force integration when intentionally enabled.

`body_entered` and related contact reporting require contact monitoring and a
sufficient maximum contact count.

## 6. Area3D

`Area3D` detects `CollisionObject3D` overlaps and can override local 3D
gravity/damping and audio effects. It does not provide solid collision
response.

Common signals:

- `body_entered(body)`;
- `body_exited(body)`;
- `area_entered(area)`;
- `area_exited(area)`;
- `body_shape_entered(body_rid, body, body_shape_index, local_shape_index)`;
- `body_shape_exited(...)`;
- `area_shape_entered(...)`;
- `area_shape_exited(...)`.

Use `get_overlapping_bodies()` and `get_overlapping_areas()` with monitoring
enabled. These lists represent the tracked physics state at an update
boundary, not an unrestricted immediate geometry test.

Area override modes are:

- **Combine**;
- **Replace**;
- **Combine-Replace**;
- **Replace-Combine**.

Higher-priority areas are processed first. Area3D can override gravity,
gravity direction, linear/angular damping, and 3D audio/reverb/wind-related
properties exposed by the class. Point gravity uses `gravity_point_center` and
`gravity_point_unit_distance`.

Avoid placing a hollow `ConcavePolygonShape3D` in an Area3D unless its hollow
surface semantics are intended. Use convex or primitive shapes for filled
trigger volumes.

## 7. AnimatableBody3D

`AnimatableBody3D` inherits static-body behavior but is intended to be moved
manually by code or animation. The engine estimates its linear and angular
velocity and uses that motion to affect other bodies in its path.

Use it for moving platforms, doors, elevators, and similar objects that should
not be pushed by external forces. When animation drives the movement, process
the animation during physics when physics-frame synchronization is required.
Do not combine `sync_to_physics` animation movement with
`PhysicsBody3D.move_and_collide()` on the same body.

## 8. RayCast3D and ShapeCast3D

`RayCast3D` casts from its origin to local `target_position` and reports the
closest hit. It updates every physics frame and retains the result until the
next update.

Key properties:

- `enabled`;
- `target_position: Vector3`;
- `collision_mask`;
- `collide_with_bodies`;
- `collide_with_areas`;
- `exclude_parent`;
- `hit_from_inside`;
- `hit_back_faces`.

Useful methods:

- `is_colliding()`;
- `get_collider()`;
- `get_collider_rid()`;
- `get_collider_shape()`;
- `get_collision_point()`;
- `get_collision_normal()`;
- `get_collision_face_index()`;
- `force_raycast_update()`;
- `add_exception()`/`remove_exception()`.

`hit_back_faces` matters for concave mesh surfaces. `hit_from_inside` controls
whether a ray originating inside a shape can report that shape.

`ShapeCast3D` sweeps a `Shape3D` through 3D space and is useful for character
clearance, thick movement tests, and volume detection. Use its collision
results rather than treating it as a physical body.

## 9. 3D direct-space queries

Inside `_physics_process()`:

```gdscript
func _physics_process(_delta: float) -> void:
	var space_state := get_world_3d().direct_space_state
	var query := PhysicsRayQueryParameters3D.create(
		global_position,
		global_position + Vector3.DOWN * 100.0,
	)
	query.collision_mask = 1 << 0
	query.collide_with_areas = true
	query.exclude = [self]
	var result := space_state.intersect_ray(query)
	if not result.is_empty():
		print(result.position, result.normal, result.collider)
```

3D query positions are world-space `Vector3` values. A ray result dictionary
can contain `position`, `normal`, `collider`, `collider_id`, `rid`, `shape`,
and `metadata`. Check for an empty result first.

The 3D result may also expose a face index for mesh/concave hits through APIs
that support it. Use `collide_with_areas = true` when areas should be included.

## 10. SoftBody3D

`SoftBody3D` is a deformable 3D physics mesh for cloth, rubber, and other
flexible objects. It is based on `MeshInstance3D` rather than an ordinary
`PhysicsBody3D`, so its simulation is driven by mesh geometry and soft-body
parameters rather than a `CollisionShape3D` child.

Important properties include `total_mass`, `linear_stiffness`,
`simulation_precision`, `damping_coefficient`, `drag_coefficient`,
`pressure_coefficient`, `shrinking_factor`, `collision_layer`,
`collision_mask`, and `parent_collision_ignore`.

Soft-body points can be pinned to nodes with point indices and attachment
paths. The mesh topology and pinned points must be valid for the intended
deformation. Closed meshes are required for pressure behavior, and additional
subdivision improves deformation detail at a simulation cost. Physics
interpolation currently does not affect soft bodies. Godot recommends Jolt
Physics for faster and more reliable soft-body behavior.

Area wind properties can affect `SoftBody3D` when an area supplies a wind
source, magnitude, and attenuation.

## 11. 3D collision geometry

For imported meshes, create collision from simplified source geometry rather
than using the render mesh unchanged. The editor can generate:

- one convex collision sibling;
- multiple convex collision siblings using decomposition;
- a trimesh static body;
- a trimesh collision sibling.

Use one convex shape for small simple objects, multiple convex shapes for
moderately complex concave objects, and concave trimesh only for static level
geometry. Concave geometry is hollow and can produce unexpected results in
areas or dynamic bodies.

`HeightMapShape3D` is appropriate for height-field terrain, not arbitrary
overhangs or caves. Use mesh/convex composition when terrain needs true
overhang volume.

## 12. VehicleBody3D

`VehicleBody3D` is a specialized `RigidBody3D` for raycast-style car
simulation. It requires a main collision shape and one `VehicleWheel3D` child
per wheel. The visual vehicle mesh should generally omit wheel meshes.

Control it with `engine_force`, `brake`, and `steering`. Do not set the
vehicle's position or orientation directly during simulation. Its origin
affects the center of gravity; keeping the origin low and placing the
visual/body geometry above it can make the vehicle more grounded.

The local forward direction is `Vector3.MODEL_FRONT`. VehicleBody3D has known
limitations and is not intended to provide realistic advanced vehicle
simulation. Use custom `CharacterBody3D` or `RigidBody3D` integration when
more control is required.

## 13. 3D joints

3D projects commonly use `Joint3D` subclasses, `PhysicalBone3D`, and
`VehicleBody3D`/vehicle wheels. Joint anchors, axes, limits, and connected
body paths are all 3D `Transform3D`/`Vector3` data.

Vehicle simulation is sensitive to high speeds, wheel geometry, mass, friction,
and physics tick rate. Continuous collision detection and a higher tick rate
can reduce tunneling, but do not treat them as a substitute for suitable
vehicle dimensions and simplified collision geometry.

Use `Jolt` only when the project explicitly selects and validates that 3D
physics backend. Backend changes can alter stability, cylinder behavior,
vehicle behavior, and solver results.

## 14. 3D physics backends and stability

Projects created in Godot 4.6 and later use Jolt Physics by default, while
projects upgraded from earlier versions can retain GodotPhysics3D. Always read
the project's `physics/3d/physics_engine` setting instead of assuming either
backend. Backend-specific behavior must not be assumed portable without
testing.

Known sensitive cases include:

- cylinder collision shapes;
- stacked rigid bodies;
- high-speed vehicles;
- detailed concave meshes;
- thin resting bodies;
- very large world coordinates.

Prefer boxes or capsules for characters when reliability is more important than
exact cylindrical appearance.

## 15. 3D validation checklist

- The body has direct `CollisionShape3D` children.
- Each shape uses an appropriate `Shape3D` resource.
- Character movement uses `Vector3` and occurs in `_physics_process()`.
- `move_and_slide()` receives velocity without multiplying by `delta`.
- `move_and_collide()` receives motion multiplied by `delta`.
- `up_direction` and floor-angle settings match the world orientation.
- Area trigger volumes do not use hollow concave shapes accidentally.
- Rigid-body contact monitoring is enabled when contact signals are used.
- Query coordinates are global `Vector3` values.
- Ray area/body filters and back-face behavior are intentional.
- Dynamic objects use primitive/convex shapes where possible.
- Static level collision is simplified and appropriately concave.
- The selected 3D physics backend has been tested for the project's behavior.
