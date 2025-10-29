#!/usr/bin/env python
"""
Debug script to find exact segfault location in environment creation
"""
import sys
print("1. Starting imports...")

from isaacgym import gymapi
from isaacgym.gymutil import parse_device_str
print("2. Isaac Gym imported successfully")

import torch
print(f"3. PyTorch imported: {torch.__version__}, CUDA: {torch.cuda.is_available()}")

from mqe.envs.npc.go1_object import Go1Object
from mqe.envs.configs.go1_push_mid_config import Go1PushMidCfg
print("4. Environment classes imported successfully")

from mqe.utils.helpers import class_to_dict, parse_sim_params
print("5. Helper functions imported successfully")

# Create minimal args similar to what train.py uses
class Args:
    def __init__(self):
        self.num_envs = 2
        self.task = "go1push_mid"
        self.seed = 1
        self.headless = True
        self.physics_engine = gymapi.SIM_PHYSX
        self.sim_device = "cuda:0"
        self.sim_device_type = "cuda"
        self.compute_device_id = 0
        self.use_gpu = True
        self.use_gpu_pipeline = True
        self.subscenes = 0
        self.num_threads = 0

args = Args()
print("6. Args created")

# Create config
env_cfg = Go1PushMidCfg()
env_cfg.env.num_envs = args.num_envs
print(f"7. Config created with {env_cfg.env.num_envs} envs")

# Parse sim params
sim_params_dict = {"sim": class_to_dict(env_cfg.sim)}
sim_params = parse_sim_params(args, sim_params_dict)
print("8. Sim params parsed successfully")

print("9. About to create environment... (this is where segfault likely happens)")
sys.stdout.flush()

# Monkey-patch to add debug output
from mqe.envs.base.legged_robot import LeggedRobot
original_create_terrain = LeggedRobot._create_terrain
original_create_envs = LeggedRobot._create_envs

def debug_create_terrain(self):
    print("DEBUG: _create_terrain called")
    sys.stdout.flush()
    result = original_create_terrain(self)
    print("DEBUG: _create_terrain completed successfully")
    sys.stdout.flush()
    return result

def debug_create_envs(self):
    print("DEBUG: _create_envs called")
    sys.stdout.flush()
    result = original_create_envs(self)
    print("DEBUG: _create_envs completed successfully")
    sys.stdout.flush()
    return result

LeggedRobot._create_terrain = debug_create_terrain
LeggedRobot._create_envs = debug_create_envs

try:
    env = Go1Object(
        cfg=env_cfg,
        sim_params=sim_params,
        physics_engine=args.physics_engine,
        sim_device=args.sim_device,
        headless=args.headless
    )
    print("10. Environment created successfully! No segfault!")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
