import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import os

# Parameters

N_SAMPLES = 16
N_TIMEPOINTS = 121

PERIOD_MIN = 20
PERIOD_MAX = 28

PHASE_STD = np.pi / 6      # ~30° variability
SHARED_NOISE_STRENGTH = 0.2

# Folder pick

def choose_folder():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askdirectory(title="Select output folder")

# Timepoints

time = np.arange(N_TIMEPOINTS)

# Generate shared noise

shared_noise = SHARED_NOISE_STRENGTH * np.random.normal(0,1,N_TIMEPOINTS)

# Generate sine signals

signals = []

for i in range(N_SAMPLES):

    # random circadian period
    period = np.random.uniform(PERIOD_MIN, PERIOD_MAX)

    # random phase shift
    phase_shift = np.random.normal(0, PHASE_STD)

    # random amplitude
    amp = np.random.normal(0, 1)

    # two opposite-phase groups
    if i < N_SAMPLES // 2:
        phase = phase_shift
        signal = amp*np.sin(2*np.pi*time/period + phase)
        signal = signal + shared_noise
        signals.append(signal)

    else:
        signal = shared_noise
        signals.append(signal)

    
 # add shared noise    
signals = np.array(signals).T

# Save

columns = ["time"] + [f"sample_{i+1}" for i in range(N_SAMPLES)]

data = np.column_stack((time, signals))

df = pd.DataFrame(data, columns=columns)

folder = choose_folder()

path = os.path.join(folder, "dataset_circadian_synthetic.csv")

df.to_csv(path, index=False)

print("Saved:", path)