import carla
import random
import time

# Connect
client = carla.Client("localhost", 2000)
client.set_timeout(10.0)
world  = client.get_world()
bp_lib = world.get_blueprint_library()

spawned_actors = []

# spawn a vehicle at a random spawn point
def spawn_vehicle(model="vehicle.tesla.model3", spawn_index=1):
    bp  = bp_lib.find(model)
    spawn_point = world.get_map().get_spawn_points()[spawn_index]
    actor = world.try_spawn_actor(bp, spawn_point)
    actor.set_autopilot(True)   # uses CARLA Traffic Manager
    spawned_actors.append(actor)
    print(f"Spawned {model} at spawn point {spawn_index}")
    return actor

# spawn a pedestrian
def spawn_pedestrian(x, y, z=0.5):
    ped_bps = bp_lib.filter("walker.pedestrian.*")
    bp      = random.choice(ped_bps)
    tf      = carla.Transform(carla.Location(x=x, y=y, z=z))
    walker  = world.try_spawn_actor(bp, tf)
    spawned_actors.append(walker)
    # Give the walker a simple AI controller
    ctrl_bp    = bp_lib.find("controller.ai.walker")
    controller = world.spawn_actor(ctrl_bp,
                    carla.Transform(), attach_to=walker)
    spawned_actors.append(controller)
    controller.start()
    controller.go_to_location(
        world.get_random_location_from_navigation())
    controller.set_max_speed(1.4)   # ~normal walking speed m/s
    print(f"Spawned pedestrian at ({x}, {y})")
    return walker, controller

# move a vehicle to exact waypoints 
def teleport_vehicle(actor, x, y, yaw=0.0):
    """Instantly move vehicle to (x,y) facing yaw degrees."""
    tf = carla.Transform(
        carla.Location(x=x, y=y, z=0.5),
        carla.Rotation(yaw=yaw))
    actor.set_transform(tf)

# drive vehicle along a list of waypoints
def drive_waypoints(actor, waypoints, speed=10.0):
    """
    Very simple waypoint follower.
    waypoints = [(x1,y1), (x2,y2), ...]
    For a real project, use CARLA's built-in Waypoint API instead.
    """
    actor.set_autopilot(False)
    for (tx, ty) in waypoints:
        tf = carla.Transform(
            carla.Location(x=tx, y=ty, z=0.5))
        actor.set_transform(tf)
        time.sleep(0.5)
    actor.set_autopilot(True)

#build a  scene 
v1 = spawn_vehicle("vehicle.tesla.model3",spawn_index=1)
v2 = spawn_vehicle("vehicle.audi.a2", spawn_index=3)
v3 = spawn_vehicle("vehicle.mercedes.coupe_2020",spawn_index=5)

ped1, ped_ctrl1 = spawn_pedestrian(x=20, y=15)
ped2, ped_ctrl2 = spawn_pedestrian(x=35, y=-10)

print("Scene running for 20s,watch in CARLA window")
time.sleep(20)

#  Remove ab actor 
print("Removing a vehicle")
v3.destroy()
spawned_actors.remove(v3)
time.sleep(5)

# Cleanup allactors 
print("Cleaning up actors")
for actor in reversed(spawned_actors):
    try:
        if hasattr(actor, "stop"): actor.stop()
        actor.destroy()
    except: pass

print("Done.")
