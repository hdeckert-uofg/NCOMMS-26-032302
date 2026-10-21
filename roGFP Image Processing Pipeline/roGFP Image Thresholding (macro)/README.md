# Thresholding Macro- Supplement to roGFP2 Image Processing Pipeline

## Overview

This ImageJ Macro was written to work with two image stacks: a 2-channel .tiff file with individual processed roGFP2-emission channels, and the roGFP2 ratio (Ratio<sub>UV ex/blue ex</sub>) image stack. The purpose of the macro is to remove unwanted pixels (due to pixel fringing, etc.) that were not removed during the first round of thresholding included in the original *roGFP2 Image Processing Pipeline* macro.

## Getting started

### Dependencies

- Fiji 2.16.0/1.54p or later
	* to install: https://imagej.net/software/fiji/downloads 
- Windows 10 (Version 22H2)

  * *Check the macro if using on macOS devices- current macro version should run smoothly on Mac but there has been some issues in the past with certain commands (mainly related to thresholding)*

Expected install time: N/A

### Demo
The script can be tested on the processed image stacks found in the *Example data>> Processed stacks* folder (*improved_corrected-WT-LUMOB-141_70-2_MMStack_Default.ome-1.tiff* and *new_ratio-WT-LUMOB-141_70-2_MMStack_Default.ome-1.tiff*). The expected output is provided in the *Thresholded stacks* folder.
<br> Expected demo run time: 1-2 min

## Executing program

### Macro Requirements

This is a supplementary macro to the “roGFP2 Image Processing Pipeline” macro. Please refer to that macro's README file for more detail.

To run the macro, two image stacks need to be open:
1.	two-channel processed roGFP2-emission stack (*improved-corrected....tiff*)
2.	roGFP2 ratio stack (*new-ratio....tiff*)

### Thresholding Macro

This macro allows to:
1)	Exclude all pixels that are above or below a certain threshold (values provided by the user) on the ratio image

```
waitForUser("Find threshold ratios (needs to be provided in the next step)");
Dialog.create("Remove nonsense ratio (cannot be reversed)");
			Dialog.addNumber("Ratio threshold (max):", 0);
			Dialog.addNumber("Ratio threshold (min):", 0);
		Dialog.show();
		thrmax = Dialog.getNumber();
		thrmin= Dialog.getNumber();
		
selectImage(img);
getDimensions(width, height, channels, slices, frames);
		
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

saveAs("Tiff",dir+"cyto-"+img);
```

*The macro currently saves the thresholded images with a prefix cyto-. You can manually change the prefix in the Macro Editing window*

2)	Use a binary mask of the ratio image to exclude the same pixels on the individual processed roGFP2-emission channels

- Generate a binary mask (non-NaN pixels changed to 65535)
```
selectImage("cyto-"+img);
run("Duplicate...", "title=[mask-"+img+"] duplicate");
selectImage("mask-"+img);
getDimensions(width, height, channels, slices, frames);

if (frames==1) {
	run("Macro...", "code=[if( v > " + 0 + ") v = 65535]");
} else {
	run("Macro...", "code=[if( v > " + 0 + ") v = 65535] stack");
}
```
 - Use the binary mask to threshold the individual processed roGFP2-emission channels
```
if (frames==1) {
	imageCalculator("AND create", C1,"mask-"+img);
	selectImage("Result of "+C1);
	imageCalculator("AND create", C2,"mask-"+img);
	selectImage("Result of "+C2);
} else {
	imageCalculator("AND create stack", C1,"mask-"+img);
	selectImage("Result of "+C1);
	imageCalculator("AND create stack", C2,"mask-"+img);
	selectImage("Result of "+C2);
}
selectImage(C1);
close;
selectImage(C2);
close;

run("Merge Channels...", "c1=[Result of "+C1+"] c2=[Result of "+C2+"] create keep");
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
saveAs("Tiff",dir+"cyto-"+img2);
```

That’s it! **Do not click on any image window before the script stops running (you will receive ‘All done!’ message in the Log window).** The macro saves the image that is currently being selected so if you select any other image window it will overwrite and save that one instead.

## Authors

Hanna Deckert (contact: Hanna.Deckert@glasgow.ac.uk)
<br> at Matt Jones lab, University of Glasgow (Matt.Jones@glasgow.ac.uk)

## Acknowledgements

I would like to acknowledge the invaluable image.sc threads and many thanks to the people who have contributed their answers:
<br> Karl-Heinz: https://forum.image.sc/t/fiji-image-calculator-boolean-and-potential-bug/1188/15 
<br> John Bogovic and Ved Sharma: https://forum.image.sc/t/conditionally-change-pixel-values/58267 
