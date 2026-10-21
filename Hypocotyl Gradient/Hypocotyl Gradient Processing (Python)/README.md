# Hypocotyl Gradient Processing

## Overview
This Python application is designed to process (that is, standardise, align, merge, and normalise) hypocotyl gradient datasets generated using the *Hypocotyl Gradient Measurements* ImageJ macro and stored in Microsoft Excel workbooks. The app was developed to process pixel profile measurements collected from multiple samples of varying lengths, enabling direct comparison between biological replicates. If the pixel values represent roGFP2-Orp1 ratios, the program also allows automated calculation of roGFP2-Orp1 oxidation degree.

## Getting started

### Dependencies

- Python 3.14 or later
  - NumPy
  - Pandas
  - Openpyxl
  - Tkinter

Required Python libraries are automatically installed if missing when the script is launched:
```
required_libs = ["pandas", "numpy", "openpyxl"]
for lib in required_libs:
    try:
        importlib.import_module(lib)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
```
Expected install time: 1-5 min
- Windows 10 (Version 22H2) 
 <br> The script was developed and tested on Windows systems but should also run on macOS and Linux with appropriate Python installations.

 ### Demo
 A real demo dataset (*12-gradient.xlsx*) can be found in the *Example data* folder. Two generated outputs are included: for data alignment (*processed_single_20261005_172055.xlsx*) and oxidation degree calculation (*calculated_20261005_172059.xlsx*)
<br>For the roGFP2-Orp1 OxD calculations, the values provided below can be used:
- *a* : 0.1116
- *b* : 0.3438
- *R<sub>ox</sub>* : 0.5274549
- *I<sub>min/max</sub>* : 0.588214

<br>Expected demo run time: approx. 10 s

## Executing program
Upon running the script, a graphical user interface will open, allowing file selection and processing options to be configured.

### Input Requirements

#### Excel Workbook Format
The script expects .xlsx workbooks containing one or more worksheets.

Each worksheet should contain:
1. A title row (preserved during processing).
2. Numerical measurement columns (can contain NaN- these cells will be changed to empty cells during processing).
3. Column headers numbered sequentially (e.g. 1, 2, 3, 4). 
4. Workbook sheets labelled *Frame-* and corresponding frame number (e.g. Frame-1, Frame-2,...). The frames do not have to be in ascending order.
   
Example:
| file | metadata  | in row 1 |  |  |
| --------  | -------- | --------  | -------- | --------  |
| Count |  1  | 2 | 3 | 4 |
| 1 | 0.6847 | 0.7341 | 0.1344 | 0.8375 |
| 2 | 0.64271 | 0.6935 | NaN | 0.6273 |
| 3 | ...   | ... | ... | ... |

Columns may contain different numbers of measurements. The script aligns all columns to the length of the longest measurement series.
 <br> **Excel workbooks generated using the *Hypocotyl Gradient Measurements* ImageJ macro already satisfy all the above requirements.**


#### roGFP2-Orp1 Oxidation Calibration Parameters
In order to use the roGFP2-Orp1 oxidation degree calculation option, certain parameters need to be provided. The parameters are experimentally estimated by treating a subset of sample replicates with H<sub>2</sub>O<sub>2</sub> and DTT (or other reducing agent) to induce full oxidation and reduction of the roGFP2-Orp1 probe, respectively.

The following values must be supplied through the graphical interface:

| Parameter | Description  |
| --------  | -------- | 
| *a* |  gradient for R<sub>red</sub> vs R<sub>baseline</sub> line-of-best-fit | 
| *b* |  y-intercept for R<sub>red</sub> vs R<sub>baseline</sub> line-of-best-fit  | 
| *R<sub>ox</sub>* |  Average R<sub>395/453</sub> for fully oxidised samples | 
| *I<sub>min/max</sub>* |  Ratio of fluorescence intensity for 453/515 ex/em channel for fully oxidised (min) over reduced (max) samples  | 

Values *a* and *b* are used to calculate *R<sub>red</sub>* :
$$ R_{red} = a × ln ( R_{baseline} ) + b $$
where *R<sub>baseline</sub>* is the average pixel value (if they represent roGFP2-Orp1 ratio values) of an individual sample for Frame 1

The oxidation degree (OxD) calculation applied to every measurement is:
$$ OxD = { R - R_{red} \over
I_{min/max} × (R_{ox} - R) + (R - R_{red}) } $$

The calculated values replace the original measurement values in the output workbook.

### Processing Workflow
The script provides a user-friendly graphical interface and supports:
1. Automatic processing and alignment of unequal-length measurement series for individual Excel workbooks.
   - All columns are aligned to the longest column in the dataset/s. Empty cells are added and equally distributed along all the sample columns to match the length of the longest sample column.
2. Merging, processing, and aligning two workbooks into a single dataset.
3. Application of the roGFP2-Orp1 oxidation degree formula
   - This step can be applied independently to the merging and aligning option. Simply tick off *Process.Merge Files* option. Separate oxidation degree calculation can only be done on single files.
   - Empty cells and zero values are treated as missing data during averaging calculations.


The output file is saved as either *processed_single_YYYYMMDD_HHMMSS.xlsx*, *merged_processed_YYYYMMDD_HHMMSS.xlsx*, or *calculated_YYYYMMDD_HHMMSS.xlsx* depending on the selected processing type.

## Authors
Magdalena Czech, University College London (magdalena.czech.25@ucl.ac.uk)
<br>Hanna Deckert (contact: Hanna.Deckert@glasgow.ac.uk)
<br> at Matt Jones lab, University of Glasgow (Matt.Jones@glasgow.ac.uk)

## Acknowledgements

The script was generated with the assistance of generative AI (OpenAI) and validated on real data (see supplementary files). 
<br> The readme file was generated with assistance of Microsoft Copilot (version: 2.20260928.61.0). 
