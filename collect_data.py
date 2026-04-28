import carla
import os
import json
import numpy as np
import time


OUTPUT_DIR = "collected_data"
IMG_DIR = os.path.join(OUTPUT_DIR, "images")
PCD_DIR = os.path.join(OUTPUT_DIR, "pointclouds")
GPS_LOG = os.path.join(OUTPUT_DIR, "gps_log.json")

for d in [IMG_DIR, PCD_DIR]:
    os.makedirs(d, exist_ok=True)


#connecting to carla
client = carla.Client("localhost", 2000)
client.set_timeout(10.0)
world = client.get_world()


#spawn car
bp_lib = world.get_blueprint_library()
vehicle_bp = bp_lib.find("vehicle.tesla.model3")
spawn_point = world.get_map().get_spawn_points()[0]
vehicle = world.spawn_actor(vehicle_bp, spawn_point)
vehicle.set_autopilot(True)
 # vehicle spawned and autopilot on 

gps_log = []
actors_to_destroy = [vehicle]


#camera
cam_bp = bp_lib.find("sensor.camera.rgb")
cam_bp.set_attribute("image_size_x", "1280")
cam_bp.set_attribute("image_size_y", "720")
cam_bp.set_attribute("fov", "90")
cam_transform = carla.Transform(carla.Location(x=1.5, z=2.4 ))
camera = world.spawn_actor(cam_bp, cam_transform, attach_to=vehicle)
actors_to_destroy.append(camera)

frame_count = [0]


def save_data(image):
    path = os.path.join(IMG_DIR, f"frame_{image.frame:06d}.png")
    image.save_to_disk(path)
    frame_count[0] += 1
    if frame_count[0] % 20 == 0:
        print(f"Saved {frame_count[0]} frames")

camera.listen(save_data)

#LiDAR
lidar_bp = bp_lib.find("sensor.lidar.ray_cast")
lidar_bp.set_attribute("channels",         "32")
lidar_bp.set_attribute("range",             "50")
lidar_bp.set_attribute("points_per_second", "100000")
lidar_bp.set_attribute("rotation_frequency","10")
lidar_transform = carla.Transform(carla.Location(z=2.5))
lidar = world.spawn_actor(lidar_bp, lidar_transform, attach_to=vehicle)
actors_to_destroy.append(lidar)

def save_lidar(point_cloud):
    path = os.path.join(PCD_DIR, f"lidar_{point_cloud.frame:06d}.ply")
    point_cloud.save_to_disk(path)

lidar.listen(save_lidar)



#GPS
gnss_bp = bp_lib.find("sensor.other.gnss")
gnss = world.spawn_actor(gnss_bp,
        carla.Transform(), attach_to=vehicle)
actors_to_destroy.append(gnss)

def save_gps(data):
    gps_log.append({
        "frame"    : data.frame,
        "timestamp": data.timestamp,
        "latitude" : data.latitude,
        "longitude": data.longitude,
        "altitude" : data.altitude,
    })

gnss.listen(save_gps)

#COLLCT FOR N SECONDS
COLLECT_SECONDS = 30
print(f"Collecting data ")
time.sleep(COLLECT_SECONDS)

#  Save log and cleanup
with open(GPS_LOG, "w") as f:
    json.dump(gps_log, f, indent=2)
print(f"GPS log saved: {len(gps_log)} readings → {GPS_LOG}")

for actor in reversed(actors_to_destroy):
    actor.stop() if hasattr(actor, "stop") else None
    actor.destroy()

print("Data saved to:", os.path.abspath(OUTPUT_DIR))