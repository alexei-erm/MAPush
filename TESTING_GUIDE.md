# Testing Guide - MAPush Mid-Level Controller

## Overview

The MAPush project has two test modes for evaluating the trained mid-level controller:

1. **Calculator Mode** - Quantitative evaluation (success rate, metrics)
2. **Viewer Mode** - Visual evaluation (with optional video recording)

---

## Available Checkpoints

After training, checkpoints are saved in:
```
./results/<timestamp>_<task>/checkpoints/rl_model_<steps>_steps/module.pt
```

### Example Checkpoints
From your previous training (`10-15-23_cuboid`):
```
/home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_10000000_steps/module.pt
/home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_20000000_steps/module.pt
/home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_30000000_steps/module.pt
...
/home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt
```

**Checkpoint Saving**:
- Checkpoints save every **10M steps** during training
- Configured in `train.py` via `CheckpointCallback(save_freq=20000, ...)`
- Best checkpoint is typically the latest (100M steps)

---

## Test Mode 1: Calculator Mode (Success Rate Evaluation)

### Purpose
Quantitatively evaluate policy performance across many environments:
- **Success Rate**: Percentage of successful pushes to target
- **Finished Time**: Average time to complete task
- **Collision Degree**: How often robots collide with each other
- **Collaboration Degree**: How well robots coordinate

### Command

```bash
conda activate mapush
cd /home/gvlab/MAPush

python ./openrl_ws/test.py \
    --num_envs 300 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode calculator \
    --headless
```

### Parameters Explained

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--num_envs` | 300 | Number of parallel test environments (more = better statistics) |
| `--algo` | ppo | Algorithm used (PPO for mid-level) |
| `--task` | go1push_mid | Mid-level pushing task |
| `--checkpoint` | `<path>` | Path to trained model checkpoint |
| `--test_mode` | calculator | Run quantitative evaluation |
| `--headless` | - | No rendering (faster) |

### Expected Output

```
Loaded checkpoint from: /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt
---------------------------------------------------------------------------

success rate: 0.85
finished time: 15.3
collision degree: 0.02
collaboration degree: 0.76
-----------------------------------------------------
```

**Metrics Explained**:
- **Success Rate**: 0.85 = 85% of episodes successfully pushed box to target
- **Finished Time**: 15.3 seconds average to complete task
- **Collision Degree**: 0.02 = low collision rate (good!)
- **Collaboration Degree**: 0.76 = high collaboration (good!)

### Recommended Test Configurations

**Quick Test** (fast, lower statistics):
```bash
python ./openrl_ws/test.py \
    --num_envs 50 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint <YOUR_CHECKPOINT> \
    --test_mode calculator \
    --headless
```

**Standard Test** (paper-like evaluation):
```bash
python ./openrl_ws/test.py \
    --num_envs 300 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint <YOUR_CHECKPOINT> \
    --test_mode calculator \
    --headless
```

**Thorough Test** (maximum statistics):
```bash
python ./openrl_ws/test.py \
    --num_envs 500 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint <YOUR_CHECKPOINT> \
    --test_mode calculator \
    --headless
```

---

## Test Mode 2: Viewer Mode (Visual Evaluation)

### Purpose
Visualize the policy behavior in real-time or record videos for analysis.

### Option A: Live Visualization (No Recording)

**Command**:
```bash
conda activate mapush
cd /home/gvlab/MAPush

python ./openrl_ws/test.py \
    --num_envs 1 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode viewer
```

**What happens**:
- Opens Isaac Gym viewer window
- Shows 1 environment with 2 robots pushing the cuboid
- Runs continuously until you close the window
- Prints "success" or "fail" after each episode

**Keyboard Controls** (standard Isaac Gym):
- `ESC`: Quit
- `V`: Toggle viewer sync
- `R`: Reset view

### Option B: Video Recording

**Command**:
```bash
conda activate mapush
cd /home/gvlab/MAPush

python ./openrl_ws/test.py \
    --num_envs 1 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode viewer \
    --record_video \
    --headless
```

**What happens**:
- Runs 1 episode headless (no viewer)
- Records frames during execution
- Saves video to: `/home/gvlab/MAPush/docs/video/test.mp4`
- Prints "success" or "fail" at the end
- Exits after 1 episode

**Video Output**:
- Location: `./docs/video/test.mp4`
- Format: MP4 (H.264)
- FPS: 50 (based on simulation dt)
- Resolution: 240x360 (configured in environment)

### Recording Multiple Episodes

To record multiple episodes, modify the script or run multiple times:

```bash
# Record episode 1
python ./openrl_ws/test.py --num_envs 1 --algo ppo --task go1push_mid \
    --checkpoint <CHECKPOINT> --test_mode viewer --record_video --headless

# Rename video
mv ./docs/video/test.mp4 ./docs/video/episode_1.mp4

# Record episode 2
python ./openrl_ws/test.py --num_envs 1 --algo ppo --task go1push_mid \
    --checkpoint <CHECKPOINT> --test_mode viewer --record_video --headless

mv ./docs/video/test.mp4 ./docs/video/episode_2.mp4
```

---

## Complete Testing Workflow

### Step 1: Find Your Best Checkpoint

```bash
# List all checkpoints sorted by steps
ls -lh /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/
```

Typical progression:
- **10M-30M steps**: Early learning, low success rate
- **40M-70M steps**: Intermediate, improving behavior
- **80M-100M steps**: Near-optimal performance
- **100M+ steps**: Best checkpoint (if available)

### Step 2: Quick Visual Check

```bash
# Verify the policy works visually (1 episode)
python ./openrl_ws/test.py \
    --num_envs 1 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode viewer
```

Watch the robots - they should:
- ✅ Approach the cuboid collaboratively
- ✅ Push toward the target (blue sphere)
- ✅ Coordinate without colliding
- ✅ Successfully reach target in <20 seconds

### Step 3: Quantitative Evaluation

```bash
# Run comprehensive success rate test
python ./openrl_ws/test.py \
    --num_envs 300 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode calculator \
    --headless
```

Expected results for a well-trained policy:
- Success rate: **>80%**
- Collision degree: **<0.05**
- Collaboration degree: **>0.70**

### Step 4: Record Demo Video

```bash
# Record a successful episode
python ./openrl_ws/test.py \
    --num_envs 1 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode viewer \
    --record_video \
    --headless
```

Video saved to: `./docs/video/test.mp4`

---

## Testing Different Checkpoints

### Compare Checkpoint Performance

Create a script to test all checkpoints:

```bash
#!/bin/bash
# test_all_checkpoints.sh

CHECKPOINTS_DIR="/home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints"
OUTPUT_FILE="checkpoint_comparison.txt"

echo "Checkpoint Performance Comparison" > $OUTPUT_FILE
echo "=================================" >> $OUTPUT_FILE

for checkpoint_dir in $CHECKPOINTS_DIR/rl_model_*_steps/; do
    checkpoint="${checkpoint_dir}module.pt"
    steps=$(basename $checkpoint_dir | sed 's/rl_model_//;s/_steps//')

    echo "" >> $OUTPUT_FILE
    echo "Testing checkpoint: ${steps} steps" >> $OUTPUT_FILE
    echo "-----------------------------------" >> $OUTPUT_FILE

    python ./openrl_ws/test.py \
        --num_envs 200 \
        --algo ppo \
        --task go1push_mid \
        --checkpoint $checkpoint \
        --test_mode calculator \
        --headless >> $OUTPUT_FILE 2>&1
done

echo "Comparison complete! Results in $OUTPUT_FILE"
```

Run it:
```bash
cd /home/gvlab/MAPush
chmod +x test_all_checkpoints.sh
./test_all_checkpoints.sh
```

---

## Testing Your Latest Training (200 Envs Run)

### Check Available Checkpoints

```bash
# Check if checkpoints were saved from your 200-env training
ls -lh /home/gvlab/MAPush/results/10-28-18_cuboid/checkpoints/
```

**Note**: Checkpoints save every **20,000 training steps**. Your 10M step training should have saved at:
- 20k steps
- 40k steps
- 60k steps
- ...
- 10M steps

If no checkpoints yet, the training needs to reach at least 20k steps first.

### Test Your Latest Checkpoint

Once you have a checkpoint from the 200-env run:

```bash
# Find the latest checkpoint
LATEST_CHECKPOINT=$(ls -t /home/gvlab/MAPush/results/10-28-18_cuboid/checkpoints/*/module.pt | head -1)

# Test it
python ./openrl_ws/test.py \
    --num_envs 300 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint $LATEST_CHECKPOINT \
    --test_mode calculator \
    --headless
```

---

## Common Issues & Solutions

### Issue 1: "Checkpoint not found"

**Error**: `FileNotFoundError: [Errno 2] No such file or directory`

**Solution**: Check the checkpoint path exists:
```bash
ls -lh /home/gvlab/MAPush/results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/module.pt
```

### Issue 2: "CUDA out of memory" in Calculator Mode

**Error**: `RuntimeError: CUDA out of memory`

**Solution**: Reduce `--num_envs`:
```bash
python ./openrl_ws/test.py \
    --num_envs 100 \
    --test_mode calculator \
    --headless \
    ...
```

### Issue 3: Viewer Mode Shows Black Screen

**Problem**: Viewer opens but shows nothing

**Solutions**:
1. Check you removed `--headless` flag
2. Ensure `--num_envs 1` (viewer works best with 1 env)
3. Try pressing `R` to reset view

### Issue 4: Video Recording Creates Empty File

**Problem**: `test.mp4` is created but has 0 bytes

**Solution**: Make sure the docs/video directory exists:
```bash
mkdir -p /home/gvlab/MAPush/docs/video
```

### Issue 5: Success Rate is 0%

**Problem**: Policy performs poorly in testing

**Possible Causes**:
1. **Checkpoint too early**: Try a later checkpoint (80M+ steps)
2. **Wrong task**: Ensure `--task go1push_mid` matches training
3. **Different config**: Testing uses config from `task/cuboid/config.py`

---

## Understanding Test Metrics

### Success Rate
- **Definition**: Percentage of episodes where the box reaches the target
- **Target threshold**: Box center within 1.0m of target position (configured in `goal.THRESHOLD`)
- **Good performance**: >80%
- **Excellent performance**: >90%

### Finished Time
- **Definition**: Average time (seconds) to complete successful episodes
- **Episode timeout**: 20 seconds (configured in `env.episode_length_s`)
- **Good performance**: <15 seconds
- **Excellent performance**: <10 seconds

### Collision Degree
- **Definition**: Average collision events per timestep during successful episodes
- **Range**: 0.0 (no collisions) to 1.0 (constant collision)
- **Good performance**: <0.05
- **Excellent performance**: <0.02

### Collaboration Degree
- **Definition**: Measure of how well robots coordinate (implementation in env)
- **Range**: 0.0 (no collaboration) to 1.0 (perfect collaboration)
- **Good performance**: >0.70
- **Excellent performance**: >0.85

---

## Advanced Testing

### Test with Custom Initial Positions

Modify the test to use specific scenarios by editing:
```python
# In task/cuboid/config.py
class init_state:
    # Set specific robot/box positions for testing
    init_states = [
        init_state_class(pos=[11.0, -1.0, 0.45], ...),  # Robot 1
        init_state_class(pos=[11.0, 1.0, 0.45], ...),   # Robot 2
    ]
    init_states_npc = [
        init_state_class(pos=[12.0, 0.0, 0.30], ...),   # Box
        init_state_class(pos=[8.0, 0.0, 0.1], ...),     # Target
    ]
```

### Test with Different Objects

To test with different objects (cylinder, Tblock):
```bash
# Test with cylinder
python ./openrl_ws/test.py \
    --algo ppo \
    --task go1push_mid \
    --checkpoint <YOUR_CHECKPOINT> \
    --test_mode viewer
```

Note: Must use checkpoint trained on the same object type!

---

## Next Steps: High-Level Controller

After successfully testing the mid-level controller, you can:

1. **Train High-Level Controller**: Plans waypoint sequences for longer pushes
   ```bash
   python ./openrl_ws/train.py \
       --algo ppo \
       --task go1push_upper \
       --train_timesteps 100000000 \
       --num_envs 500 \
       --use_tensorboard \
       --headless
   ```

2. **Test Complete Hierarchical System**: Combine high-level + mid-level
   - High-level outputs waypoint goals
   - Mid-level executes to reach each waypoint
   - Can push objects much longer distances (10m+)

---

## Summary

### Quick Reference Commands

**Calculator Test** (quantitative):
```bash
python ./openrl_ws/test.py --num_envs 300 --algo ppo --task go1push_mid \
    --checkpoint <CHECKPOINT> --test_mode calculator --headless
```

**Viewer Test** (visual):
```bash
python ./openrl_ws/test.py --num_envs 1 --algo ppo --task go1push_mid \
    --checkpoint <CHECKPOINT> --test_mode viewer
```

**Video Recording**:
```bash
python ./openrl_ws/test.py --num_envs 1 --algo ppo --task go1push_mid \
    --checkpoint <CHECKPOINT> --test_mode viewer --record_video --headless
```

### Best Practices

1. ✅ **Always test with calculator mode first** - get quantitative metrics
2. ✅ **Use 200-300 envs for calculator mode** - better statistics
3. ✅ **Use viewer mode to debug** - understand policy behavior visually
4. ✅ **Test multiple checkpoints** - find the best performing one
5. ✅ **Record videos for presentations** - showcase successful behaviors

---

**Happy Testing! 🚀**
