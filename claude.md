# MAPush - Claude Code Documentation

## Project Overview

**MAPush** (Multi-Agent Pushing) is a hierarchical multi-agent reinforcement learning (MARL) framework for training multiple Unitree Go1 quadruped robots to collaboratively push objects in Isaac Gym simulation.

**Paper**: [Learning Multi-Agent Loco-Manipulation for Long-Horizon Quadrupedal Pushing](https://arxiv.org/pdf/2411.07104)

**Website**: https://collaborative-mapush.github.io/

---

## Directory Structure

```
MAPush/
├── mqe/                          # Multi-Quadruped Environment
│   ├── envs/                     # Environment definitions
│   │   ├── base/                 # Base classes (legged_robot.py, base_task.py, base_config.py)
│   │   ├── go1/                  # Go1 robot with locomotion policy (go1.py, go1_config.py)
│   │   ├── npc/                  # Interactive objects (go1_object.py)
│   │   ├── field/                # Environment field (legged_robot_field.py)
│   │   ├── configs/              # Task configs (go1_push_mid_config.py, go1_push_upper_config.py)
│   │   └── wrappers/             # Observation/action/reward definitions
│   │       ├── go1_push_mid_wrapper.py    # Mid-level controller wrapper
│   │       └── go1_push_upper_wrapper.py  # High-level planner wrapper
│   └── utils/                    # Utilities (terrain, math, logger, etc.)
│       └── terrain/              # Terrain generation (barrier_track.py, perlin.py)
├── task/                         # Task configurations for training
│   ├── cuboid/                   # Cuboid pushing task (2 agents)
│   │   ├── config.py             # Task settings
│   │   └── train.sh              # Training script
│   ├── Tblock/                   # T-shaped block task (2 agents)
│   └── cylinder/                 # Cylinder task (3 agents)
├── script/                       # Training entry points
│   ├── train.py                  # Main training orchestrator
│   └── utils/                    # Processing utilities (process_marl.py, process_sarl.py)
├── openrl_ws/                    # OpenRL workspace
│   ├── train.py                  # OpenRL training interface
│   ├── test.py                   # OpenRL testing interface
│   ├── update_config.py          # Config updater
│   └── cfgs/                     # Algorithm configs (ppo.yaml)
├── resources/                    # Assets and pretrained models
│   ├── objects/                  # URDF files (cuboid, Tblock, cylinder)
│   ├── robots/                   # Robot URDFs (go1/)
│   ├── command_nets/             # Pretrained locomotion networks
│   ├── goals_net/                # Pretrained high-level policies
│   └── visualize.py              # Visualization tools
└── results/                      # Training outputs (checkpoints, logs)
```

---

## Hierarchical Architecture

### Three-Level Control System

1. **Low-Level Locomotion** (Pretrained)
   - Converts velocity commands → joint torques
   - Pretrained from [walk-these-ways](https://github.com/Improbable-AI/walk-these-ways)
   - Located in: `resources/command_nets/`

2. **Mid-Level Controller** (Decentralized - TRAINS HERE)
   - Input: Current state (relative positions)
   - Output: Velocity commands [vx, vy, ω]
   - Each robot acts independently
   - Config: `task/<object>/config.py`
   - Wrapper: `mqe/envs/wrappers/go1_push_mid_wrapper.py`

3. **High-Level Planner** (Centralized)
   - Input: Object pose, target pose
   - Output: Sequence of subgoals
   - Uses mid-level policy as skill primitive
   - Config: `mqe/envs/configs/go1_push_upper_config.py`
   - Wrapper: `mqe/envs/wrappers/go1_push_upper_wrapper.py`

---

## Training Workflow

### Mid-Level Controller Training

**Command**:
```bash
source task/cuboid/train.sh False
```

**Execution Flow**:
1. `train.sh` calls `openrl_ws/update_config.py`
2. Copies `task/cuboid/config.py` → `mqe/envs/configs/go1_push_mid_config.py`
3. Launches `openrl_ws/train.py` with:
   - Algorithm: PPO
   - Task: `go1push_mid`
   - Environments: 500 parallel
   - Timesteps: 100M
4. Training uses Isaac Gym environment
5. Outputs saved to `results/<timestamp>_cuboid/`
6. Success rates calculated for each checkpoint

**Key Files**:
- Entry: `task/cuboid/train.sh`
- Config: `task/cuboid/config.py`
- Wrapper: `mqe/envs/wrappers/go1_push_mid_wrapper.py`
- Training: `openrl_ws/train.py`

### High-Level Controller Training

**Command**:
```bash
python ./openrl_ws/train.py --algo ppo --task go1push_upper \
  --train_timesteps 100000000 --num_envs 500 --use_tensorboard --headless
```

**Requirements**:
- Mid-level controller must be trained first
- Add checkpoint path to `mqe/envs/configs/go1_push_upper_config.py`

---

## Configuration Guide

### Controlling Number of Agents

**File**: `task/cuboid/config.py`

**Line 10**:
```python
num_agents = 2  # Change to 3, 4, etc.
```

**Current Settings**:
- Cuboid: 2 agents
- T-block: 2 agents
- Cylinder: 3 agents

**Important**: Update `init_states` list (lines 149-162) to match `num_agents`:
```python
init_states = [
    init_state_class(pos = [11.0,-1.0, 0.45], ...),  # Agent 1
    init_state_class(pos = [11.0, 1.0, 0.45], ...),  # Agent 2
    # Add more if num_agents > 2
]
```

### Controlling Object Type

**File**: `task/cuboid/config.py`

**Lines 18-20**:
```python
file_npc = "{LEGGED_GYM_ROOT_DIR}/resources/objects/cuboid/SmallBox.urdf"
vertex_list = [[-0.60, -0.60], [ 0.60,-0.60],
               [ 0.60,  0.60], [-0.60, 0.60]]
```

- `file_npc`: URDF file path (defines physics/mesh)
- `vertex_list`: 2D footprint for collision/rewards

**Available Objects**:
- `resources/objects/cuboid/SmallBox.urdf` (1.2m × 1.2m)
- `resources/objects/Tblock/SuperSmallTblock.urdf`
- `resources/objects/cylinder/BigCylinder.urdf`

### Key Configuration Classes

**1. Environment** (`class env`, line 7):
- `num_agents`: Number of robots
- `num_npcs`: Number of objects (2: box + target)
- `episode_length_s`: Episode duration

**2. Rewards** (`class rewards`, line 97):
- `target_reward_scale`: Reward for moving toward target
- `approach_reward_scale`: Reward for approaching box
- `collision_punishment_scale`: Penalty for agent collisions
- `push_reward_scale`: Reward for pushing box
- `ocb_reward_scale`: Reward for optimal configuration
- `reach_target_reward_scale`: Bonus for reaching goal
- `exception_punishment_scale`: Penalty for termination

**3. Goal** (`class goal`, line 109):
- `static_goal_pos`: Fixed goal (False by default)
- `random_goal_pos`: Random goal generation (True by default)
- `random_goal_distance_from_init`: Goal distance range [1.5, 3.0]m
- `THRESHOLD`: Completion threshold (1.0m)

**4. Domain Randomization** (`class domain_rand`, line 186):
- `random_base_init_state`: Randomize agent positions
- `init_base_pos_range`: Agent position randomization
- `init_base_rpy_range`: Agent orientation randomization
- `init_npc_rpy_range`: Box orientation randomization
- `friction_range`: Terrain friction randomization [0.5, 0.6]

---

## Testing

### Mid-Level Testing

**Command**:
```bash
source results/10-15-23_cuboid/task/train.sh True
```

**Edit checkpoint in train.sh** (line 50):
```bash
filename="rl_model_110000000_steps/module.pt"
```

**Add video recording** (uncomment line 57):
```bash
--record_video
```

### High-Level Testing

**Command**:
```bash
python ./openrl_ws/test.py --algo ppo --task go1push_upper \
  --num_envs 10 --checkpoint your_checkpoint --record_video
```

**Pretrained Example**:
- Path: `resources/goals_net`
- Task: Push 1.2m × 1.2m cube

---

## Observation and Action Spaces

### Mid-Level Controller

**Observation** (`go1_push_mid_wrapper.py:54`):
- Shape: `(2 + 3 * num_agents,)` or `(3 + 3 * num_agents,)` if `general_dist=True`
- Content: Relative positions of box, target, and agents

**Action** (`go1_push_mid_wrapper.py:58`):
- Shape: `(3,)` per agent
- Content: `[vx, vy, ω]` velocity commands
- Scale: `[-0.5, 0.5]` m/s for linear, rad/s for angular

### High-Level Controller

**Observation** (`go1_push_upper_wrapper.py:124`):
- Shape: `(3 + 3 * num_agents,)`
- Content: Box pose, target pose, agent poses

**Action**:
- Output: Subgoal positions for mid-level controller

---

## Important Notes

### Multi-Agent Setup
- The codebase uses **decentralized execution** for mid-level
- Each agent receives its own observation (egocentric view)
- Rewards are shared/team-based
- Wrapper converts multi-agent env → single-agent for PPO training

### Training Hyperparameters

**In train.sh**:
- `num_envs`: Number of parallel environments (500 default)
- `num_steps`: Total training timesteps (100M default)
- `algo`: Algorithm (ppo default)

**Success Rate Calculation**:
- Automatically tests checkpoints every 10M steps
- Results saved to `results/<timestamp>_cuboid/success_rate.txt`

### Common Issues

1. **Numpy version**: Must be ≤1.19.5 or modify Isaac Gym utils
2. **LibPython error**: Set `export LD_LIBRARY_PATH=/path/to/conda/envs/mapush/lib`
3. **Segmentation fault on A100/A800**: Switch to GeForce GPUs for rendering

---

## Quick Start for k=2 Agents, Cuboid Only

**Current config is already set for this!**

```bash
cd /Users/alexei.ermochkine/Desktop/uTOKYOxEPFL_GVLab/MAPush
source task/cuboid/train.sh False
```

This will:
1. Train 2 agents to push a 1.2m × 1.2m cuboid
2. Use PPO with 500 parallel environments
3. Train for 100M timesteps
4. Save results to `results/<timestamp>_cuboid/`
5. Calculate success rates for all checkpoints

---

## Modifications Not Yet Made

As of this session, **no modifications** have been made to the codebase. All analysis was read-only.

---

## Citation

```bibtex
@article{mapush2024,
  title={Learning Multi-Agent Loco-Manipulation for Long-Horizon Quadrupedal Pushing},
  author={Feng, Yuming and Hong, Chuye and Niu, Yaru and Liu, Shiqi and Yang, Yuxiang and Yu, Wenhao and Zhang, Tingnan and Tan, Jie and Zhao, Ding},
  journal={arXiv preprint arXiv:2411.07104},
  year={2024}
}
```

---

## Related Resources

- **Base Environment**: [MQE](https://github.com/ziyanx02/multiagent-quadruped-environment)
- **Locomotion Policy**: [walk-these-ways](https://github.com/Improbable-AI/walk-these-ways)
- **RL Framework**: [OpenRL](https://github.com/OpenRL-Lab/openrl)
- **Simulator**: [Isaac Gym](https://developer.nvidia.com/isaac-gym)
