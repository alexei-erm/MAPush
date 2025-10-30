# MAPush Checkpoint & Directory Naming System

## Overview

This document explains how MAPush saves trained models, the checkpoint naming scheme, and the directory structure for training results.

---

## Directory Naming Scheme

### Format: `<MM-DD-HH>_<experiment_name>`

**Pattern**: `results/<month>-<day>-<hour>_<exp_name>/`

**Examples**:
- `10-15-23_cuboid` = October 15th at 23:00 (11 PM), experiment name "cuboid"
- `10-28-18_cuboid` = October 28th at 18:00 (6 PM), experiment name "cuboid"
- `10-15-23_cylinder` = October 15th at 23:00 (11 PM), experiment name "cylinder"

### Where It's Created

**Code**: `openrl_ws/train.py` lines 16-17, 84-87

```python
# Line 16-17: Create timestamp when training starts
start_time = datetime.now()
start_time_str = start_time.strftime("%m-%d-%H")  # Format: MM-DD-HH

# Line 86: Create final results directory
target_folder = "./results/"+start_time_str+"_"+args.exp_name+"/"
```

### Why This Naming?

**Advantages**:
1. ✅ **Automatic organization**: Results sorted chronologically by date
2. ✅ **No overwrites**: Each training run gets unique directory (unless same hour)
3. ✅ **Easy identification**: Immediately see when training was run
4. ✅ **Experiment tracking**: Multiple runs of same task (e.g., "cuboid") are separate

**Important Notes**:
- ⚠️ **Hour precision only**: If you start 2 trainings in the same hour with the same exp_name, the second will fail (directory already exists)
- ⚠️ **24-hour format**: Hour is 0-23 (not AM/PM)
- ⚠️ **Local timezone**: Uses system time, not UTC

### Example Timeline

```
10-15-23_cuboid  → Started Oct 15 at 11 PM
10-28-18_cuboid  → Started Oct 28 at 6 PM  (Your 200-env training!)
10-29-09_cuboid  → Started Oct 29 at 9 AM  (Hypothetical next run)
```

---

## Complete Training Directory Structure

### During Training

While training is active, data is temporarily stored in:
```
./log/MQE/<task_name>/<timestamp>/
```

**Example**:
```
./log/MQE/go1push_mid/2025_10_28_18_12_45/
├── checkpoints/
│   ├── rl_model_20000_steps/
│   │   └── module.pt
│   ├── rl_model_40000_steps/
│   │   └── module.pt
│   └── ...
├── tensorboard/
└── log.txt
```

### After Training Completes

Training results are moved to `./results/` with timestamp naming:

```
./results/10-28-18_cuboid/
├── checkpoints/                    # All saved model checkpoints
│   ├── rl_model_10000000_steps/   # Checkpoint at 10M steps
│   │   └── module.pt              # PyTorch model file (actual weights)
│   ├── rl_model_20000000_steps/   # Checkpoint at 20M steps
│   │   └── module.pt
│   ├── rl_model_30000000_steps/
│   │   └── module.pt
│   └── ...
│   └── rl_model_100000000_steps/  # Final checkpoint at 100M steps
│       └── module.pt
├── task/                          # Copy of task configuration
│   ├── config.py                  # Task-specific config
│   └── train.sh                   # Training script used
├── success_rate.txt               # Evaluation results (if ran)
└── log.txt                        # Training logs
```

---

## Checkpoint Saving System

### Configuration

**Code**: `openrl_ws/train.py` line 74

```python
callback = CheckpointCallback(
    save_freq=20000,              # Save every 20,000 training steps
    save_path=run_dir + "/checkpoints",
    name_prefix="rl_model",
    save_replay_buffer=False,
    verbose=2
)
```

### How Checkpoints Are Saved

1. **Training starts** → Initialize checkpoint callback
2. **Every 20,000 steps** → Callback triggers
3. **Create directory**: `rl_model_<steps>_steps/`
4. **Save model**: `module.pt` inside the directory

### Checkpoint Naming: `rl_model_<N>_steps/module.pt`

**Pattern**: `rl_model_<total_training_steps>_steps/module.pt`

**Examples**:
- `rl_model_10000000_steps/module.pt` = 10 million steps
- `rl_model_20000000_steps/module.pt` = 20 million steps
- `rl_model_100000000_steps/module.pt` = 100 million steps (100M)

### Why Multiple Checkpoints?

**Benefits**:
1. ✅ **Track learning progress**: Compare performance at 10M, 50M, 100M steps
2. ✅ **Recover from overtraining**: If performance degrades, use earlier checkpoint
3. ✅ **Ablation studies**: Test how performance improves with more training
4. ✅ **Safety backup**: If training crashes, don't lose all progress

### Checkpoint File: `module.pt`

**Format**: PyTorch serialized model file

**Contains**:
- 🧠 **Neural network weights**: Actor (policy) and Critic (value function)
- 📊 **Optimizer state**: Adam optimizer parameters
- 🔢 **Training metadata**: Current training step, epoch number
- ⚙️ **Network architecture**: Hidden layer sizes, activation functions

**File Size**: ~10-50 MB per checkpoint (depends on network architecture)

### What Gets Saved in Each Checkpoint

```python
# Conceptual content of module.pt
{
    'actor_network': {
        'layer1.weight': Tensor(...),
        'layer1.bias': Tensor(...),
        'layer2.weight': Tensor(...),
        ...
    },
    'critic_network': {
        'layer1.weight': Tensor(...),
        'layer1.bias': Tensor(...),
        ...
    },
    'optimizer_state': {
        'learning_rate': 0.0005,
        'momentum': ...,
        ...
    },
    'training_step': 10000000,
    'epoch': 1562,
}
```

---

## Checkpoint Frequency & Storage

### Saving Frequency

**Default**: Every **20,000 training steps**

**For 100M step training**:
- Total checkpoints saved: **5,000 checkpoints**
- Saved at: 20k, 40k, 60k, ..., 99,980k, 100M

**Storage Calculation** (assuming ~30 MB per checkpoint):
```
5,000 checkpoints × 30 MB = ~150 GB
```

⚠️ **Warning**: Long training runs can consume significant disk space!

### Checkpoint Cleanup Strategy

**Option 1**: Keep only milestone checkpoints
```bash
# Keep checkpoints at 10M intervals
cd /home/gvlab/MAPush/results/10-28-18_cuboid/checkpoints/
rm -rf rl_model_[1-9]0000000_steps/  # Remove 10M, 20M, ..., 90M
# Keeps only 100M
```

**Option 2**: Keep only recent + best
```bash
# Keep last 5 checkpoints + 100M
find . -name "rl_model_*_steps" | sort | head -n -5 | xargs rm -rf
```

**Option 3**: Reduce save_freq
```python
# In train.py, change line 74:
callback = CheckpointCallback(
    save_freq=10000000,  # Save every 10M steps instead of 20k
    ...
)
```

---

## Loading Checkpoints

### During Training (Resume)

**Purpose**: Continue training from a saved checkpoint

```bash
python ./openrl_ws/train.py \
    --num_envs 200 \
    --train_timesteps 200000000 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-28-18_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --exp_name cuboid
```

**What happens**:
1. Loads weights from checkpoint
2. Resumes training from 100M steps
3. Continues saving checkpoints at 100.02M, 100.04M, etc.

### During Testing (Evaluation)

**Purpose**: Evaluate a trained policy

```bash
python ./openrl_ws/test.py \
    --num_envs 300 \
    --algo ppo \
    --task go1push_mid \
    --checkpoint /home/gvlab/MAPush/results/10-28-18_cuboid/checkpoints/rl_model_100000000_steps/module.pt \
    --test_mode calculator \
    --headless
```

**What happens**:
1. Loads weights from checkpoint
2. Runs policy in test environments
3. No training, only evaluation

---

## Training Logs

### log.txt

**Location**: `./results/<timestamp>_<exp_name>/log.txt`

**Contents**: Complete training log including:
- Episode rewards
- Policy/value losses
- Training metrics
- System information

**Example snippet**:
```
[10/28/25 18:12:53] INFO Episode: 0/12
[10/28/25 18:12:58] INFO average_step_reward: -0.021021399646997452
                         distance_to_target_reward: -0.00775153050199151
                         collision_punishment: -0.0046801299729850145
                         value_loss: 0.30958522856235504
                         policy_loss: -0.004811584241221567
```

### TensorBoard Logs (if enabled)

**Location**: `./log/MQE/<task>/<timestamp>/tensorboard/`

**View with**:
```bash
tensorboard --logdir ./log/MQE/go1push_mid/
```

**Contains**:
- Real-time training curves
- Reward components over time
- Loss values
- Learning rate schedules

---

## Task Configuration Backup

### Why It's Saved

**Location**: `./results/<timestamp>_<exp_name>/task/`

**Purpose**: Record exact configuration used for training

**Files**:
- `config.py`: Task-specific parameters (rewards, termination, initial states)
- `train.sh`: Training script with hyperparameters

**Importance**:
- ✅ **Reproducibility**: Know exactly how model was trained
- ✅ **Comparison**: Compare configs between different runs
- ✅ **Testing**: Use same config for evaluation

**Code**: `openrl_ws/train.py` lines 52-55
```python
if args.task == "go1push_mid":
    source_folder = "./task/"+args.exp_name+"/"
    target_folder = run_dir + "/task/"
    shutil.copytree(source_folder, target_folder)
```

---

## Practical Examples

### Example 1: Your 200-Env Training Run

**Started**: October 28, 2025 at 18:00 (6 PM)

**Directory created**: `./results/10-28-18_cuboid/`

**Command used**:
```bash
python ./openrl_ws/train.py \
    --num_envs 200 \
    --train_timesteps 10000000 \
    --algo ppo \
    --task go1push_mid \
    --exp_name cuboid
```

**Timeline**:
1. **18:00:00** - Training starts, temp dir created: `./log/MQE/go1push_mid/2025_10_28_18_00_00/`
2. **18:00:30** - First checkpoint saved: `rl_model_20000_steps/module.pt`
3. **18:01:00** - Second checkpoint: `rl_model_40000_steps/module.pt`
4. **...** - Checkpoints continue every ~30 seconds (for 20k steps)
5. **18:12:45** - Final checkpoint: `rl_model_10000000_steps/module.pt`
6. **18:12:46** - Training completes, directory moved to: `./results/10-28-18_cuboid/`

### Example 2: Original Pre-trained Model

**Started**: October 15, 2025 at 23:00 (11 PM)

**Directory**: `./results/10-15-23_cuboid/`

**Training duration**: ~100M steps = ~83 hours (~3.5 days)

**Checkpoints saved**: Every 10M steps = 10 total checkpoints

**Best checkpoint**: `rl_model_100000000_steps/module.pt`

### Example 3: Multiple Runs Same Day

**Scenario**: Train 3 times on October 29, 2025

```bash
# Run 1: Started 9:00 AM
python ./openrl_ws/train.py ... --exp_name cuboid
# Creates: ./results/10-29-09_cuboid/

# Run 2: Started 3:00 PM (15:00)
python ./openrl_ws/train.py ... --exp_name cuboid
# Creates: ./results/10-29-15_cuboid/

# Run 3: Started 9:30 PM (21:00)
python ./openrl_ws/train.py ... --exp_name cuboid
# Creates: ./results/10-29-21_cuboid/
```

All three runs have separate directories - no conflicts!

---

## Comparison: Your Runs

### 10-15-23_cuboid (Pre-existing)
- **Date**: October 15 at 11 PM
- **Training steps**: 100M steps (100,000,000)
- **Duration**: ~3-4 days
- **Environments**: 50 (original paper baseline)
- **Checkpoints**: 10 total (10M, 20M, ..., 100M)
- **Purpose**: Original training run from paper/previous work

### 10-28-18_cuboid (Your New Run)
- **Date**: October 28 at 6 PM
- **Training steps**: 10M steps (10,000,000)
- **Duration**: ~15 minutes
- **Environments**: 200 (4× more than paper!)
- **Checkpoints**: 500 total (20k, 40k, ..., 10M)
- **Purpose**: Test run after fixing segmentation fault
- **Result**: ✅ Successful! Proved 200 envs works

---

## Best Practices

### 1. Naming Experiments
Use descriptive `--exp_name`:
```bash
# Good
--exp_name cuboid_200envs
--exp_name cylinder_ablation
--exp_name tblock_long_push

# Not recommended
--exp_name test
--exp_name v1
--exp_name final
```

### 2. Checkpoint Management

**Keep**:
- ✅ Final checkpoint (100M steps)
- ✅ Milestone checkpoints (25M, 50M, 75M)
- ✅ Best performing checkpoint (based on evaluation)

**Delete**:
- ❌ Intermediate checkpoints (unless debugging)
- ❌ Failed training runs
- ❌ Early checkpoints (<10M steps) after training completes

### 3. Documentation

For each training run, document:
```
Run: 10-28-18_cuboid
Date: October 28, 2025 18:00
Command: python train.py --num_envs 200 --train_timesteps 10000000 ...
GPU: RTX 2070 8GB
Duration: 15 minutes
Result: Success rate 85% (tested with calculator mode)
Notes: First successful training after fixing max_gpu_contact_pairs bug
```

### 4. Backup Important Checkpoints

```bash
# Backup best checkpoint
cp -r ./results/10-15-23_cuboid/checkpoints/rl_model_100000000_steps/ \
      ./backups/cuboid_100M_best/
```

---

## Troubleshooting

### Issue 1: Directory Already Exists

**Error**: `FileExistsError: [Errno 17] File exists: './results/10-28-18_cuboid/'`

**Cause**: Started two trainings in the same hour with same exp_name

**Solutions**:
1. Wait until next hour
2. Change exp_name: `--exp_name cuboid_v2`
3. Manually rename existing directory

### Issue 2: No Checkpoints Saved

**Problem**: Training completes but `checkpoints/` is empty

**Causes**:
1. Training didn't reach 20k steps (save_freq threshold)
2. Insufficient disk space
3. Permission issues

**Check**:
```bash
# Did training reach 20k steps?
grep "Episode" ./results/10-28-18_cuboid/log.txt | tail

# Check disk space
df -h .

# Check permissions
ls -la ./results/10-28-18_cuboid/
```

### Issue 3: Checkpoint File Corrupted

**Error**: `RuntimeError: Error loading checkpoint`

**Possible causes**:
1. Training crashed during checkpoint save
2. Disk full during save
3. File system corruption

**Recovery**:
```bash
# Use previous checkpoint
python test.py --checkpoint .../rl_model_90000000_steps/module.pt

# Check file integrity
ls -lh .../rl_model_100000000_steps/module.pt
# Should be ~30MB, not 0 bytes
```

---

## Summary

### Quick Reference

**Directory naming**: `results/<MM-DD-HH>_<exp_name>/`
- Example: `10-28-18_cuboid` = Oct 28 at 6 PM, exp "cuboid"

**Checkpoint naming**: `rl_model_<steps>_steps/module.pt`
- Example: `rl_model_100000000_steps/module.pt` = 100M steps

**Checkpoint frequency**: Every 20,000 training steps (configurable)

**Key files**:
- `checkpoints/rl_model_*/module.pt` - Trained model weights
- `task/config.py` - Task configuration
- `task/train.sh` - Training script used
- `log.txt` - Training logs
- `success_rate.txt` - Evaluation results (if tested)

### File Structure Template

```
results/
└── <MM-DD-HH>_<exp_name>/
    ├── checkpoints/
    │   ├── rl_model_10000000_steps/
    │   │   └── module.pt
    │   ├── rl_model_20000000_steps/
    │   │   └── module.pt
    │   └── rl_model_100000000_steps/
    │       └── module.pt
    ├── task/
    │   ├── config.py
    │   └── train.sh
    ├── log.txt
    └── success_rate.txt
```

---

**For more details, see**:
- `TESTING_GUIDE.md` - How to test checkpoints
- `segmentationfault.md` - Training setup and fixes
- `SESSION_NOTES.md` - Complete debugging history
