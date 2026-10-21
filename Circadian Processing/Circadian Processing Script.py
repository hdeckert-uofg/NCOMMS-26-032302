# in terminal: pip install matplotlib
# in terminal: pip install scipy

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog
import os
from scipy.stats import mannwhitneyu, kruskal

# Parameters

DETREND = True
VARIANCE_NORMALISE = True
#MAX_COMPONENTS_REMOVE: change to either 1, or 2. Capping at 2 is generally safe, but can pull some shared oscillations if oscillatory signal strength > noise. 
#For example, having MAX_COMPONENTS_REMOVE=2 for the synthetic data affects the amplitude at data edges-> change to MAX_COMPONENTS_REMOVE=1
#For the actual data we are working with, capping components at 1 or 2 has little effect on the processed data (see examples)
MAX_COMPONENTS_REMOVE = 2 

# Pick a file

def choose_csv():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename(filetypes=[("CSV","*.csv")])

# Load data

def load_data(path):

    df = pd.read_csv(path)

    cols = df.columns.tolist()
    new_cols=[]
    counts={}

    for c in cols:
        if c not in counts:
            counts[c]=0
            new_cols.append(c)
        else:
            counts[c]+=1
            new_cols.append(f"{c}_{counts[c]}")

    df.columns=new_cols

    time = df.iloc[:,0].values
    X = df.iloc[:,1:].values
    names = df.columns[1:]

    return X,time,names

# Identify groups

def infer_groups_from_names(sample_names, separator="."):

    groups=[]

    for name in sample_names:

        if separator in name:
            g=name.split(separator)[0]
        else:
            g=name

        groups.append(g)

    groups=np.array(groups)

    print("\nDetected groups:")
    for g in np.unique(groups):
        print(g, np.sum(groups==g))

    return groups


# Identify circadian component

def remove_circadian_band(X, time, low=18, high=32):

    T = len(time)

    # Mirror padding
    X_pad = np.vstack([X[::-1], X, X[::-1]])

    dt = np.mean(np.diff(time))
    freqs = np.fft.rfftfreq(len(X_pad), dt)

    band = (freqs >= 1/high) & (freqs <= 1/low)

    X_fft = np.fft.rfft(X_pad, axis=0)

    circadian_fft = np.zeros_like(X_fft)
    circadian_fft[band] = X_fft[band]

    circadian_pad = np.fft.irfft(circadian_fft, n=len(X_pad), axis=0)

    # Remove padding
    circadian_projection = circadian_pad[T:2*T]

    residual = X - circadian_projection

    return residual, circadian_projection


# Component selection

def auto_select_components(U, group_labels):

    groups=np.unique(group_labels)

    n_remove=0
    pvals=[]

    if len(groups)==2:

        g1,g2=groups

        for pc in range(min(U.shape[1],MAX_COMPONENTS_REMOVE)):

            v1=U[group_labels==g1,pc]
            v2=U[group_labels==g2,pc]

            stat,p=mannwhitneyu(v1,v2)

            pvals.append(p)

            if p<0.05:
                break
            else:
                n_remove+=1

    else:

        for pc in range(min(U.shape[1],MAX_COMPONENTS_REMOVE)):

            data=[U[group_labels==g,pc] for g in groups]

            stat,p=kruskal(*data)

            pvals.append(p)

            if p<0.05:
                break
            else:
                n_remove+=1

    if n_remove==0:
        n_remove=1

    print("PCs removed:",n_remove)

    return n_remove,pvals

# SVD denoising

def remove_shared_components(X,time,n_remove):

    X=X.copy()
    T,N=X.shape
    trend = np.zeros_like(X)


    # detrend
    if DETREND:

        t=np.arange(T)

        for j in range(N):

            p=np.polyfit(t,X[:,j],1)
            trend[:,j] = np.polyval(p,t)
            X[:,j] -= trend[:,j]
            
    # mean center
    means=X.mean(axis=0,keepdims=True)
    Xc=X-means

    # variance normalize
    stds=Xc.std(axis=0,keepdims=True)
    stds[stds==0]=1
    X_proc=Xc/stds

    # phase invariant
    X_proc, circadian_projection = remove_circadian_band(X_proc,time)

    # SVD (TRANSPOSED)
    U,s,Vt=np.linalg.svd(X_proc.T,full_matrices=False)

    # protect oscillatory PCs
    freqs = np.fft.rfftfreq(len(time), np.mean(np.diff(time)))
    circadian_band = (freqs > 1/32) & (freqs < 1/18)

    for k in range(len(s)):

        spec = np.abs(np.fft.rfft(Vt[k]))**2
        circ_power = spec[circadian_band].sum()
        total_power = spec.sum()

        if circ_power / total_power > 0.40:
            s[k] = 0  

    var_exp=(s**2)/np.sum(s**2)

    print("\nVariance explained:")
    for i,v in enumerate(var_exp[:10]):
        print(f"PC{i+1}: {v:.3f}")

    if n_remove>0:

        U_k=U[:,:n_remove]
        s_k=s[:n_remove]
        Vt_k=Vt[:n_remove,:]

        noise_proc = (U_k * s_k) @ Vt_k
        noise_proc = noise_proc.T

    else:

        noise_proc=np.zeros_like(X_proc)

    # subtract noise in normalized space
    X_denoised_proc = X_proc - noise_proc

    # ADD BACK circadian projection
    X_denoised_proc = X_denoised_proc + circadian_projection

    # restore variance
    X_denoised_centered = X_denoised_proc * stds

    # restore mean
    X_clean = X_denoised_centered + means

    # restore linear trend
    X_clean = X_clean + trend

    waveforms=Vt[:n_remove].T

    return X_clean,noise_proc,waveforms,var_exp,U,Vt

# Plots

def plot_scree(var_exp):

    plt.figure()
    plt.plot(var_exp[:10],'o-')
    plt.title("Scree plot")
    plt.xlabel("PC")
    plt.ylabel("Variance explained")
    plt.show()


def plot_pc_loadings(U,groups):

    g=np.unique(groups)

    plt.figure(figsize=(8,4))

    for pc in range(3):

        plt.subplot(1,3,pc+1)

        for gg in g:

            vals=U[groups==gg,pc]
            plt.scatter([gg]*len(vals),vals)

        plt.title(f"PC{pc+1}")

    plt.tight_layout()
    plt.show()


def plot_debug(time,X,X_clean,waveforms):

    plt.figure(figsize=(12,10))

    plt.subplot(3,1,1)
    plt.title("Original")
    plt.plot(time,X)

    plt.subplot(3,1,2)
    plt.title("Shared waveforms")
    plt.plot(time,waveforms)

    plt.subplot(3,1,3)
    plt.title("Cleaned")
    plt.plot(time,X_clean)

    plt.tight_layout()
    plt.show()

# Save

def save_output(path,time,X,names):

    folder=os.path.dirname(path)
    base=os.path.splitext(os.path.basename(path))[0]

    out=os.path.join(folder,base+"-cleaned.csv")

    df=pd.DataFrame(X,columns=names)
    df.insert(0,"time",time)

    df.to_csv(out,index=False)

    print("Saved:",out)


def save_waveforms(path,time,waveforms):

    folder=os.path.dirname(path)
    base=os.path.splitext(os.path.basename(path))[0]

    out=os.path.join(folder,base+"_SharedWaveforms.csv")

    df=pd.DataFrame(waveforms,
        columns=[f"PC{i+1}" for i in range(waveforms.shape[1])]
    )

    df.insert(0,"time",time)

    df.to_csv(out,index=False)

    print("Saved:",out)

# Main

def main():

    path=choose_csv()

    if not path:
        return

    X,time,names=load_data(path)

    groups=infer_groups_from_names(names)

    print("\nDiagnostics run")

    _,_,_,var_exp,U,Vt=remove_shared_components(X,time,0)

    plot_scree(var_exp)

    n_remove,pvals=auto_select_components(U,groups)

    n_remove=min(n_remove,MAX_COMPONENTS_REMOVE)

    print("\nFinal removal:",n_remove)

    X_clean,noise,waveforms,var_exp,U,Vt=remove_shared_components(
        X,time,n_remove
    )

    plot_pc_loadings(U,groups)

    plot_debug(time,X,X_clean,waveforms)

    save_output(path,time,X_clean,names)

    save_waveforms(path,time,waveforms)

    print("\nProcessing complete")


if __name__=="__main__":
    main()