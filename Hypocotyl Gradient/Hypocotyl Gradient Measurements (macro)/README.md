# Hypocotyl Gradient Measurements- ImageJ Macro

## Overview
This macro plots profiles for segmented lines for each frame in a whole one-channel stack (.tiff) and saves them in Excel format. The output is an Excel file with multiple sheets, each sheet is data from one frame and contains a table with pixel profiles of all segmented lines provided. 
  
## Getting started

### Dependencies

- Fiji 2.16.0/1.54p or later
	* to install: https://imagej.net/software/fiji/downloads 
- Windows 10 (Version 22H2)

  * *Check the macro if using on macOS devices- current macro version should run smoothly on Mac but there has been some issues in the past with certain commands (mainly related to thresholding)*

### ImageJ Tools/Plugins Required

- MultiMeasure
  - see https://www.optinav.info/Multi-Measure.htm if not already pre-installed

- Read and Write Excel
  - see https://imagej.net/plugins/read-and-write-excel if not already pre-installed

Expected install time: >5 min if not already pre-installed

### Demo
Example image stack (*Example image stack (genotype 12).tiff*) and segmented line ROI list (*12-gradientRoiSet.zip*) are provided in the *Example data* folder. Expected output included as *12-gradient.xlsx*.
<br>Expected demo run time: 1-2 min (depends on the number of ROIs and frames)

## Executing program

### Macro Requirements

This is a supplementary document to the Macro “Hypocotyl Gradient Measurements”. It describes the commands and provides rationale for including various elements found throughout the script.

**Open your image stack (one channel, one slice, t frames) before running the script.**

The image stack must contain only one channel and multiple frames.

If you open the script through ImageJ (Plugins>>Macro>>Edit…) and click “Run” below the script you are welcomed with a window that lets you median filter the image and choose a name for an .xlsx file with your measured data.

```
Dialog.create("Hypocotyl Gradient Measurement");
	Dialog.addChoice("Have you median filtered the image? \n (If not, median filtering with px=2 will be performed)", newArray("No", "Yes"));
	Dialog.addString("Save Excel file as XXX-gradient.xlsx :", "XXX");
Dialog.show();
```
*You need to decide whether median filtering is needed for your measurements- median filter if you expect your data profiles to be noisy otherwise.*

**How to make a segmented line ROIs list**
<br> You need to provide your segmented lines ROI list (.zip file) before running the script. It should be saved in the same folder as your image stack. Profiles will be sequentially measured for all the provided segmented lines frame by frame.
1. Open your image stack and MultiMeasure tool (Plugins >> MultiMeasure)
2. Make a segmented line selection and add it to the list (*spacebar* or click *Add* in the MultiMeasure window)
3. Click *Toggle Select All*, followed by *Save* 
4. Save the .zip file in the same folder as your image

Next, the macro opens a dialog window with the folder your image stack (.zip file) is saved to. 
```
path = File.openDialog("Select .zip file");
  dirZIP = File.getParent(path);
  nameZIP = File.getName(path);
```

### Macro

This macro:
1) Performs median filtering (if selected)

```
if (filter == "No"){
	run("Median...", "radius=2 stack");
}
```

2) Measures pixel profiles for the provided segmented lines list for each frame in the stack

```
run("ROI Manager...");

roiManager("Open", path);	

for (f=1; f<= frames; f++) {
	
run("Clear Results");	

for (i = 0; i < roiManager("Count"); i++) {
A=i+1;
roiManager("Select", i);

selectImage(img);
Stack.setFrame(f);

profile = getProfile(); 

for (n=0; n<profile.length; n++){
setResult(A, n, profile[n]);
updateResults();
}

}
```

3) Saves the results as an Excel file

```
for (f=1; f<= frames; f++) {

...

selectWindow("Results");
//saveAs("Results",dir + f + "-" + img +"Gradient.csv");

run("Read and Write Excel", "file=[" + dir + excel + "-gradient.xlsx] sheet=Frame-" + f);

}
}
else {
waitForUser("The provided ROI file is not in a .zip format \n Please select a correct file");
}

print("All done!");
```

## Authors

Hanna Deckert (contact: Hanna.Deckert@glasgow.ac.uk)
<br> at Matt Jones lab, University of Glasgow (Matt.Jones@glasgow.ac.uk)

## Acknowledgements

I would like to acknowledge the invaluable image.sc and reddit threads and many thanks to the people who have contributed their answers:
<br> MurphysLab https://www.reddit.com/r/ImageJ/comments/3eckjn/macro_help_need_to_continuously_update_results/
<br> Antinos https://forum.image.sc/t/writing-macro-that-exports-results-to-excel-file-and-does-not-overwrite-previous-results/31343/15 
<br> Wayne Rasband http://imagej.273.s1.nabble.com/Let-the-user-choose-a-file-td3698562.html#a3698563