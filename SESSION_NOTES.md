# MAPush Project - Session Notes

## Project Overview
- **Location**: `/home/gvlab/MAPush`
- **Type**: Reinforcement learning project using Isaac Gym
- **Environment**: Conda environment named `mapush`
- **Hardware**: NVIDIA GeForce RTX 2070 (8GB VRAM)

## Recent Work & Issues

### ROOT CAUSE ANALYSIS - Training Failures

#### Issue 1: OpenRL Circular Import Bug (FIXED ✅)
**Problem**: Training script crashed with circular import error before driver issues were relevant

**Error**: `AttributeError: partially initialized module 'openrl.utils.callbacks.callbacks' has no attribute 'BaseCallback'`

**Root Cause**: OpenRL v0.2.0 has circular import chain:
- `type_aliases.py` → `callbacks.py` → `base_agent.py` → `rl_driver.py` → `type_aliases.py`

**Fix Applied** (patches to conda environment):
1. Modified `/home/gvlab/miniconda3/envs/mapush/lib/python3.8/site-packages/openrl/utils/type_aliases.py`:
   - Added `TYPE_CHECKING` import
   - Moved `callbacks` import inside `TYPE_CHECKING` block
   - Changed type hints to use string literals: `"callbacks.BaseCallback"`

2. Modified `/home/gvlab/miniconda3/envs/mapush/lib/python3.8/site-packages/openrl/utils/callbacks/callbacks.py`:
   - Added `TYPE_CHECKING` import
   - Moved `BaseAgent` import inside `TYPE_CHECKING` block
   - Moved `callbacks_factory` import to inside the `__init__` method where it's actually used

**Result**: Circular import resolved! Training now progresses past import stage.

---

#### Issue 2: NVIDIA Driver Compatibility (ACTIVE ISSUE ⚠️)
**Problem**: Training crashes with **Segmentation fault** immediately after "GPU Pipeline: enabled"

**Current Driver**: 580.95.05 (September 2025 release)

**Why Driver 550 Was Attempted**:
- Driver 550 is NOT available in Ubuntu repositories for this system
- Available versions: 418, 450, 470, 535, 545, 570, 580 (recommended)
- Ubuntu auto-reinstalls driver 580 on reboot (marked as "recommended")

**Isaac Gym Requirements** (from `/home/gvlab/isaac_gym/isaacgym/docs/install.html`):
- Minimum driver: **470**
- Supported: Python 3.6-3.8, Ubuntu 18.04/20.04
- Isaac Gym Preview 4 (rc4) released ~2021-2022
- **Gap**: 3-4 years between Isaac Gym and driver 580 (Sep 2025)

**Segfault Evidence**:
```
Using GPU PhysX
Physics Engine: PhysX
Physics Device: cuda:0
GPU Pipeline: enabled
Segmentation fault (core dumped)
```

**What Works** (driver 580 is functional):
✅ nvidia-smi detects GPU
✅ PyTorch CUDA 12.1 available
✅ Isaac Gym initializes: `gymapi.acquire_gym()` succeeds
✅ Physics engine starts

**What Fails**:
❌ Crashes during PhysX GPU pipeline initialization (likely driver API changes)

---

### Recommended Solutions (in order of preference)

#### Option 1: Install Driver 535 (RECOMMENDED ⭐)
Driver 535 is available in Ubuntu repos and is the newest "stable" branch before the 5xx series.

**Steps**:
```bash
# Remove driver 580
sudo apt remove --purge nvidia-driver-580 nvidia-dkms-580

# Install driver 535
sudo apt install nvidia-driver-535

# Reboot
sudo reboot

# Verify after reboot
nvidia-smi  # Should show 535.xxx.xx
```

**Why this is best**:
- Available in Ubuntu repositories (easy to maintain)
- Newer than Isaac Gym minimum (470)
- Tested era (2023) closer to Isaac Gym's release period
- Less likely to have compatibility issues

#### Option 2: Install Driver 470 (SAFE BUT OLD)
Use Isaac Gym's exact minimum requirement.

```bash
sudo apt remove --purge nvidia-driver-580 nvidia-dkms-580
sudo apt install nvidia-driver-470
sudo reboot
```

**Pros**: Matches Isaac Gym minimum requirement exactly
**Cons**: Very old driver (2021), may have security/performance issues

#### Option 3: Prevent Ubuntu from Auto-Installing 580
If you try other drivers, prevent 580 from coming back:

```bash
sudo apt-mark hold nvidia-driver-580
```

#### Option 4: Try CPU-Only Mode (TEMPORARY WORKAROUND)
For testing/debugging without GPU:
```python
# In train.py, check if there's a --device cpu flag or similar
# Isaac Gym might support CPU-only physics (much slower)
```

---

### Git Status
Modified files:
- `results/10-15-23_Tblock/success_rate.txt`
- `task/cuboid/train.sh`

### Recent Commits
- 0e61e1b: Update README.md
- 4736a5c: Update README.md
- 6d6a5d8: arxiv paper
- Branch: main

## Known Issues
- Conda environment has libtinfo.so.6 version warning (minor, not blocking)

## Project Structure Notes
- Training scripts in `task/cuboid/`
- Results stored in `results/` directory
- Uses OpenRL framework
- Isaac Gym Python examples in `/home/gvlab/isaac_gym/isaacgym/python/`

## Summary

**The real problem involves multiple compatibility issues:**

1. **Primary Bug**: OpenRL v0.2.0 circular import bug (FIXED ✅ with patches)
2. **CUDA Version Chaos**: Mixed CUDA 11.x and 12.x packages (FIXED ✅ - cleaned up to consistent 11.6)
3. **Driver + Training Compatibility**: Driver 470 installed, but segfaults persist (ACTIVE ⚠️)

**What We've Tried:**
- ✅ Driver 580 → 535 → 470 (segfaults persist)
- ✅ PyTorch 2.3.1+cu121 → 1.13.1+cu117 → 1.13.1+cu116
- ✅ Removed ALL CUDA 12.x packages (nvidia-cuda-*, torchaudio)
- ✅ Isaac Gym basic test PASSED (gymtorch extension loads successfully)
- ✗ Training script still segfaults after "GPU Pipeline: enabled"

**Key Finding**:
- Basic Isaac Gym operations work fine (sim creation, GPU pipeline)
- gymtorch extension compiles and loads successfully
- Segfault happens during environment/actor creation in training script
- Isaac Gym PyTorch example ran without segfault (but timed out)

**Current Theory**: Issue may be in MAPush environment setup code, not Isaac Gym/driver itself.

**Next Actions to Try**:

### SOLUTION A: Try Driver 535 Again (RECOMMENDED ⭐)
Now that CUDA packages are clean (no more 12.x conflicts), driver 535 may work.

**Commands to run:**
```bash
# 1. Remove driver 470
sudo apt remove --purge nvidia-driver-470 nvidia-dkms-470

# 2. Install driver 535
sudo apt install nvidia-driver-535

# 3. Reboot
sudo reboot

# After reboot, verify driver:
nvidia-smi  # Should show 535.xxx.xx

# 4. Test training:
conda activate mapush
cd /home/gvlab/MAPush
timeout 120 python ./openrl_ws/train.py --num_envs 2 --train_timesteps 1000 --algo ppo --config ./openrl_ws/cfgs/ppo.yaml --seed 1 --exp_name test_535 --task go1push_mid --headless
```

---

### SOLUTION B: Debug MAPush Environment Creation
If Solution A fails, the issue is in MAPush environment setup code.

**Steps:**
1. Run Isaac Gym RL examples to verify framework works
2. Debug train.py step-by-step to find exact crash point
3. Check MAPush's mqe/envs/ code for incompatible Isaac Gym API calls

**Commands:**
```bash
# Test Isaac Gym RL example
cd /home/gvlab/isaac_gym/isaacgym/python/examples
timeout 60 conda run -n mapush python joint_monkey.py --headless

# Debug MAPush environment creation
cd /home/gvlab/MAPush
conda activate mapush
# Add print statements to openrl_ws/utils.py and mqe/envs/utils.py
# to find exact crash location
```

**Test Command**:
```bash
conda activate mapush
cd /home/gvlab/MAPush
python ./openrl_ws/train.py --num_envs 2 --train_timesteps 1000 --algo ppo --config ./openrl_ws/cfgs/ppo.yaml --seed 1 --exp_name test_run --task go1push_mid --headless
```

## Environment Details (CURRENT - 2025-10-28)
- **Python**: 3.8 (mapush conda environment)
- **PyTorch**: 1.13.1+cu116 (CLEAN - no CUDA 12.x packages)
- **CUDA**: 11.6 (driver supports 11.4, should be compatible)
- **OpenRL**: 0.2.0 (with applied patches for circular imports)
- **Isaac Gym**: Preview 4 (1.0rc4) - binaries from June 28, 2022
- **Current Driver**: 535.274.02 (CUDA 12.2 support - back from 470)

---

## Critical Fixes Applied This Session ✅

### 1. OpenRL Circular Import Bug
**Files patched:**
- `/home/gvlab/miniconda3/envs/mapush/lib/python3.8/site-packages/openrl/utils/type_aliases.py`
- `/home/gvlab/miniconda3/envs/mapush/lib/python3.8/site-packages/openrl/utils/callbacks/callbacks.py`

### 2. CUDA Package Cleanup (CRITICAL!)
**Removed conflicting CUDA 12.x packages:**
```bash
pip uninstall -y nvidia-cublas-cu12 nvidia-cuda-cupti-cu12 nvidia-cuda-nvrtc-cu12 \
  nvidia-cuda-runtime-cu12 nvidia-cudnn-cu12 nvidia-cufft-cu12 nvidia-curand-cu12 \
  nvidia-cusolver-cu12 nvidia-cusparse-cu12 nvidia-nccl-cu12 nvidia-nvjitlink-cu12 \
  nvidia-nvtx-cu12 torchaudio
```

**Installed clean PyTorch:**
```bash
pip install torch==1.13.1+cu116 torchvision==0.14.1+cu116 \
  --index-url https://download.pytorch.org/whl/cu116
```

### 3. Driver Changes
- Started with: 580.95.05 (too new, segfaults)
- Tried: 535.274.02 (segfaults with mixed CUDA packages)
- **Current**: 470.256.02 (still segfaults, but CUDA is now clean)
- **Next try**: 535 again with clean CUDA packages

---

## Quick Reference: Why Each Fix Was Needed

| Issue | Symptom | Root Cause | Fix |
|-------|---------|------------|-----|
| Import Error | `AttributeError: 'callbacks'` | OpenRL circular imports | Patched with TYPE_CHECKING |
| Segfault | Crash at "GPU Pipeline: enabled" | Mixed CUDA 11.x + 12.x packages | Removed all cu12 packages |
| Wrong PyTorch | N/A | torchaudio 2.3.1+cu121 incompatible | Removed, using torch 1.13.1+cu116 |
| Driver too new | Possible API incompatibility | Driver 580 (2025) vs Isaac Gym (2022) | Downgraded to 470/535 |

---

## After Reboot Checklist

```bash
# 1. Verify driver
nvidia-smi

# 2. Verify conda environment
conda activate mapush
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.version.cuda}, Available: {torch.cuda.is_available()}')"

# 3. Check no CUDA 12.x packages
pip list | grep cuda

# 4. Test Isaac Gym basic
python -c "from isaacgym import gymapi; gym = gymapi.acquire_gym(); print('✓ Isaac Gym works')"

# 5. Test training
cd /home/gvlab/MAPush
timeout 120 python ./openrl_ws/train.py --num_envs 2 --train_timesteps 1000 --algo ppo --config ./openrl_ws/cfgs/ppo.yaml --seed 1 --exp_name test_run --task go1push_mid --headless
```

---

## 🎯 ROOT CAUSE DISCOVERED (2025-10-28)

After extensive debugging with driver 535.274.02 (switched back from 470), the **true cause of the segfault has been identified**:

### The Real Problem: CUDA Out of Memory During Terrain Creation

**Crash Location**: `mqe/envs/base/legged_robot.py:316` - inside `_create_terrain()` method

**Error Message** (visible when terrain creation is skipped):
```
[Error] [carb.gym.plugin] Gym cuda error: out of memory: ../../../source/plugins/carb/gym/impl/Gym/GymPhysX.cpp: 1721
```

### Debug Timeline

1. ✅ `gym.create_sim()` completes successfully (prints "GPU Pipeline: enabled")
2. ❌ `_create_terrain()` crashes with segfault due to CUDA OOM
3. ⏭️ `_create_envs()` never reached
4. ⏭️ `gym.prepare_sim()` never reached

### What This Means

The "segmentation fault" is actually a **CUDA out of memory error** that manifests as a segfault. This explains why:
- Different drivers behave differently (memory management varies)
- The crash happens at the same point regardless of driver version
- Basic Isaac Gym operations work fine (they use less memory)

### Hardware Constraint

**GPU**: NVIDIA GeForce RTX 2070 with **8GB VRAM** - this might be insufficient for the MAPush environment's terrain generation with current settings.

### Potential Solutions

1. **Reduce num_envs** (currently testing with 2 - try with 1)
2. **Simplify terrain** (switch from 'heightfield'/'trimesh' to 'plane')
3. **Reduce terrain complexity** in config
4. **Check PhysX memory settings** in sim_params
5. **Try different GPU pipeline settings**

### Files Modified for Debugging (can be reverted)
- `/home/gvlab/MAPush/debug_env.py` (created)
- Temporary debug prints added (now removed) to:
  - `mqe/envs/base/base_task.py`
  - `mqe/envs/base/legged_robot.py`

### Next Steps

Try training with minimal configuration to reduce VRAM usage.
