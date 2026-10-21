# roGFP2 Image Processing Pipeline

## Overview

This ImageJ Macro was written to work with 3-channel .tiff files: it first subtracts background noise (here plant autofluorescence) from individual roGFP2 emission channels and then generates the roGFP2 ratio (Ratio<sub>UV ex/blue ex</sub>) image stack. The purpose of the macro was to process macroscopic whole-plant images (see example .tiff file), but it can potentially work with microscopy images as well. See below for more details about channel requirements. 

## Getting started

### Dependencies

- Fiji 2.16.0/1.54p or later
	* to install: https://imagej.net/software/fiji/downloads 
- Windows 10 (Version 22H2)

  * *Check the macro if using on macOS devices- current macro version should run smoothly on Mac but there has been some issues in the past with certain commands (mainly related to thresholding)*

### ImageJ Tools/Plugins Required

- Circle Tool
  - copy text available at: https://imagej.net/ij/macros/tools/CircleTool.txt and paste it at the end of *StartupMacros.fiji* file in the *macros* folder of the Fiji app
- MultiMeasure
  - see https://www.optinav.info/Multi-Measure.htm if not already pre-installed

Expected install time (if not pre-installed): 1-5 min

### Demo
An example image stack (*WT-LUMOB-141_70-2_MMStack_Default.ome-1.tiff*) is provided in the *Example data* folder. The stack consists of four rows of Arabidopsis seedlings. The first row is roGFP2 negative plants that are used for background/autofluorescence correction (see *Macro Requirements* below), and the rows below are seedlings expressing roGFP2-Orp1. The expected output files can be found in the *Processed stacks* folder.
<br>Expected demo run time: 2-5 min

## Executing program

### Macro Requirements

This is a supplementary document to the Macro “roGFP Image Analysis- Ratiometric Image”. It describes the commands and provides rationale for including various elements found throughout the script.

**Always include plants that do not express roGFP2 (i.e. roGFP2 -ve plants) on your images- the autofluorescence signal form them will be used during background subtraction***

Each image stack contains i) 3 channels:
1.	453/515nm channel (i.e. 453 nm excitation, 515 nm emission)
2.	395/515nm channel
3.	395/460nm channel (autofluorescence channel)

**The order of your images is crucial for the macro to work properly (453/515, then 395/515, then 395/460 nm).**

And ii) t number of frames (e.g. an experiment that takes images every hour for 2 days would have 48 frames).

**Open your image stack before running the script.**

If you open the script through ImageJ (Plugins>>Macro>>Edit…) and click “Run” below the script, you are welcomed with a window to choose the autofluorescence correction method.

```
Dialog.create("roGFP Image Processing");
	Dialog.addChoice("Autofluorescence correction:", newArray("Dynamic only", "C460 Mean, C400 Dynamic", "Frame-by-Frame Only", "Mean only", "None"));
	Dialog.addCheckbox("Stack registration?", false);
	Dialog.addCheckbox("Measure (requires ROI Set)?", false);
	Dialog.addCheckbox("Calibrated ratio image?", false);
Dialog.show();
```

Before running the macro, you need to find values included in the script that are used to subtract the autofluorescence signal from the 453/515nm and 395/515nm channels. There are four different autofluorescence subtraction methods available:

-	For *Mean only* you need:
1)	Mean pixel intensity of roGFP2 -ve plants at the 453/515 nm channel (single value, will be subtracted from each frame)
2)	Mean pixel intensity of roGFP2 -ve plants at the 395/515 nm channel (single value, will be subtracted from each frame)

-	For *Frame-by-Frame only* you need:
1)	Mean pixel intensity of roGFP2 -ve plants at the 453/515 nm channel for each individual frame.
<br>Measure pixel intensity from regions of interest (ROIs) using the MultiMeasure plugin and take averages for each frame. Paste the mean values into a separate Excel file in the first column starting from A2. Put ‘C’ into A1 cell. Name the file XXX-460, where you replace XXX with the name of your genotype, and save it as a .csv file **in the folder where the image stack is stored**. It should look like:

|  |  A   | 
| --------  | -------- |
| 1 | C    | 
| 2 | 674.2555 | 
| 3 | 673.01 | 
| 4 | ...   | 

**Please note that in Excel you need to save the file as CSV and NOT CSV UTF-8.**

2)	Mean pixel intensity of roGFP2 -ve plants at 395/515 nm channel for each individual frame. Name the file XXX-400, where you replace XXX with the name of your genotype, and save it as a .csv file in the stack folder.

- For *C460 Mean, C400 Dynamic* you need:

1)	Mean pixel intensity of roGFP2 -ve plants at 453/515 nm channel 
2)	Gradient and y-intercept of the line-of-best-fit for 395/515nm vs 395/460nm (y vs x) plot for roGFP2 -ve plants

    You only need to find the gradient and the intercept once per experiment. That is, if your experiment contains image stacks for multiple treatments, you only need to use one or selected stacks to find these values. Make sure you have a representative set of ROIs- around 50 of 1-2 px circle ROIs is a good number. There is a linear relationship between 395/515nm and 395/460nm channels. Make sure you don’t select areas where very bright ‘dust’ speckles are in the 395/460nm channel- they will significantly increase the mean pixel value of the ROI which would in turn impact the line-of-best-fit.

    Split your channels (Image>>Color>>Split Channels). Create your ROIs in MultiMeasure, set measurement to ‘Mean gray value’, and click Measure. In Excel, make a scatterplot of 395/515nm vs 395/460nm. You can read the gradient and y-intercept from the x-y scatterplot.
    
    Input the numbers in the next pop-up window, for example:

```
if (autofluo == "Dynamic only") {
	Dialog.create("Autofluorescence correction");
		Dialog.addString(".csv file named as XXX-460:", "WT");
		Dialog.addNumber("Gradient 400/515 nm:", 0.4562);
		Dialog.addNumber("y-Intercept 400/515 nm:", 239);
	Dialog.show();
    ...
    }
```

-	For *Dynamic only* you need:
1)	Mean pixel intensity of roGFP2 -ve plants at 453/515 nm channel for each individual frame. Name the file XXX-460, where you replace XXX with the name of your genotype, and save it as a .csv file.
2)	Gradient and y-intercept of the line-of-best-fit for 395/515nm vs 395/460nm (y vs x) plot for roGFP2 -ve plants

**The Dynamic only correction is the most sensitive and should be used whenever possible.**

### roGFP Image Processing Macro

This macro allows to:
1)	Create a mask that excludes pixels that do not belong to roGFP-expressing plants and sets the background pixels to NaN
2)	Subtract autofluorescence signal from 453/515 nm and 395/453 nm channels based on the selected autofluorescence correction method
3)	Divide the two processed channels by each other (395/453 nm by 453/515 nm) to obtain a ratiometric stack
4)	Improve the quality of the ratiometric and corrected double-channel stacks by removing ‘nonsense’ pixels using human intervention

Additionally, the macro can:
1)	Align the frames using stack registration
2)	Measure the signal intensity for the generated ratiometric and double-channel stack using a provided ROI list

We have provided an example stack: *WT-LUMOB-141_70-2_MMStack_Default.ome-1.tif*. It consists of 3 channels and shows three lines of etiolated seedlings: Col-0, 12 (NES roGFP2-Orp1), and 15 (peroxisomal roGFP2-Orp1). I recommend opening the file using Bio-Formats (Plugins>>Bio-Formats>>Bio-Formats Importer).

To use the *Dynamic only* correction method, first input all the values for the dynamic autofluorescence correction, such as:

```
if (autofluo == "Dynamic only") {
	Dialog.create("Autofluorescence correction");
		Dialog.addString(".csv file named as XXX-460:", "WT");
		Dialog.addNumber("Gradient 400/515 nm:", 0.4562);
		Dialog.addNumber("y-Intercept 400/515 nm:", 239);
	Dialog.show();
    ...
    }
```

The macro first performs median filtering (since the raw images are too noisy for accurate pixel-based calculations) and then subtracts the provided autofluorescence values from the corresponding channels. 
In the case of the 395/515 nm channel, the macro will multiply each pixel from the 395/460 nm channel by the gradient value, add the intercept value, and then subtract the created stack from the raw 395/515 nm channel. 

```
call("ij.ImagePlus.setDefault16bitRange", 0);
run("Median...", "radius=1 stack");
run("32-bit");
getDimensions(width, height, channels, slices, frames);
run("Split Channels");

selectImage("C3-"+img);
run("Duplicate...", "title=[scaled C3-"+img+"] duplicate");

selectImage("C2-"+img);
if (autofluo == "Dynamic only") {
	selectImage("scaled C3-"+img);
	if (frames==1) {
		run("Multiply...", "value="+a);
		run("Add...", "value="+b);
		selectImage("C2-"+img); 
		imageCalculator("Subtract create", "C2-"+img,"scaled C3-"+img);
		run("Macro...", "code=[if( v < 0) v = 0]");
	} else {
		run("Multiply...", "value="+a+" stack");
		run("Add...", "value="+b+" stack");
		selectImage("C2-"+img); 
		imageCalculator("Subtract create stack", "C2-"+img,"scaled C3-"+img);
		run("Macro...", "code=[if( v < 0) v = 0] stack");
	}
	selectImage("Result of C2-"+img);
}

...

rename("corrected C2-"+img);
selectImage("scaled C3-"+img);
close;
```



In the case of the 453/515 nm channel, the macro opens the provided table (here named WT-460.csv) and goes frame by frame, subtracting the corresponding table value from each pixel in the frame. You will see the messages appearing in the log window as the script goes through each frame: 

```
selectImage("C1-"+img);
run("Duplicate...", "title=[corrected C1-"+img+"] duplicate");

...

getDimensions(width, height, channels, slices, frames);
if (autofluo == "Dynamic only" || autofluo == "Frame-by-Frame Only"){
	open(dir+x+"-460.csv");
	for (i = 0; i <= frames-1; i++) {
		f=i+1;
		Stack.setFrame(f);
		v = Table.get("C",i);
		print("Value subtracted from frame"+f+": "+v);
		run("Subtract...", "value="+v);
	}
}

if (autofluo == "Dynamic only" || autofluo == "C460 Mean, C400 Dynamic"){
	selectImage("C2-"+img);
	close;
}
selectImage("C3-"+img);
close;
```

The next step takes the 453/515 nm channel and creates a binary mask to select only regions where there is a detectable roGFP2 signal. Since different images are being captured using the system (images of roots, whole rosettes, and young seedlings), there is no single way of thresholding that works well for them all. Hence, we have included some freedom of choice in that step. The macro stops at that step and asks the user to choose a version of the image with better contrast:

```
selectImage("C1-"+img);
run("Duplicate...", "title=[mask C1-"+img+"] duplicate");

selectImage("C1-"+img);
close;
selectImage("mask C1-"+img);

run("Duplicate...", "title=std");
getStatistics(voxelCount, mean, min, max, stdDev);
selectImage("std");
setMinAndMax(2*stdDev, mean+2*stdDev);
run("8-bit");
selectImage("mask C1-"+img);
selectImage("mask C1-"+img);
run("Duplicate...", "title=std-1");
selectImage("std-1");
getStatistics(voxelCount, mean, min, max, stdDev);
setMinAndMax(3*stdDev, mean+3*stdDev);
run("8-bit");
run("Images to Stack", "  title=std use keep");
run("Make Montage...", "columns=2 rows=1 scale=0.25 label");
Dialog.create("Mask choice");
	Dialog.addChoice("Which image has a better contrast?", newArray("Left", "Right"));
Dialog.show();
contrast = Dialog.getChoice();

selectImage("mask C1-"+img);
getDimensions(width, height, channels, slices, frames);
if (contrast=="Left"){
	if (frames==1) {
		getStatistics(voxelCount, mean, min, max, stdDev);
	} else {
		Stack.getStatistics(voxelCount, mean, min, max, stdDev);
	}
	setMinAndMax(2*stdDev, mean+2*stdDev);
	}

if (contrast=="Right"){
	if (frames==1) {
		getStatistics(voxelCount, mean, min, max, stdDev);
	} else {
		Stack.getStatistics(voxelCount, mean, min, max, stdDev);
	}
	setMinAndMax(3*stdDev, mean+3*stdDev);
	}
```
Next, choose your thresholding method from the choice of three: Huang, local Phansalkar, and Otsu. Otsu is a straightforward thresholding method when dealing with bimodal histograms (in this case, images with bright signal and very low background). Local Phansalkar is for the opposite scenario (when there is not a lot of contrast between signal and background). It is also a better choice for images that start off bright and dim towards the end (i.e. oxidation treatment). Local Phansalkar is more computationally expensive so there is no point in using it for standard, high-contrast images. The macro then removes speckles from the mask using median filtering and dilation-erosion steps. 
```
run("8-bit");
run("Duplicate...", "title=mask");
selectImage("mask C1-"+img);
run("Duplicate...", "title=mask-1");
run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white");
selectImage("mask");
run("Auto Threshold", "method=Huang2 white");
selectImage("mask C1-"+img);
run("Duplicate...", "title=mask-2");
run("Auto Threshold", "method=Otsu white");
run("Images to Stack", "  title=mask use keep");
run("Make Montage...", "columns=3 rows=1 scale=0.25 label");
Dialog.create("Mask choice");
	Dialog.addChoice("Which mask is better?", newArray("Left (Huang)", "Middle (Local Phan)", "Right (Otsu)"));
Dialog.show();
mask = Dialog.getChoice();
close();
selectImage("Stack");
close();
selectImage("mask");
close();
selectImage("mask-1");
close();
selectImage("mask-2");
close();

selectImage("mask C1-"+img);
getDimensions(width, height, channels, slices, frames);
if (mask=="Left (Huang)"){
	if (frames==1) {
		run("Auto Threshold", "method=Huang2 white");
		setOption("ScaleConversions", true);
		setOption("BlackBackground", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Threshold", "method=Huang2 white stack");
		setOption("ScaleConversions", true);
		setOption("BlackBackground", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}
if (mask=="Middle (Local Phan)"){
	if (frames==1) {
		run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}
if (mask=="Right (Otsu)"){
	if (frames==1) {
		run("Auto Threshold", "method=Otsu white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Threshold", "method=Otsu white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}

saveAs("Tiff",dir+"mask C1-"+img);
```
The ready mask is then used to threshold the 453/515 and 395/515 nm channels using the AND operation in the Image Calculator. The channels are then converted to 32-bit in preparation for ratiometric image generation.

```
selectImage("mask C1-"+img);
run("16-bit");
selectImage("mask C1-"+img);
run("32-bit");
selectImage("mask C1-"+img);
run("16-bit");

if (frames==1) {
	imageCalculator("AND create", "corrected C1-"+img,"mask C1-"+img);
	selectImage("Result of corrected C1-"+img);
	imageCalculator("AND create", "corrected C2-"+img,"mask C1-"+img);
	selectImage("Result of corrected C2-"+img);
} else {
	imageCalculator("AND create stack", "corrected C1-"+img,"mask C1-"+img);
	selectImage("Result of corrected C1-"+img);
	imageCalculator("AND create stack", "corrected C2-"+img,"mask C1-"+img);
	selectImage("Result of corrected C2-"+img);
}

selectImage("Result of corrected C1-"+img);
run("32-bit");
selectImage("Result of corrected C2-"+img);
run("32-bit");

selectImage("corrected C1-"+img);
close;
selectImage("corrected C2-"+img);
close;
```
*If selected, this is when registration occurs. The macro first aligns one channel (453/515 nm), saves all the transformations as a temporary file, and then uses the saved parameters to align the 395/515 nm channel and the mask. It is important that for registration the image is cropped so minimal amount of background is present- if a bright edge of the plate is present on the top of the image, the registration sometimes fails. If that happens, crop the image once more. It is also important to note that registration ‘straightens out’ frames of the individual channel (so that the plant does not move in time) but it assumes that the two channels are aligned to each other to start with.*
```
if (reg== true){
	getDateAndTime(year, month, dayOfWeek, dayOfMonth,
		hour, minute, second, msec);
	tmpfile  = getDirectory("temp");
	tmpfile += "MSR-" + year + "-" + month + "-" + dayOfMonth +
		"_" + hour + "-" + minute + "-" + second + ".txt";
	run("MultiStackReg", "stack_1=[Result of corrected C1-"+ img
		+ "] action_1=Align"
		+ " file_1=[" + tmpfile + "]"
		+ " stack_2=None"
		+ " action_2=Ignore"
		+ " file_2=[]"
		+ " transformation=[Rigid Body] save");
	
	run("MultiStackReg", "stack_1=[Result of corrected C2-"+ img +
		"] action_1=[Load Transformation File]" +
		" file_1=[" + tmpfile + "]" +
		" stack_2=None" +
		" action_2=Ignore" +
		" file_2=[]" +
		" transformation=[Rigid Body]");
	
	run("MultiStackReg", "stack_1=[mask C1-"+ img +
		"] action_1=[Load Transformation File]" +
		" file_1=[" + tmpfile + "]" +
		" stack_2=None" +
		" action_2=Ignore" +
		" file_2=[]" +
		" transformation=[Rigid Body]");
	
	selectImage("mask C1-"+img);
	run("Auto Threshold", "method=Otsu white stack");
	setOption("ScaleConversions", true);
	selectImage("mask C1-"+img);
	run("32-bit");
	run("16-bit");
	
	selectImage("Result of corrected C1-"+img);
	rename("corrected C1-"+img);
	selectImage("Result of corrected C2-"+img);
	rename("corrected C2-"+img);
	
	if (frames==1) {
	imageCalculator("AND create", "corrected C1-"+img,"mask C1-"+img);
	rename("Result of corrected C1-"+img);
	imageCalculator("AND create", "corrected C2-"+img,"mask C1-"+img);
	rename("Result of corrected C2-"+img);
	} else {
	imageCalculator("AND create stack", "corrected C1-"+img,"mask C1-"+img);
	rename("Result of corrected C1-"+img);
	imageCalculator("AND create stack", "corrected C2-"+img,"mask C1-"+img);
	rename("Result of corrected C2-"+img);
	}
	
	selectImage("Result of corrected C1-"+img);
	getDimensions(width, height, channels, slices, frames);
	if (frames==1) {
	changeValues(60000, 65536, 0);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(60000, 65536, 0);
		}
	}
	
	selectImage("Result of corrected C2-"+img);
	getDimensions(width, height, channels, slices, frames);
	if (frames==1) {
	changeValues(60000, 65536, 0);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(60000, 65536, 0);
		}
	}
}
```
The corrected, and aligned if applicable, channels are now merged and any 0 pixels are turned into NaN. This is a very crucial step as now the NaN values from the background do not affect the measurements where crude ROIs are taken.
```
run("Merge Channels...", "c1=[Result of corrected C1-"+img+"] c2=[Result of corrected C2-"+img+"] create");
rename("corrected-"+img);

selectImage("corrected-"+img);

getDimensions(width, height, channels, slices, frames);
for (c=1; c<= channels; c++) {
	Stack.setChannel(c);
	if (frames==1) {
	changeValues(0, 0, NaN);	
	changeValues(60000, 65536, 0);
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(0, 0, NaN);
		changeValues(60000, 65536, 0);
		}
	}	
}
```
Next, the ratio image is generated. The corrected stack channels are split and the corrected 395/515 nm channel is divided by the 453/515 nm channel. We have observed that the true roGFP2-Orp1 ratio pixels cannot reach values higher than 3. If they do occur within the plant area, it is always at the edges of the plant which is likely due to fringing (i.e. pixels right on the plant-background border combine signals from both the plant and background). 
```
run("Split Channels");
selectImage("C1-corrected-"+img);
selectImage("C2-corrected-"+img);

getDimensions(width, height, channels, slices, frames);
if (frames==1) {
	imageCalculator("Divide create 32-bit", "C2-corrected-"+img,"C1-corrected-"+img);
	run("Macro...", "code=[if( v > 4 ) v = NaN]");
} else {
	imageCalculator("Divide create 32-bit stack", "C2-corrected-"+img,"C1-corrected-"+img);
	run("Macro...", "code=[if( v > 4 ) v = NaN] stack");
}

selectImage("Result of C2-corrected-"+img);
rename("ratio-"+img);

run("Fire");
```
At this stage, the ratiometric stack can still have some noisy pixels that we later call 'nonsense' pixels. The macro will stop at that step for you to investigate the ratiometric stack. Look for any pixel values at the edges of your plants that are much higher than pixel values within the plant. You can adjust brightness and contrast to identify them better. 

Now notice what the highest observable pixel values within your plant are.  For the next step, you will need to provide the maximum and minimum threshold ratio values. The trick is to find the highest possible value to exclude most of the ‘nonsense’ fringed pixels while preserving all the ‘sensical’ pixels that make up the plant. Type it as ‘Ratio threshold (max)’. You can leave ‘Ratio threshold (min)’ as 0 unless you have a good reason to change it. From experience, I rarely observed low-value pixels that looked fringed so I almost always leave it at 0.
```
getDimensions(width, height, channels, slices, frames);
if (frames==1) {
	getStatistics(voxelCount, mean, min, max, stdDev);
} else {
	Stack.getStatistics(voxelCount, mean, min, max, stdDev);
}

scalar=mean+2*stdDev;
setMinAndMax(0, scalar);
if (calratio == true) {
	setMinAndMax(calMin,calMax);
}

waitForUser("Find threshold ratios (needs to be provided in the next step)");
Dialog.create("Remove nonsense ratio (cannot be reversed)");
			Dialog.addNumber("Ratio threshold (max):", 0);
			Dialog.addNumber("Ratio threshold (min):", 0);
		Dialog.show();
		thrmax = Dialog.getNumber();
		thrmin= Dialog.getNumber();
```
The macro will turn all the pixels higher than or equal to the threshold value into NaN and save the ratiometric stack as new_ratio-StackName. The macro duplicates the ratiometric image, converts it to a binary mask, and uses the mask to exclude the same ‘nonsense’ pixels from the 395/515 and 453/515 nm channels.  The channels are merged and saved as improved_corrected-StackName.
```
selectImage("ratio-"+img);
		
if (frames==1) {
	run("Macro...", "code=[if( v >= " + thrmax + ") v = NaN]");
} else {
	run("Macro...", "code=[if( v >= " + thrmax + ") v = NaN] stack");
}

if (frames==1) {
	run("Macro...", "code=[if( v <= " + thrmin + ") v = NaN]");
} else {
	run("Macro...", "code=[if( v <= " + thrmin + ") v = NaN] stack");
}

saveAs("Tiff",dir+"new_ratio-"+img);
print("Ratiometric image created");

selectImage("new_ratio-"+img);

...

run("Duplicate...", "title=[mask_improved-"+img+"] duplicate");
selectImage("mask_improved-"+img);
if (frames==1) {
	run("Macro...", "code=[if( v > " + 0 + ") v = 255]");
} else {
	run("Macro...", "code=[if( v > " + 0 + ") v = 255] stack");
}
run("8-bit");

selectImage("mask C1-"+img);
close;

selectImage("mask_improved-"+img);
	
run("16-bit");
selectImage("mask_improved-"+img);
run("32-bit");
selectImage("mask_improved-"+img);
run("16-bit");

if (frames==1) {
	imageCalculator("AND create", "C1-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C1-corrected-"+img);
	imageCalculator("AND create", "C2-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C2-corrected-"+img);
} else {
	imageCalculator("AND create stack", "C1-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C1-corrected-"+img);
	imageCalculator("AND create stack", "C2-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C2-corrected-"+img);
}
selectImage("C1-corrected-"+img);
close;
selectImage("C2-corrected-"+img);
close;

...

run("Merge Channels...", "c1=[Result of C1-corrected-"+img+"] c2=[Result of C2-corrected-"+img+"] create keep");
rename("improved_corrected-"+img);
getDimensions(width, height, channels, slices, frames);
for (c=1; c<= channels; c++) {
	Stack.setChannel(c);
	if (frames==1) {
	changeValues(0, 0, NaN);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(0, 0, NaN);
		}
	}	
}
saveAs("Tiff",dir+"improved_corrected-"+img);
print("Corrected image saved");

selectImage("Result of C1-corrected-"+img);
close;
selectImage("Result of C2-corrected-"+img);
close;

print("All done!");
```
*If the measurement option has been selected, the channels are used to set measurements before the channels are merged. The measurements are done based on the ROI list named RoiSet.zip (the default name) that needs to be located in the image folder. You can create and save the ROI list using the MultiMeasure plugin. The type of measurements depends on your current ImageJ settings (Analyze>>Set Measurements…). The multi-measurements are recorded and saved as either 400Results-StackName.csv or 460Results-StackName.csv in the image folder.*
```
if (measure == true) {
	selectImage("new_ratio"+img);
	run("Duplicate...", "title=[measure-ratio-"+img+"] duplicate");
	
	run("ROI Manager...");
	
	selectImage("measure-ratio-"+img);
	
	roiManager("Open", dir+"RoiSet.zip");
	roiManager("Show All with labels");
	roiManager("Select All");
	
	run("Set Measurements...", "mean redirect=None decimal=5");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"Ratio-"+img+".csv");
	print("Ratio results saved");
	
	selectImage("new_ratio-"+img);
}

...

if (measure == true) {
	selectImage("Result of C2-corrected-"+img);
	run("Duplicate...", "title=[measure-C2-"+img+"] duplicate");
	
	selectImage("Result of C1-corrected-"+img);
	run("Duplicate...", "title=[measure-C1-"+img+"] duplicate");
	
	run("ROI Manager...");
	
	selectImage("measure-C1-"+img);
	
	roiManager("Open", dir+"RoiSet.zip");
	roiManager("Show All with labels");
	roiManager("Select All");
	
	run("Set Measurements...", "mean redirect=None decimal=5");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"460Results-"+img+".csv");
	print("460/515nm results saved");
	
	selectImage("measure-C2-"+img);
	roiManager("Show All with labels");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"400Results-"+img+".csv");
	print("400/515nm results saved");
	
	selectImage("measure-C1-"+img);
	close;
	selectImage("measure-C2-"+img);
	close;
}
```
That’s it! **Do not click on any image windows before the script stops running (you will receive ‘All done!’ message in the Log window).** The macro saves the image that is currently being selected so if you select any other image window it will overwrite and save that one instead.

## Authors

Hanna Deckert (contact: Hanna.Deckert@glasgow.ac.uk)
<br> at Matt Jones lab, University of Glasgow (Matt.Jones@glasgow.ac.uk)

## Acknowledgements

I would like to acknowledge the invaluable image.sc threads and many thanks to the people who have contributed their answers:
<br> Karl-Heinz: https://forum.image.sc/t/fiji-image-calculator-boolean-and-potential-bug/1188/15 
<br> Curtis Rueden: https://forum.image.sc/t/interactive-selection-in-imagej-macro/1451/4 
<br> Niko Ehrenfeuchter: https://forum.image.sc/t/multistackreg-macro/174/6 
<br> David Mason: https://forum.image.sc/t/how-to-set-a-universal-ratio-image-callibration-bar-for-the-ratio-number-and-the-corresponding-color/90763/2 
<br> John Bogovic and Ved Sharma: https://forum.image.sc/t/conditionally-change-pixel-values/58267 
