//open hypocotyl selection on ROI manager
for (i = 0; i < roiManager("Count"); i++) {
run("Clear Results");
roiManager("Select", i);
profile = getProfile(); //warning: do not use Plot profile() before

for (n=0; n<profile.length; n++)
setResult("Value", n, profile[n]);
updateResults();
//save or amend the other table to include new results
}