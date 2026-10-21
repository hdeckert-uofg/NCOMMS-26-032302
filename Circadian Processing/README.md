# Circadian Processing Script

## Overview

This Python script removes shared non-biological variation from circadian time-series datasets while preserving oscillatory signals within the circadian range. It uses singular value decomposition (SVD) to identify components shared across samples, automatically determines how many components to remove based on group comparisons, and generates denoised output suitable for downstream circadian analyses. The script was developed to process biological time-series measurements that include multiple genotypes, treatments, or experimental groups. It works best with irregular 'spiky' noise sources that are shared among all samples. The script assumes regularly sampled time-series data.

## Getting started

### Dependencies

- Python 3.14 or later
  - NumPy
  - pandas
  - matplotlib
  - scipy
  - tkinter (included with most Python installations)

Install required packages (type in the terminal):

	pip install numpy pandas matplotlib scipy
Expected installation time: >5 min

- Windows 10 (Version 22H2) 
 <br> The script was developed and tested on Windows systems but should also run on macOS and Linux with appropriate Python installations.

 ### Demo
One real (*data-example-C1.csv*) and simulated (*dataset_synthetic-C1.csv*) dataset are provided in the *Synthetic and Real Data* folder (Python script for generating the simulated data also provided). Expected outputs for the demo data are included in corresponding subfolders. 
 <br> Expected demo run time: 10-20 s

## Executing program
** *DISCLAIMER* **
<br> The denoising script is not to be used when: 
1. The noise is not completely shared
   - See example data for examples of homogeneous non-biological noise. In our case, the noise came from differences in plate illumination/ camera exposure that varied from frame to frame during imaging.
2.  The shared variation is biological 
       - For example, when samples were treated during imaging, which results in non-oscillatory signal change of biological significance.
       - **Any treatment-induced changes mid-imaging will likely be treated as noise and removed from the dataset by the script** therefore caution is advised. Do not use the script if you expect to see any other sources of biological signal changes other than circadian oscillations.

Carefully examine your data. **If you notice any parts of your time series that heavily impacts variance, remove them from the dataset.** It happens quite often with circadian data that the signal is much stronger in the beginning of the experiment and dampens after a couple of hours. In such cases, the beginning of the time series will inflate the variance calculated for each sample in a way that it will no longer represent the sample variance observed throughout the rest of the dataset. If possible, trim the dataset so that all samples show a similar amplitude range throughout the entire time series.  

### Input Requirements

The input file must be a .csv file where:

1. Column 1 contains time points. No header required.
2. Remaining columns contain sample measurements.
3. Each column represents an individual replicate or sample.
4. Samples belonging to the same group share the same sample name (full stop allowed as the naming convention, for example 407.03 as the group name).

Example:
|  |  WT   | WT | mut | mut |
| --------  | -------- | --------  | -------- | --------  |
| 0 |  0.275  | 0.281 | 0.231 | 0.238 |
| 1 | 0.271 | 0.278 | 0.234 | 0.233 |
| 2 | 0.270 | 0.279 | 0.233 | 0.231 |
| 3 | ...   | ... | ... | ... |

### Processing Workflow

The script:
1. Loads a .csv file containing time-series measurements.
2. Automatically identifies experimental groups based on sample names.
3. Removes linear trends and normalises variance between samples.
4. Temporarily isolates circadian-frequency signals (here 18-32 h period range) to protect them during denoising.
5. Uses SVD to identify shared components across all samples.
6. Automatically determines how many components to remove using statistical tests (can be capped using user-defined parameters).
7. Restores the circadian signal and original scaling after denoising.
8. Generates diagnostic plots.
9. Saves cleaned data and removed shared waveforms as .csv files.

A file-selection window will appear, allowing you to choose the input .csv file.

Several parameters can be modified near the beginning of the script:
```
DETREND = True
VARIANCE_NORMALISE = True
MAX_COMPONENTS_REMOVE = 2 
```
Detrending removes a linear trend from each sample before decomposition and restores it after processing.
<br>Normalises variance between samples before SVD analysis. 
<br>**Both detrending and variance normalisation are best practice when SVD is used- they should always be included.**

MAX_COMPONENTS_REMOVED limits the number of shared components that may be removed.
Recommended values:
- 1 for synthetic or highly regular datasets
- 2 for most biological datasets

According to testing included in the script supplemental, values above 2 may lead to oversubtraction.

#### 1. Group Detection
Group information is automatically inferred from column names. The detected groups and replicate counts are printed to the console.
```
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
```
#### 2. Circadian Signal Protection
Before decomposition, the script identifies oscillatory components with periods between 18 and 32 hours using Fourier analysis and temporarily removes them from the dataset. This prevents circadian rhythms from being incorrectly identified as shared noise, as denoising is then performed on the residual signal. After denoising, the circadian component (circadian_projection) is restored.

```
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
```
#### 3. PCA diagnostics
Before the SVD-based denoising, PC analysis is performed to assess group similarity. If the given component is not statistically different between experimental groups, it will be removed during SVD denoising (assuming shared noise is the main driver of similarity between them). Higher-order components are removed until statistically significant group separation is detected (p < 0.05). Why? We want to subtract shared noise, hence PCs that are different between the groups do not satisfy this condition.
<br>In case of experimental conditions where all groups are biologically identical, the maximum number of components to be removed is capped (MAX_COMPONENTS_REMOVE parameter). For example, if *MAX_COMPONENTS_REMOVE=2*, only the first and second PCs is removed even when the third PC is not statistically different between the groups. At least one component is always removed.
```
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
```
<br>Statistical tests used:
- Two groups: Mann-Whitney U test
- Three or more groups: Kruskal-Wallis test
#### 4. SVD Analysis

The processed data are decomposed using singular value decomposition. The shared waveform is removed as shared noise, but all the other original sample characteristics are restored: circadian oscillations, variance and mean, and linear trends.
<br>The script reports the variance explained by each principal component.
```
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
```
#### 5. Diagnostic Plots
The script generates three diagnostic outputs:

**Scree Plot**
<br>Displays variance explained by the first principal components.
```
def plot_scree(var_exp):

    plt.figure()
    plt.plot(var_exp[:10],'o-')
    plt.title("Scree plot")
    plt.xlabel("PC")
    plt.ylabel("Variance explained")
    plt.show()
```
**PC Loading Plot**
<br>Shows sample loadings for the first three principal components grouped by treatment. Helps visualise statistical significance tests.
```
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
```
**Denoising Plot**
<br>Displays the original data, shared waveforms (to be removed), and the cleaned data. These plots help assess whether component removal behaved as expected.
```
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
```
### Output Files
The denoised dataset is saved as *OriginalFile-cleaned.csv* in the parent folder. It contains the original time column and processed sample measurements. The removed shared components are saved as *OriginalFile_SharedWaveforms.csv*. 
```
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
```
## Authors

Hanna Deckert (contact: Hanna.Deckert@glasgow.ac.uk)
<br> at Matt Jones lab, University of Glasgow (Matt.Jones@glasgow.ac.uk)

## Acknowledgements

The script was generated with the assistance of generative AI (OpenAI) and tested on both synthetic and real data (see supplementary files). We thank Dr Rónán Daly (University *of* Glasgow) for invaluable feedback regarding script validation methods.
<br> The readme file was generated with assistance of Microsoft Copilot (version: 2.20260928.61.0). 
